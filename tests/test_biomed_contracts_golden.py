from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[1]
PROGRAMS = REPO / "programs" / "biomed_v1"
WORLD = REPO / "fixtures" / "world" / "biomed_world_v1.json"
EXPECTED_DIR = REPO / "fixtures" / "expected" / "biomed_v1"
TRACE_SCHEMA = REPO / "schemas" / "trace.schema.json"


def _stable_path(s: str) -> str:
    s = s.replace("\\", "/")
    repo = REPO.as_posix().rstrip("/")
    if repo and repo in s:
        return s.split(repo, 1)[1].lstrip("/")
    if s.startswith(("tests/", "schemas/", "fixtures/", "programs/")):
        return s
    return os.path.basename(s)


def _normalize(obj: object) -> object:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in ("program_file", "world_file"):
                out[k] = _stable_path(str(v))
            else:
                out[k] = _normalize(v)
        return out
    if isinstance(obj, list):
        return [_normalize(x) for x in obj]
    return obj


def _c14n_sha256(obj: object) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _load_json(p: Path) -> object:
    return json.loads(p.read_text(encoding="utf-8"))


def _run(program: Path, out_trace: Path) -> None:
    out_manifest = out_trace.with_suffix(".manifest.json")
    cmd = [
        sys.executable, "-m", "semioc",
        "run",
        str(program),
        "--world", str(WORLD),
        "--emit-manifest", str(out_manifest),
        "--emit-trace", str(out_trace),
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + "\n" + r.stderr)


def test_biomed_contracts_traces_match_expected():
    schema = _load_json(TRACE_SCHEMA)
    jsonschema.Draft202012Validator.check_schema(schema)

    programs = sorted(PROGRAMS.glob("*.sc"))
    assert programs, "No biomed_v1 programs found"

    for p in programs:
        expected = EXPECTED_DIR / (p.stem + ".trace.json")
        assert expected.is_file(), f"Missing expected trace: {expected}"

        tmp = REPO / "tests" / "tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        out_trace = tmp / (p.stem + ".trace.json")

        _run(p, out_trace)

        got = _load_json(out_trace)
        exp = _load_json(expected)

        # Schema sanity (both)
        jsonschema.validate(instance=got, schema=schema)
        jsonschema.validate(instance=exp, schema=schema)

        h_got = _c14n_sha256(_normalize(got))
        h_exp = _c14n_sha256(_normalize(exp))
        assert h_got == h_exp, f"Trace mismatch for {p.name}: {h_got} != {h_exp}"
