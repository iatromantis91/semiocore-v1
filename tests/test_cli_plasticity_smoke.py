import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import jsonschema


def _load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def test_cli_plasticity_smoke_emits_expected_report():
    repo_root = Path(__file__).resolve().parents[1]

    traces = [
        repo_root / "fixtures" / "expected" / "e1.trace.json",
        repo_root / "fixtures" / "expected" / "e2.trace.json",
        repo_root / "fixtures" / "expected" / "e3.trace.json",
    ]
    for p in traces:
        assert p.is_file(), f"Missing trace fixture: {p}"

    schema_path = repo_root / "schemas" / "plasticity.schema.json"
    expected_path = repo_root / "expected" / "plasticity" / "basic.plasticity.json"
    assert schema_path.is_file()
    assert expected_path.is_file()

    with TemporaryDirectory() as td:
        out_path = Path(td) / "out.plasticity.json"
        cmd = [
            sys.executable,
            "-m",
            "semioc",
            "plasticity",
            "--traces",
            *[str(p) for p in traces],
            "--ctx",
            "Add(0.5)>>Sign",
            "--channel",
            "chN",
            "--emit-report",
            str(out_path),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
        assert proc.returncode == 0, f"CLI failed. stdout={proc.stdout}\nstderr={proc.stderr}"
        assert out_path.is_file(), "CLI did not emit report"

        out_obj = _load_json(out_path)
        schema = _load_json(schema_path)
        jsonschema.validate(instance=out_obj, schema=schema)

        expected_obj = _load_json(expected_path)
        assert out_obj == expected_obj, "CLI output differs from golden fixture"
