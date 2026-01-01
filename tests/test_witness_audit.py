import hashlib
import subprocess
import sys
from pathlib import Path

def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()

def test_verify_witness_ok(tmp_path: Path):
    a = tmp_path / "a.trace.json"
    b = tmp_path / "b.trace.json"
    a.write_text('{"hello": "world"}\n', encoding="utf-8")
    b.write_text('{"hello": "world"}\n', encoding="utf-8")

    sha = _sha256(a)
    w = tmp_path / "witness.txt"
    w.write_text(
        "\n".join([
            f"perm_trace_src : {a.as_posix()}",
            f"e2p_trace      : {b.as_posix()}",
            f"perm_sha256    : {sha}",
            f"e2p_sha256     : {sha}",
            f"sha_match      : True",
            "",
        ]),
        encoding="utf-8",
    )

    r = subprocess.run([sys.executable, "tools/verify_witness.py", "--witness", str(w)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + "\n" + r.stderr

def test_verify_witness_fails_on_mismatch(tmp_path: Path):
    a = tmp_path / "a.trace.json"
    b = tmp_path / "b.trace.json"
    a.write_text('{"x": 1}\n', encoding="utf-8")
    b.write_text('{"x": 2}\n', encoding="utf-8")

    w = tmp_path / "witness.txt"
    w.write_text(
        "\n".join([
            f"perm_trace_src : {a.as_posix()}",
            f"e2p_trace      : {b.as_posix()}",
            f"perm_sha256    : {_sha256(a)}",
            f"e2p_sha256     : {_sha256(b)}",
            f"sha_match      : True",
            "",
        ]),
        encoding="utf-8",
    )

    r = subprocess.run([sys.executable, "tools/verify_witness.py", "--witness", str(w)], capture_output=True, text=True)
    assert r.returncode != 0, "verify_witness debería fallar si sha_match es inconsistente"
