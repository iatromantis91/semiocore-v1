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
    witness.txt   (selected permutation + metrics)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Tuple


def _quote(s: str) -> str:
    # For pretty printing only
    if any(c in s for c in [' ', '\t', '"', "'"]):
        return f'"{s}"'
    return s


def run(cmd: list[str], cwd: Optional[Path] = None) -> None:
    print("+", " ".join(_quote(c) for c in cmd))
    subprocess.check_call(cmd, cwd=str(cwd) if cwd else None)


def ensure_editable_install(py: str) -> None:
    run([py, "-m", "pip", "install", "-e", "."])


def ensure_matplotlib(py: str) -> None:
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

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _objs_from_trace(tr: dict[str, Any]) -> list[Any]:
    ev = tr.get("events") or []
    if not isinstance(ev, list):
        return []
    return [e.get("obj") for e in ev if isinstance(e, dict)]


def _hamming(a: list[Any], b: list[Any]) -> int:
    m = min(len(a), len(b))
    return sum(1 for i in range(m) if a[i] != b[i]) + abs(len(a) - len(b))


def pick_best_perm_trace(
    base_trace_path: Path,
    ctxscan_report: dict[str, Any],
    perm_dir: Path,
    *,
    fallback_index: int = 1,
) -> Tuple[Path, dict[str, Any]]:
    """
    Choose the permutation trace that maximizes observable divergence vs the base trace.

    Score (lexicographic):
      1) abs(delta_kappa)
      2) obj_hamming
      3) abs(delta_rho)

    Returns:
      (best_perm_trace_path, metrics_dict)
    """
    base_tr = load_json(base_trace_path)
    base_sum = base_tr.get("summary") or {}
    base_kappa = _safe_float(base_sum.get("kappa"))
    base_rho = _safe_float(base_sum.get("rho"))
    base_objs = _objs_from_trace(base_tr)

    candidates = sorted(perm_dir.glob("perm_*.trace.json"))
    if not candidates:
        # fallback: perm_{idx}
        p = perm_dir / f"perm_{fallback_index:02d}.trace.json"
        if p.exists():
            candidates = [p]
        else:
            raise FileNotFoundError(f"No permutation trace files found in: {perm_dir}")

    perms = ctxscan_report.get("permutations") or []
    baseline_ctx = (ctxscan_report.get("baseline_ctx") or "")

    best_path: Optional[Path] = None
    best_score: Optional[tuple[float, int, float]] = None
    best_meta: dict[str, Any] = {}

    for fp in candidates:
        tr = load_json(fp)
        s = tr.get("summary") or {}
        k = _safe_float(s.get("kappa"))
        r = _safe_float(s.get("rho"))
        objs = _objs_from_trace(tr)

        dk = (k - base_kappa) if (k is not None and base_kappa is not None) else None
        dr = (r - base_rho) if (r is not None and base_rho is not None) else None
        ham = _hamming(base_objs, objs)

        score = (
            abs(dk) if dk is not None else -1.0,
            ham,
            abs(dr) if dr is not None else -1.0,
        )

        if best_score is None or score > best_score:
            best_score = score
            best_path = fp

            # try to recover perm index and ctx from report
            perm_ctx = ""
            try:
                # filename "perm_03.trace.json" -> 3
                name = fp.name
                idx = int(name.split("_")[1].split(".")[0])
                if isinstance(perms, list) and idx < len(perms) and isinstance(perms[idx], dict):
                    perm_ctx = perms[idx].get("ctx") or ""
            except Exception:
                perm_ctx = ""

            best_meta = {
                "base_trace": str(base_trace_path),
                "perm_trace": str(fp),
                "baseline_ctx": baseline_ctx,
                "permuted_ctx": perm_ctx,
                "obj_hamming": ham,
                "delta_kappa": dk,
                "delta_rho": dr,
                "base_kappa": base_kappa,
                "perm_kappa": k,
                "base_rho": base_rho,
                "perm_rho": r,
                "score": {"abs_delta_kappa": score[0], "obj_hamming": score[1], "abs_delta_rho": score[2]},
            }

    assert best_path is not None
    return best_path, best_meta


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
    ap.add_argument("--seed-count", type=int, default=1, help="Number of seeds for E2 sweep (default: 1)")
    ap.add_argument(
    "--sweep-tables",
    action="store_true",
    help="Use E2 seed sweep traces for make_tables (via --e2-glob/--e2p-glob).",
)

    ap.add_argument(
        "--e2-ctx",
        default="Add(0.5) >> Sign >> JitterU(0.05)",

    )
    ap.add_argument("--e2-channel", default="chN", help="World channel sensed by E2 (default: chN)")

    # Base programs (E1/E3 are optional but useful for tables/figures/snippets)
    ap.add_argument("--e1-program", default="programs/e1_fusion.sc", help="E1 .sc program path")
    ap.add_argument("--e3-program", default="programs/e3_jitter_seed.sc", help="E3 .sc program path")
    ap.add_argument("--no-e1", action="store_true", help="Skip running E1")
    ap.add_argument("--no-e3", action="store_true", help="Skip running E3")

    # Permutation fallback index (used only if no perm files exist)
    ap.add_argument("--perm-index", type=int, default=1, help="Fallback perm index (default: 1 -> perm_01)")

    args = ap.parse_args()

    py = sys.executable
    outroot = Path(args.outdir)
    world = Path(args.world)

    if args.clean and outroot.exists():
        shutil.rmtree(outroot)
    outroot.mkdir(parents=True, exist_ok=True)

    if args.install:
        ensure_editable_install(py)

    # Generate paper-grade E2 program under outroot/programs (keeps repo clean)
    # ---------------------------
    # Paper-grade E2 seed sweep
    # ---------------------------
    e2_prog_dir = outroot / "programs"
    e2_prog_dir.mkdir(parents=True, exist_ok=True)

    sweep_dir = outroot / "e2_sweep"
    sweep_dir.mkdir(parents=True, exist_ok=True)

    seeds = [args.seed + i for i in range(args.seed_count)]

    # Legacy/primary outputs (seed 0): keep existing filenames for downstream tooling
    e2_program = e2_prog_dir / "e2_border_paper.sc"
    e2_manifest = outroot / "e2.manifest.json"
    e2_trace = outroot / "e2.trace.json"
    ctxscan_report = outroot / "e2.ctxscan.json"
    ctxscan_dir = outroot / "e2.ctxscan.traces"
    e2p_trace = outroot / "e2p.trace.json"
    witness_txt = outroot / "witness.txt"

    # Paths for E1/E3 (unchanged)
    e1_manifest = outroot / "e1.manifest.json"
    e1_trace = outroot / "e1.trace.json"
    e3_manifest = outroot / "e3.manifest.json"
    e3_trace = outroot / "e3.trace.json"

    # Run E1/E3 once
    if not args.no_e1:
        run([py, "-m", "semioc", "run", args.e1_program, "--world", str(world),
             "--emit-manifest", str(e1_manifest), "--emit-trace", str(e1_trace)])
    if not args.no_e3:
        run([py, "-m", "semioc", "run", args.e3_program, "--world", str(world),
             "--emit-manifest", str(e3_manifest), "--emit-trace", str(e3_trace)])

    # Seed sweep + deterministic witness (seed 0) -----------------------------

    best_src_path: Path | None = None
    best_meta: dict[str, Any] | None = None
    best_seed_i: int | None = None
    best_seed_tag: str | None = None
    best_seed_program: Path | None = None
    best_seed_trace: Path | None = None
    best_seed_ctxrep: Path | None = None
    best_seed_ctxdir: Path | None = None

    for i, sd in enumerate(seeds):
        tag = f"{i:02d}"

        # seed 0 uses legacy paths; others go to sweep_dir
        if i == 0:
            prog_i = e2_program
            manifest_i = e2_manifest
            trace_i = e2_trace
            ctxrep_i = ctxscan_report
            ctxdir_i = ctxscan_dir
            e2p_out_i: Path | None = None   # do NOT write stable e2p inside loop
        else:
            prog_i = e2_prog_dir / f"e2_border_paper_seed_{tag}.sc"
            manifest_i = sweep_dir / f"e2_seed_{tag}.manifest.json"
            trace_i = sweep_dir / f"e2_seed_{tag}.trace.json"
            ctxrep_i = sweep_dir / f"e2_seed_{tag}.ctxscan.json"
            ctxdir_i = sweep_dir / f"e2_seed_{tag}.ctxscan.traces"
            e2p_out_i = sweep_dir / f"e2p_seed_{tag}.trace.json"

        write_e2_paper_program(
            prog_i,
            steps=args.steps,
            seed=sd,
            ctx=args.e2_ctx,
            channel=args.e2_channel,
        )

        run([py, "-m", "semioc", "run", str(prog_i), "--world", str(world),
             "--emit-manifest", str(manifest_i), "--emit-trace", str(trace_i)])

        run([py, "-m", "semioc", "ctxscan", str(prog_i), "--world", str(world),
            "--emit-report", str(ctxrep_i), "--emit-dir", str(ctxdir_i),
            "--max-perms", str(args.max_perms)])

        report_i = load_json(ctxrep_i)
        perm_path_i, meta_i = pick_best_perm_trace(
            trace_i, report_i, ctxdir_i, fallback_index=args.perm_index
        )

        # Always capture seed 0 as the unique witness (independent of sweep copies)
        if i == 0:
            best_src_path = perm_path_i
            best_meta = meta_i

            best_seed_i = i
            best_seed_tag = tag
            best_seed_program = prog_i
            best_seed_trace = trace_i
            best_seed_ctxrep = ctxrep_i
            best_seed_ctxdir = ctxdir_i

        # Optional: write per-seed e2p outputs (sweep only)
        if e2p_out_i is not None:
            shutil.copyfile(perm_path_i, e2p_out_i)

    # Single source of truth for stable e2p/witness + witness.txt
    if best_src_path is None or best_meta is None:
        raise RuntimeError("Seed 0 did not produce a witness perm trace/meta.")

    if best_seed_i != 0:
        raise SystemExit(f"Internal error: seed_witness expected 0, got {best_seed_i}")

    # IMPORTANT: overwrite stable e2p even if it exists (correct even without --clean)
    shutil.copyfile(best_src_path, e2p_trace)
    perm_sha = sha256_file(best_src_path)
    e2p_sha  = sha256_file(e2p_trace)
    sha_match = (perm_sha == e2p_sha)

    def norm(p: Path | None) -> str:
        return "" if p is None else str(p).replace("\\", "/")

    # Write witness.txt from best_meta/best_src_path (no recomputation)
    meta = dict(best_meta)
    meta["perm_trace"] = norm(best_src_path)
    # base_trace comes from meta; normalize if present
    if meta.get("base_trace"):
        meta["base_trace"] = str(meta["base_trace"]).replace("\\", "/")

    lines = [
        "SemioCore paper-grade witness selection",
        "schema_version : 1",

        # Explicit witness seed (no inference required)
        f"seed_witness   : {best_seed_i}",
        f"seed_tag       : {best_seed_tag}",
        f"seed_program   : {norm(best_seed_program)}",
        f"seed_trace     : {norm(best_seed_trace)}",
        f"seed_ctxreport : {norm(best_seed_ctxrep)}",
        f"seed_ctxdir    : {norm(best_seed_ctxdir)}",

        # Stable output and exact chosen perm trace
        f"e2p_trace      : {norm(e2p_trace)}",
        f"base_trace     : {meta.get('base_trace')}",
        f"perm_trace     : {meta.get('perm_trace')}",
        f"perm_trace_src : {norm(best_src_path)}",
        f"perm_sha256    : {perm_sha}",
        f"e2p_sha256     : {e2p_sha}",
        f"sha_match      : {sha_match}",

        # Context + metrics actually present in best_meta
        f"baseline_ctx   : {meta.get('baseline_ctx')}",
        f"permuted_ctx   : {meta.get('permuted_ctx')}",
        f"obj_hamming    : {meta.get('obj_hamming')}",
        f"delta_kappa    : {meta.get('delta_kappa')}",
        f"delta_rho      : {meta.get('delta_rho')}",
        f"base_kappa     : {meta.get('base_kappa')}",
        f"perm_kappa     : {meta.get('perm_kappa')}",
        f"base_rho       : {meta.get('base_rho')}",
        f"perm_rho       : {meta.get('perm_rho')}",
        f"score          : {meta.get('score')}",
    ]
    witness_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Ensure seed 00 exists in sweep_dir for globbing (tables/figures)
    if args.sweep_tables and args.seed_count > 1:
        shutil.copyfile(e2_trace, sweep_dir / "e2_seed_00.trace.json")
        shutil.copyfile(e2p_trace, sweep_dir / "e2p_seed_00.trace.json")

    tables_dir = outroot / "paper_tables"
    figs_dir = outroot / "paper_figures"
    cites_md = outroot / "paper_citations.md"

    if args.no_e1 or args.no_e3:
        raise SystemExit("For paper_figures.make_tables/make_figures as currently written, do not use --no-e1/--no-e3.")

    tables_cmd = [
        py, "-m", "paper_figures.make_tables",
        "--outdir", str(tables_dir),
        "--e1", str(e1_trace),
        "--e3", str(e3_trace),
        "--ctxreport", str(ctxscan_report),
    ]

    if args.sweep_tables and args.seed_count > 1:
        tables_cmd += [
            "--e2-glob", str(sweep_dir / "e2_seed_*.trace.json"),
            "--e2p-glob", str(sweep_dir / "e2p_seed_*.trace.json"),
        ]
    else:
        tables_cmd += ["--e2", str(e2_trace), "--e2p", str(e2p_trace)]

    run(tables_cmd)

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

    print("OK: paper-grade artifacts")
    print("  outdir   :", outroot)
    print("  program  :", e2_program)
    print("  ctxscan  :", ctxscan_report)
    print("  e2p(best):", e2p_trace)
    print("  witness  :", witness_txt)
    print("  tables   :", tables_dir)
    print("  figures  :", figs_dir)
    print("  citations:", cites_md)


if __name__ == "__main__":
    main()
