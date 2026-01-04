#!/usr/bin/env python3
import subprocess, sys

def main():
    if len(sys.argv) != 3:
        print("Usage: compare_trace.py EXPECTED TRACE")
        sys.exit(2)
    expected, actual = sys.argv[1], sys.argv[2]
    cmd = [sys.executable, "tools/compare_json.py", expected, actual, "--tol", "1e-9"]
    raise SystemExit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
