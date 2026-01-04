import json
from pathlib import Path

def test_schemas_are_valid_json():
    root = Path(__file__).resolve().parents[1]
    for p in [root / "schemas" / "lang.schema.json", root / "schemas" / "ast.schema.json", root / "schemas" / "plasticity.schema.json"]:
        assert p.exists()
        json.loads(p.read_text(encoding="utf-8"))
