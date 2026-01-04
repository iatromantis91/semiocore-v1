import subprocess
import sys

def test_cli_help_runs():
    r = subprocess.run([sys.executable, "-m", "semioc", "--help"], capture_output=True, text=True)
    assert r.returncode == 0, (r.stdout + "\n" + r.stderr)
