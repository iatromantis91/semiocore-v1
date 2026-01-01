from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema


REPO = Path(__file__).resolve().parents[1]
CONFORMANCE = REPO / "tests" / "conformance"
PROGRAM = CONFORMANCE / "programs" / "c001_minimal.sc"
WORLD = CONFORMANCE / "worlds" / "w_paper.json"
EXPECTED = CONFORMANCE / "expected" / "c001.trace.json"
TRACE_SCHEMA = REPO / "schemas" / "trace.schema.json"

def _stable_path(s: str) -> str:
    """
    Normaliza rutas para que el hash sea cross-platform.
    - Convierte backslashes a slashes
    - Si contiene el path del repo, lo vuelve relativo al repo
    - Si no, reduce a basename (para tmp/out variables)
    """
    s = s.replace("\\", "/")
    repo = REPO.as_posix().rstrip("/")
    if repo and repo in s:
        return s.split(repo, 1)[1].lstrip("/")
    if not s.startswith("/") and ":" not in s[:3]:
        if s.startswith(("tests/", "schemas/", "fixtures/")):
            return s
    return os.path.basename(s)

def _normalize_trace_for_hash(x: object) -> object:
    if isinstance(x, dict):
        out: dict[object, object] = {}
        for k, v in x.items():
            # normaliza rutas
            if isinstance(k, str) and k.endswith("_file") and isinstance(v, str):
                out[k] = _stable_path(v)
                continue

            # (opcional, recomendado) ignora metadatos típicamente volátiles si existen
            if k in ("created_at", "timestamp", "host", "platform", "python", "cwd"):
                continue

            out[k] = _normalize_trace_for_hash(v)
        return out
    if isinstance(x, list):
        return [_normalize_trace_for_hash(i) for i in x]
    return x

def _c14n_sha256(obj: object) -> str:
    # Canonical JSON (stable across formatting)
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _load_json(p: Path) -> object:
    return json.loads(p.read_text(encoding="utf-8"))


def _schema_required_keys(schema: dict) -> list[str]:
    req = schema.get("required", [])
    return [str(x) for x in req] if isinstance(req, list) else []

def _run_semioc_run(program: Path, world: Path, out_trace: Path) -> Path:
    """
    Ejecuta: semioc run <program> --world ... --emit-manifest ... --emit-trace ...
    Devuelve la ruta del manifest generado.
    """
    out_manifest = out_trace.with_suffix(".manifest.json")

    cmd = [
        sys.executable, "-m", "semioc",
        "run",
        str(program),
        "--world", str(world),
        "--emit-manifest", str(out_manifest),
        "--emit-trace", str(out_trace),
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + "\n" + r.stderr)

    return out_manifest

def test_conformance_run_trace_matches_expected(tmp_path: Path) -> None:
    assert PROGRAM.exists(), f"Missing program: {PROGRAM}"
    assert WORLD.exists(), f"Missing world: {WORLD}"
    assert TRACE_SCHEMA.exists(), f"Missing schema: {TRACE_SCHEMA}"

    schema = json.loads(TRACE_SCHEMA.read_text(encoding="utf-8"))

    # Run twice -> determinism
    t1 = tmp_path / "c001_1.trace.json"
    t2 = tmp_path / "c001_2.trace.json"

    _run_semioc_run(PROGRAM, WORLD, t1)
    _run_semioc_run(PROGRAM, WORLD, t2)

    o1 = _load_json(t1)
    o2 = _load_json(t2)

    # 1) Schema valid
    jsonschema.validate(instance=o1, schema=schema)
    jsonschema.validate(instance=o2, schema=schema)

    # 2) Required keys present (invariants derived from schema)
    req = _schema_required_keys(schema)
    if isinstance(o1, dict):
        for k in req:
            assert k in o1, f"Trace missing required key: {k}"
    if isinstance(o2, dict):
        for k in req:
            assert k in o2, f"Trace missing required key: {k}"

    # 3) Deterministic canonical hash
    h1 = _c14n_sha256(_normalize_trace_for_hash(o1))
    h2 = _c14n_sha256(_normalize_trace_for_hash(o2))

    assert h1 == h2, f"Non-deterministic trace hash: {h1} != {h2}"

    # 4) Compare against expected (small + stable)
    expected_payload = {
        "kind": "trace",
        "sha256_c14n": h1,
        "required_keys": req,
    }

    if os.getenv("UPDATE_EXPECTED") == "1":
        EXPECTED.parent.mkdir(parents=True, exist_ok=True)
        EXPECTED.write_text(json.dumps(expected_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return

    assert EXPECTED.exists(), (
        f"Missing expected file: {EXPECTED}\n"
        f"Run: UPDATE_EXPECTED=1 {sys.executable} -m pytest -q {Path(__file__).name}"
    )
    exp = json.loads(EXPECTED.read_text(encoding="utf-8"))
    assert exp["sha256_c14n"] == h1, f"Trace hash mismatch. expected={exp['sha256_c14n']} actual={h1}"
