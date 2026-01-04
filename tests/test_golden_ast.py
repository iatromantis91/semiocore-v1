from __future__ import annotations
import json
from pathlib import Path

from semioc.parser import parse_program_to_ast

ROOT = Path(__file__).resolve().parents[1]
PROGS = ROOT / "programs" / "conformance"
EXPECTED = ROOT / "expected" / "ast"

def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))

def test_golden_ast_conformance():
    assert PROGS.exists(), f"Missing conformance programs dir: {PROGS}"
    assert EXPECTED.exists(), f"Missing expected AST dir: {EXPECTED}"

    for sc_file in sorted(PROGS.glob("*.sc")):
        rel = sc_file.relative_to(ROOT).as_posix()  # stable cross-OS
        exp_file = EXPECTED / f"{sc_file.stem}.ast.json"
        assert exp_file.exists(), f"Missing expected AST: {exp_file}"

        ast_obj = parse_program_to_ast(
            sc_file.read_text(encoding="utf-8"),
            program_file=rel,
        )
        expected = load_json(exp_file)
        assert ast_obj == expected, f"AST mismatch for {sc_file.name}"
