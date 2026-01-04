import json
import subprocess
import sys
from pathlib import Path

def test_cli_parse_emits_json(tmp_path: Path):
    # crea un programa mínimo temporal
    prog = tmp_path / "basic.sc"
    prog.write_text("", encoding="utf-8")

    out = subprocess.check_output(
        [sys.executable, "-m", "semioc", "parse", prog.as_posix()],
        text=True,
    )
    obj = json.loads(out)
    assert obj["ast"]["node"] == "Program"
    assert obj["ast"]["body"] == []
