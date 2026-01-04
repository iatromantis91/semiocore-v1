from __future__ import annotations

import json
from pathlib import Path

from semioc.contract_ids import LANG_SCHEMA_V1, AST_SCHEMA_V1, PLASTICITY_SCHEMA_V1

ROOT = Path(__file__).resolve().parents[1]

def _load_schema(relpath: str) -> dict:
    p = ROOT / relpath
    assert p.exists(), f"Missing schema file: {p}"
    return json.loads(p.read_text(encoding="utf-8"))

def _assert_schema_contract(schema: dict, expected_id: str) -> None:
    assert schema.get("$id") == expected_id, f"$id mismatch: {schema.get('$id')} != {expected_id}"
    props = schema.get("properties", {})
    assert "schema" in props, "missing properties.schema"
    assert props["schema"].get("const") == expected_id, "properties.schema.const mismatch"

def test_lang_schema_v1_matches_contract_id():
    s = _load_schema("schemas/lang.schema.json")
    _assert_schema_contract(s, LANG_SCHEMA_V1)

def test_ast_schema_v1_matches_contract_id():
    s = _load_schema("schemas/ast.schema.json")
    _assert_schema_contract(s, AST_SCHEMA_V1)


def test_plasticity_schema_v1_matches_contract_id():
    s = _load_schema("schemas/plasticity.schema.json")
    _assert_schema_contract(s, PLASTICITY_SCHEMA_V1)
