import json
from pathlib import Path

import jsonschema

from semioc.contract_ids import PLASTICITY_SCHEMA_V1
from semioc.plasticity import compute_plasticity_report

ROOT = Path(__file__).resolve().parents[1]

def test_golden_plasticity_fixture_validates_against_schema():
    schema_path = ROOT / "schemas" / "plasticity.schema.json"
    fixture_path = ROOT / "expected" / "plasticity" / "basic.plasticity.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture.get("schema") == PLASTICITY_SCHEMA_V1
    jsonschema.validate(instance=fixture, schema=schema)

def test_plasticity_runner_matches_golden_fixture():
    fixture_path = ROOT / "expected" / "plasticity" / "basic.plasticity.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    trace_paths = [
        ROOT / "fixtures" / "expected" / "e1.trace.json",
        ROOT / "fixtures" / "expected" / "e2.trace.json",
        ROOT / "fixtures" / "expected" / "e3.trace.json",
    ]
    report = compute_plasticity_report(
        trace_paths,
        ctx=fixture["ctx"],
        channel=fixture["channel"],
        protocol=fixture["protocol"],
        window_size=fixture["windowing"]["size"],
        window_step=fixture["windowing"]["step"],
        program_file=fixture["program_file"],
    )
    assert report == fixture
