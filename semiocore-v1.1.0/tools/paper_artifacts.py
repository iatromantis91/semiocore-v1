import argparse
import glob
import json
import os
import shutil
import subprocess
import sys


def run(cmd):
    print("+ " + " ".join(cmd))
    subprocess.check_call(cmd)


def pick_e2p(outdir: str, ctxreport_path: str) -> str:
    """
    Pick the perm_XX.trace.json for E2 based on ctxscan witness.perm_i when available.
    Falls back to perm_01 if present, else first perm_*.trace.json found.
    """
    traces_dir = os.path.join(outdir, "e2.ctxscan.traces")
    if not os.path.isdir(traces_dir):
        raise FileNotFoundError(f"Missing ctxscan traces dir: {traces_dir}")

    perm_i = None
    try:
        with open(ctxreport_path, "r", encoding="utf-8") as f:
            ctxr = json.load(f)
        w = ctxr.get("witness") or {}
        if isinstance(w, dict) and "perm_i" in w and w["perm_i"] is not None:
            perm_i = int(w["perm_i"])
    except Exception:
        perm_i = None

    if perm_i is not None:
        cand = os.path.join(traces_dir, f"perm_{perm_i:02d}.trace.json")
        if os.path.exists(cand):
            return cand

    cand01 = os.path.join(traces_dir, "perm_01.trace.json")
    if os.path.exists(cand01):
        return cand01

    perms = sorted(glob.glob(os.path.join(traces_dir, "perm_*.trace.json")))
    if not perms:
        raise FileNotFoundError(f"No perm traces found under: {traces_dir}")
    return perms[0]


def main():
    ap = argparse.ArgumentParser(description="Run full paper demo + generate paper artifacts.")
    ap.add_argument("--outdir", default="out", help="Output directory root (default: out)")
    ap.add_argument("--clean", action="store_true", help="Delete outdir before running")
    ap.add_argument("--skip-demo", action="store_true", help="Skip tools/paper_demo.py (assumes outdir already populated)")
    ap.add_argument("--skip-figures", action="store_true", help="Skip figure generation")
    args = ap.parse_args()

    outdir = args.outdir

    if args.clean:
        shutil.rmtree(outdir, ignore_errors=True)
    os.makedirs(outdir, exist_ok=True)

    py = sys.executable

    # 1) Demo (generates out/* and validates expected fixtures)
    if not args.skip_demo:
        run([py, "tools/paper_demo.py"])

    # Paths produced by demo
    e1 = os.path.join(outdir, "e1.trace.json")
    e2 = os.path.join(outdir, "e2.trace.json")
    e3 = os.path.join(outdir, "e3.trace.json")
    ctxreport = os.path.join(outdir, "e2.ctxscan.json")

    for p in [e1, e2, e3, ctxreport]:
        if not os.path.exists(p):
            raise FileNotFoundError(f"Missing required artifact: {p}")

    e2p = pick_e2p(outdir, ctxreport)

    # 2) Tables
    tables_dir = os.path.join(outdir, "paper_tables")
    run([
        py, "-m", "paper_figures.make_tables",
        "--outdir", tables_dir,
        "--e1", e1,
        "--e2", e2,
        "--e2p", e2p,
        "--e3", e3,
        "--ctxreport", ctxreport,
    ])

    # 3) Figures
    fig_dir = os.path.join(outdir, "paper_figures")
    if not args.skip_figures:
        try:
            import matplotlib  # noqa: F401
        except Exception:
            raise RuntimeError("matplotlib is required for figures. Install via: py -3 -m pip install matplotlib")

        run([
            py, "-m", "paper_figures.make_figures",
            "--outdir", fig_dir,
            "--e1", e1,
            "--e2", e2,
            "--e2p", e2p,
            "--e3", e3,
        ])

    # 4) Cite snippets
    cites_out = os.path.join(outdir, "paper_citations.md")
    run([
        py, "-m", "paper_figures.make_cite_snippets",
        "--out", cites_out,
        "--runs_csv", os.path.join(tables_dir, "table_runs.csv"),
        "--ctx_csv", os.path.join(tables_dir, "table_ctxreport.csv"),
        "--figdir", fig_dir,
    ])

    print("OK: paper-artifacts")
    print(f"  tables: {tables_dir}")
    print(f"  figures: {fig_dir}")
    print(f"  citations: {cites_out}")


if __name__ == "__main__":
    main()
