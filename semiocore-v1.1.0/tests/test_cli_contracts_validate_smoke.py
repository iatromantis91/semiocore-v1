import subprocess
import sys
from pathlib import Path


def test_cli_contracts_validate_smoke():
    repo_root = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, "-m", "semioc", "contracts", "validate"]
    proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    assert proc.returncode == 0, f"contracts validate failed. stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "OK" in proc.stdout
