import os
import subprocess
import sys
from pathlib import Path

def run(cmd):
    print("+", " ".join(cmd))
    r = subprocess.run(cmd, shell=False)
    if r.returncode != 0:
        raise SystemExit(r.returncode)

def main():
    # Ensure we run from repo root (…/semiocore-v1)
    repo_root = Path(__file__).resolve().parents[1]
    os.chdir(repo_root)

    os.makedirs("out", exist_ok=True)

    # Ensure editable install is present (reproducible for reviewers)
    run([sys.executable, "-m", "pip", "install", "-e", "."])

    world = "fixtures/world/paper_world.json"

    # run: E1/E2/E3
    run([sys.executable, "-m", "semioc", "run", "programs/e1_fusion.sc",
         "--world", world, "--emit-manifest", "out/e1.manifest.json", "--emit-trace", "out/e1.trace.json"])
    run([sys.executable, "-m", "semioc", "run", "programs/e2_border.sc",
         "--world", world, "--emit-manifest", "out/e2.manifest.json", "--emit-trace", "out/e2.trace.json"])
    run([sys.executable, "-m", "semioc", "run", "programs/e3_jitter_seed.sc",
         "--world", world, "--emit-manifest", "out/e3.manifest.json", "--emit-trace", "out/e3.trace.json"])

    # replay: from expected manifest
    run([sys.executable, "-m", "semioc", "replay",
         "--manifest", "fixtures/expected/e3.manifest.json",
         "--emit-trace", "out/e3.replay.trace.json"])

    # ctxscan: E1/E2/E3
    run([sys.executable, "-m", "semioc", "ctxscan", "programs/e1_fusion.sc",
         "--world", world, "--emit-report", "out/e1.ctxscan.json"])
    run([sys.executable, "-m", "semioc", "ctxscan", "programs/e2_border.sc",
         "--world", world, "--emit-report", "out/e2.ctxscan.json"])
    run([sys.executable, "-m", "semioc", "ctxscan", "programs/e3_jitter_seed.sc",
         "--world", world, "--emit-report", "out/e3.ctxscan.json"])

    # compare: traces
    run([sys.executable, "tools/compare_trace.py", "fixtures/expected/e1.trace.json", "out/e1.trace.json"])
    run([sys.executable, "tools/compare_trace.py", "fixtures/expected/e2.trace.json", "out/e2.trace.json"])
    run([sys.executable, "tools/compare_trace.py", "fixtures/expected/e3.trace.json", "out/e3.trace.json"])
    run([sys.executable, "tools/compare_trace.py", "fixtures/expected/e3.replay.trace.json", "out/e3.replay.trace.json"])

    # compare: ctxscan reports
    run([sys.executable, "tools/compare_json.py", "fixtures/expected/e1.ctxscan.json", "out/e1.ctxscan.json"])
    run([sys.executable, "tools/compare_json.py", "fixtures/expected/e2.ctxscan.json", "out/e2.ctxscan.json"])
    run([sys.executable, "tools/compare_json.py", "fixtures/expected/e3.ctxscan.json", "out/e3.ctxscan.json"])

    print("OK: paper-demo")

if __name__ == "__main__":
    main()
