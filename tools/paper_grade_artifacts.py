#!/usr/bin/env python3
"""
Paper-grade artifacts runner (no fixtures compares).

Runs:
  - semioc run: E1 (optional), E2 paper-grade (auto-generated long trace), E3 (optional)
  - semioc ctxscan on E2 paper-grade (+ per-permutation traces)
  - paper_figures.make_tables
  - paper_figures.make_figures
  - paper_figures.make_cite_snippets

Outputs (default):
  out/papergrade/
    e1.trace.json, e2.trace.json, e3.trace.json, ...
    e2.ctxscan.json + e2.ctxscan.traces/perm_XX.trace.json
    paper_tables/*.csv|.md
    paper_figures/*.png
    paper_citations.md
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def _quote(s: str) -> str:
    # For pretty printing only
    if any(c in s for c in [' ', '\t', '"', "'"]):
        return f'"{s}"'
    return s


def run(cmd: list[str], cwd: Optional[Path] = None) -> None:
    # Print in a style similar to your other runners
    print("+", " ".join(_quote(c) for c in cmd))
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def ensure_editable_install(py: str) -> None:
    # Ensures `python -m semioc ...` and `python -m paper_figures...` work reliably.
    run([py, "-m", "pip", "install", "-e", "."])


def ensure_matplotlib(py: str) -> None:
    # Make figures needs matplotlib. Install only if missing.
    try:
        subprocess.check_call([py, "-c", "import matplotlib"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        run([py, "-m", "pip", "install", "matplotlib"])


def write_e2_paper_program(dst_sc: Path, *, steps: int, seed: int, ctx: str, channel: str) -> None:
    dst_sc.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# SemioCore v1.0 — Paper-grade E2: long trace + richer context")
    lines.append(f"seed {seed};")
    lines.append(f"context {ctx} {{")
    for i in range(1, steps + 1):
        lines.append("  tick 1.0;")
        lines.append(f"  u{i} := sense {channel};")
        lines.append(f"  commit u{i};")
        lines.append("")
    lines.append("}")
    lines.append("out := summarize;")
    dst_sc.write_text("\n".join(lines), encoding="utf-8")


def load_json(p: Path) -> dict[str, Any]:
    return json.loads(p.read_text(encoding="utf-8"))


def pick_witness_perm_trace(ctxscan_report: dict[str, Any], perm_dir: Path, *, fallback_index: int = 1) -> Path:
    """
    Try to choose the most relevant permutation trace for "permuted" comparison.

    Priority:
      1) witness.trace_file (if present)
      2) witness.i -> perm_{i:02d}.trace.json
      3) permutations[fallback_index].trace_file (if present)
      4) perm_{fallback_index:02d}.trace.json
    """
    # 1) witness.trace_file
    witness = ctxscan_report.get("witness")
    if isinstance(witness, dict):
        tf = witness.get("trace_file")
        if isinstance(tf, str) and tf:
            p = Path(tf)
            if not p.is_absolute():
                p = (perm_dir.parent / tf).resolve()
            if p.exists():
                return p

        # 2) witness.i
        wi = witness.get("i")
        if isinstance(wi, int):
            p = perm_dir / f"perm_{wi:02d}.trace.json"
            if p.exists():
                return p

    # 3) permutations[fallback_index].trace_file
    perms = ctxscan_report.get("permutations") or []
    if isinstance(perms, list) and len(perms) > fallback_index:
        entry = perms[fallback_index]
        if isinstance(entry, dict):
            tf = entry.get("trace_file")
            if isinstance(tf, str) and tf:
                p = Path(tf)
                if not p.is_absolute():
                    p = (perm_dir.parent / tf).resolve()
                if p.exists():
                    return p

    # 4) fallback perm_{idx}
    p = perm_dir / f"perm_{fallback_index:02d}.trace.json"
    if p.exists():
        return p

    # As a last resort: first perm file found
    candidates = sorted(perm_dir.glob("perm_*.trace.json"))
    if candidates:
        return candidates[0]

    raise FileNotFoundError(f"No permutation trace files found in: {perm_dir}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="out/papergrade", help="Output root directory (default: out/papergrade)")
    ap.add_argument("--clean", action="store_true", help="Delete outdir before running")
    ap.add_argument("--install", action="store_true", default=True, help="pip install -e . before running (default: on)")
    ap.add_argument("--no-install", action="store_false", dest="install", help="Skip pip install -e .")

    ap.add_argument("--world", default="fixtures/world/paper_world.json", help="World JSON path")
    ap.add_argument("--max-perms", type=int, default=12, help="ctxscan --max-perms (default: 12)")

    # Paper-grade E2 program generation
    ap.add_argument("--steps", type=int, default=50, help="Number of sense/commit steps for paper-grade E2 (default: 50)")
    ap.add_argument("--seed", type=int, default=12345, help="Seed for paper-grade E2 (default: 12345)")
    ap.add_argument(
        "--e2-ctx",
        default="Add(0.5) >> Sign >> JitterU(0.05)",
        help="Context operator chain for paper-grade E2 (default: Add(0.5) >> Sign >> JitterU(0.05))",
    )
    ap.add_argument("--e2-channel", default="chN", help="World channel sensed by E2 (default: chN)")

    # Base programs (E1/E3 are optional but useful for tables/figures/snippets)
    ap.add_argument("--e1-program", default="programs/e1_fusion.sc", help="E1 .sc program path")
    ap.add_argument("--e3-program", default="programs/e3_jitter_seed.sc", help="E3 .sc program path")
    ap.add_argument("--no-e1", action="store_true", help="Skip running E1")
    ap.add_argument("--no-e3", action="store_true", help="Skip running E3")

    # Permutation selection for the "permuted witness" trace passed to make_tables/make_figures
    ap.add_argument("--perm-index", type=int, default=1, help="Fallback perm index for e2p (default: 1 -> perm_01)")

    args = ap.parse_args()

    py = sys.executable
    outroot = Path(args.outdir)
    world = Path(args.world)

    if args.clean and outroot.exists():
        shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    # Optional: ensure editable install
    if args.install:
        ensure_editable_install(py)

    # Generate paper-grade E2 program under outroot/programs (keeps repo clean)
    e2_program = outroot / "programs" / "e2_border_paper.sc"
    write_e2_paper_program(
        e2_program,
        steps=args.steps,
        seed=args.seed,
        ctx=args.e2_ctx,
        channel=args.e2_channel,
    )

    # Paths for traces/manifests
    e1_manifest = outroot / "e1.manifest.json"
    e1_trace = outroot / "e1.trace.json"
    e2_manifest = outroot / "e2.manifest.json"
    e2_trace = outroot / "e2.trace.json"
    e3_manifest = outroot / "e3.manifest.json"
    e3_trace = outroot / "e3.trace.json"

    # Run E1/E2/E3
    if not args.no_e1:
        run([py, "-m", "semioc", "run", args.e1_program, "--world", str(world), "--emit-manifest", str(e1_manifest), "--emit-trace", str(e1_trace)])
    run([py, "-m", "semioc", "run", str(e2_program), "--world", str(world), "--emit-manifest", str(e2_manifest), "--emit-trace", str(e2_trace)])
    if not args.no_e3:
        run([py, "-m", "semioc", "run", args.e3_program, "--world", str(world), "--emit-manifest", str(e3_manifest), "--emit-trace", str(e3_trace)])

    # ctxscan for E2 paper-grade
    ctxscan_report = outroot / "e2.ctxscan.json"
    ctxscan_dir = outroot / "e2.ctxscan.traces"
    run(
        [py, "-m", "semioc", "ctxscan", str(e2_program), "--world", str(world), "--emit-report", str(ctxscan_report), "--emit-dir", str(ctxscan_dir), "--max-perms", str(args.max_perms)]
    )

    # Pick permuted trace for downstream tables/figures
    report = load_json(ctxscan_report)
    e2p_trace = pick_witness_perm_trace(report, ctxscan_dir, fallback_index=args.perm_index)

    # Generate tables/figures/snippets
    tables_dir = outroot / "paper_tables"
    figs_dir = outroot / "paper_figures"
    cites_md = outroot / "paper_citations.md"

    # Tables: requires E1/E3 traces, but your make_tables signature requires them.
    # If you skip E1/E3, we still need placeholders; best practice is: don't skip them.
    if args.no_e1 or args.no_e3:
        raise SystemExit("For paper_figures.make_tables/make_figures as currently written, do not use --no-e1/--no-e3.")

    run(
        [
            py, "-m", "paper_figures.make_tables",
            "--outdir", str(tables_dir),
            "--e1", str(e1_trace),
            "--e2", str(e2_trace),
            "--e2p", str(e2p_trace),
            "--e3", str(e3_trace),
            "--ctxreport", str(ctxscan_report),
        ]
    )

    ensure_matplotlib(py)

    run(
        [
            py, "-m", "paper_figures.make_figures",
            "--outdir", str(figs_dir),
            "--e1", str(e1_trace),
            "--e2", str(e2_trace),
            "--e2p", str(e2p_trace),
            "--e3", str(e3_trace),
        ]
    )

    run(
        [
            py, "-m", "paper_figures.make_cite_snippets",
            "--out", str(cites_md),
            "--runs_csv", str(tables_dir / "table_runs.csv"),
            "--ctx_csv", str(tables_dir / "table_ctxreport.csv"),
            "--figdir", str(figs_dir),
        ]
    )

    # Minimal sanity prints
    print("OK: paper-grade artifacts")
    print("  outdir   :", outroot)
    print("  program  :", e2_program)
    print("  ctxscan  :", ctxscan_report)
    print("  e2p      :", e2p_trace)
    print("  tables   :", tables_dir)
    print("  figures  :", figs_dir)
    print("  citations:", cites_md)


if __name__ == "__main__":
    main()
