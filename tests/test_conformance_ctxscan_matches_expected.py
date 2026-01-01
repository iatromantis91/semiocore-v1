from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import jsonschema


# Repo root (robusto: busca pyproject.toml hacia arriba)
def find_repo_root(start: Path) -> Path:
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Repo root not found (pyproject.toml missing).")

REPO = find_repo_root(Path(__file__).resolve())
CONFORMANCE = REPO / "tests" / "conformance"

PROGRAM = CONFORMANCE / "programs" / "c002_ctxscan.sc"
WORLD = CONFORMANCE / "worlds" / "w_paper.json"
EXPECTED = CONFORMANCE / "expected" / "c002.ctxscan.json"

CTXSCAN_SCHEMA = REPO / "schemas" / "ctxscan.schema.json"

def _stable_path(s: str) -> str:
    """
    Convierte rutas a una forma estable:
    - si contiene el path del repo -> lo vuelve relativo al repo
    - si no -> deja rutas relativas conocidas, o reduce a basename
    """
    s = s.replace("\\", "/")
    repo = REPO.as_posix().rstrip("/")
    if repo and repo in s:
        return s.split(repo, 1)[1].lstrip("/")

    # si ya parece relativo, lo mantenemos para paths dentro del repo
    if not s.startswith("/") and ":" not in s[:3]:
        if s.startswith(("tests/", "schemas/", "fixtures/")):
            return s

    # para tmp/out/emit dirs (variables), solo basename
    return os.path.basename(s)

def _c14n_sha256(obj: object) -> str:
    b = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()


def _load_json(p: Path) -> object:
    return json.loads(p.read_text(encoding="utf-8"))


def _schema_required_keys(schema: dict) -> list[str]:
    req = schema.get("required", [])
    return [str(x) for x in req] if isinstance(req, list) else []

def _stable_basename(p: str) -> str:
    # Unifica separadores y recorta a basename para que Windows/Linux den lo mismo
    p = p.replace("\\", "/")
    return os.path.basename(p)

def _normalize_ctxscan_for_hash(x: object) -> object:
    """
    Vista estable del ctxscan para hashing cross-platform:
    - normaliza cualquier campo *_file a basename
    - ordena determinísticamente la lista 'perms' (si existe)
    """
    if isinstance(x, dict):
        out: dict[object, object] = {}

        for k, v in x.items():
            # 1) normaliza paths en cualquier *_file (incluye trace_file, program_file, world_file, etc.)
            if isinstance(k, str) and k.endswith("_file") and isinstance(v, str):
                out[k] = _stable_basename(v)
                continue

            # 2) normaliza recursivamente
            out[k] = _normalize_ctxscan_for_hash(v)

        # 3) si existe 'perms', la ordenamos de forma estable
        perms = out.get("perms")
        if isinstance(perms, list) and perms and all(isinstance(i, dict) for i in perms):
            def _perm_key(d: dict) -> tuple[str, str]:
                ctx = str(d.get("ctx", ""))
                params = d.get("params", {})
                # params a string canónico para orden estable
                params_s = json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=False) if isinstance(params, dict) else str(params)
                return (ctx, params_s)

            out["perms"] = sorted(perms, key=_perm_key)

        return out

    if isinstance(x, list):
        return [_normalize_ctxscan_for_hash(i) for i in x]

    return x


def _run_semioc_run(program: Path, world: Path, out_trace: Path) -> Path:
    """
    Ejecuta: semioc run <program> --world ... --emit-manifest ... --emit-trace ...
    Devuelve la ruta del manifest generado (por si lo necesitas luego).
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

def _run_semioc_ctxscan(program: Path, world: Path, out_report: Path, emit_dir: Path) -> None:
    """
    Ejecuta: semioc ctxscan --world ... --emit-report ... --emit-dir ... program
    """
    emit_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "semioc",
        "ctxscan",
        "--world", str(world),
        "--emit-report", str(out_report),
        "--emit-dir", str(emit_dir),
        "--max-perms", "64",
        str(program),
    ]
    r = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + "\n" + r.stderr)

def test_conformance_ctxscan_matches_expected(tmp_path: Path) -> None:
    assert PROGRAM.exists(), f"Missing program: {PROGRAM}"
    assert WORLD.exists(), f"Missing world: {WORLD}"
    assert CTXSCAN_SCHEMA.exists(), f"Missing schema: {CTXSCAN_SCHEMA}"

    ctxscan_schema = json.loads(CTXSCAN_SCHEMA.read_text(encoding="utf-8"))

    # Run twice -> determinism
    t1 = tmp_path / "c002_1.trace.json"
    t2 = tmp_path / "c002_2.trace.json"
    c1 = tmp_path / "c002_1.ctxscan.json"
    c2 = tmp_path / "c002_2.ctxscan.json"

    _run_semioc_run(PROGRAM, WORLD, t1)
    _run_semioc_run(PROGRAM, WORLD, t2)
    d1 = tmp_path / "ctxscan_emit_1"
    d2 = tmp_path / "ctxscan_emit_2"

    _run_semioc_ctxscan(PROGRAM, WORLD, c1, d1)
    _run_semioc_ctxscan(PROGRAM, WORLD, c2, d2)

    o1 = _load_json(c1)
    o2 = _load_json(c2)

    # 1) Schema valid
    jsonschema.validate(instance=o1, schema=ctxscan_schema)
    jsonschema.validate(instance=o2, schema=ctxscan_schema)

    # 2) Required keys present (schema-derived invariants)
    req = _schema_required_keys(ctxscan_schema)
    if isinstance(o1, dict):
        for k in req:
            assert k in o1, f"Ctxscan missing required key: {k}"
    if isinstance(o2, dict):
        for k in req:
            assert k in o2, f"Ctxscan missing required key: {k}"

    # 3) Deterministic canonical hash (stable view: normalize trace_file)
    h1 = _c14n_sha256(_normalize_ctxscan_for_hash(o1))
    h2 = _c14n_sha256(_normalize_ctxscan_for_hash(o2))
    assert h1 == h2, f"Non-deterministic ctxscan (stable-view) hash: {h1} != {h2}"

    # 4) Compare against expected (small + stable)
    expected_payload = {
        "kind": "ctxscan",
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
    assert exp["sha256_c14n"] == h1, f"Ctxscan hash mismatch. expected={exp['sha256_c14n']} actual={h1}"
