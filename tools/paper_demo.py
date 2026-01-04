import os
import sys
import subprocess

PY = sys.executable

def run(cmd):
    print("+ " + " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    os.makedirs("out", exist_ok=True)

    # 0) install editable
    run([PY, "-m", "pip", "install", "-e", "."])

    # 1) run traces
    run([PY, "-m", "semioc", "run", "programs/e1_fusion.sc",
         "--world", "fixtures/world/paper_world.json",
         "--emit-manifest", "out/e1.manifest.json",
         "--emit-trace", "out/e1.trace.json"])

    run([PY, "-m", "semioc", "run", "programs/e2_border.sc",
         "--world", "fixtures/world/paper_world.json",
         "--emit-manifest", "out/e2.manifest.json",
         "--emit-trace", "out/e2.trace.json"])

    run([PY, "-m", "semioc", "run", "programs/e3_jitter_seed.sc",
         "--world", "fixtures/world/paper_world.json",
         "--emit-manifest", "out/e3.manifest.json",
         "--emit-trace", "out/e3.trace.json"])

    # 2) replay
    run([PY, "-m", "semioc", "replay",
         "--manifest", "fixtures/expected/e3.manifest.json",
         "--emit-trace", "out/e3.replay.trace.json"])

    # 3) ctxscan (IMPORTANT: emit-dir must be present to match fixtures)
    os.makedirs("out/e1.ctxscan.traces", exist_ok=True)
    os.makedirs("out/e2.ctxscan.traces", exist_ok=True)
    os.makedirs("out/e3.ctxscan.traces", exist_ok=True)

    run([PY, "-m", "semioc", "ctxscan", "programs/e1_fusion.sc",
         "--world", "fixtures/world/paper_world.json",
         "--emit-report", "out/e1.ctxscan.json",
         "--emit-dir", "out/e1.ctxscan.traces"])

    run([PY, "-m", "semioc", "ctxscan", "programs/e2_border.sc",
         "--world", "fixtures/world/paper_world.json",
         "--emit-report", "out/e2.ctxscan.json",
         "--emit-dir", "out/e2.ctxscan.traces"])

    run([PY, "-m", "semioc", "ctxscan", "programs/e3_jitter_seed.sc",
         "--world", "fixtures/world/paper_world.json",
         "--emit-report", "out/e3.ctxscan.json",
         "--emit-dir", "out/e3.ctxscan.traces"])

    # 4) compare traces
    run([PY, "tools/compare_trace.py", "fixtures/expected/e1.trace.json", "out/e1.trace.json"])
    run([PY, "tools/compare_trace.py", "fixtures/expected/e2.trace.json", "out/e2.trace.json"])
    run([PY, "tools/compare_trace.py", "fixtures/expected/e3.trace.json", "out/e3.trace.json"])
    run([PY, "tools/compare_trace.py", "fixtures/expected/e3.replay.trace.json", "out/e3.replay.trace.json"])

    # 5) compare ctxscan reports
    run([PY, "tools/compare_json.py", "fixtures/expected/e1.ctxscan.json", "out/e1.ctxscan.json"])
    run([PY, "tools/compare_json.py", "fixtures/expected/e2.ctxscan.json", "out/e2.ctxscan.json"])
    run([PY, "tools/compare_json.py", "fixtures/expected/e3.ctxscan.json", "out/e3.ctxscan.json"])

    print("OK: paper-demo")

if __name__ == "__main__":
    main()
