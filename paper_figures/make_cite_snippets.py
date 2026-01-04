#!/usr/bin/env python3
import argparse
import csv
import os
from typing import Dict, List, Any, Optional

def read_csv(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r)

def fnum(x: Optional[str], nd: int = 3) -> str:
    if x is None:
        return "NA"
    s = str(x).strip()
    if s == "" or s.lower() == "none":
        return "NA"
    try:
        v = float(s)
        fmt = f"{{:.{nd}f}}"
        return fmt.format(v)
    except Exception:
        return s

def as_int(x: Optional[str]) -> str:
    if x is None:
        return "NA"
    s = str(x).strip()
    if s == "" or s.lower() == "none":
        return "NA"
    try:
        return str(int(float(s)))
    except Exception:
        return s

def find_run(runs: List[Dict[str, Any]], label_prefix: str) -> Dict[str, Any]:
    for r in runs:
        if str(r.get("label","")).startswith(label_prefix):
            return r
    raise KeyError(f"Run not found: {label_prefix}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out/paper_figures/cite_snippets.md")
    ap.add_argument("--runs_csv", default="out/paper_figures/table_runs.csv")
    ap.add_argument("--ctx_csv", default="out/paper_figures/table_ctxreport.csv")
    ap.add_argument("--figdir", default="out/paper_figures")
    args = ap.parse_args()

    runs = read_csv(args.runs_csv)
    ctx = read_csv(args.ctx_csv)
    if not ctx:
        raise RuntimeError("ctxreport table is empty")

    e1 = find_run(runs, "E1")
    e2b = find_run(runs, "E2 base")
    e2p = find_run(runs, "E2 perm")
    e3 = find_run(runs, "E3")

    ctx0 = ctx[0]
    obj_h = as_int(ctx0.get("obj_hamming"))
    d_k = fnum(ctx0.get("delta_kappa"), 3)
    d_r = fnum(ctx0.get("delta_rho"), 3)

    k_e1 = fnum(e1.get("kappa"), 3)
    k_e2b = fnum(e2b.get("kappa"), 3)
    k_e2p = fnum(e2p.get("kappa"), 3)
    k_e3 = fnum(e3.get("kappa"), 3)

    rho_e1 = fnum(e1.get("rho"), 3)
    rho_e2b = fnum(e2b.get("rho"), 3)
    rho_e2p = fnum(e2p.get("rho"), 3)
    rho_e3 = fnum(e3.get("rho"), 3)

    ctx_base = ctx0.get("base_ctx", "NA")
    ctx_perm = ctx0.get("permuted_ctx", "NA")

    fig1 = os.path.join(args.figdir, "fig_e2_kappa.png")
    fig2 = os.path.join(args.figdir, "fig_e2_r_eff.png")
    fig3 = os.path.join(args.figdir, "fig_all_r_eff.png")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# SemioCore v1.0 — Paper-ready snippets (auto-generated)\n\n")
        f.write("This file is generated from `table_runs.csv` and `table_ctxreport.csv`.\n")
        f.write("Do not edit manually; regenerate via `make paper-figures`.\n\n")

        f.write("## Results text (copy/paste)\n\n")
        f.write(
            f"In the v1.0 paper demo, the Strict protocol yields ESE traces and defined observables "
            f"for minimal runs (N=2), with stable event rates ρ (E1: ρ={rho_e1}; E2 base: ρ={rho_e2b}; "
            f"E2 permuted: ρ={rho_e2p}; E3: ρ={rho_e3}), as summarized in Table 1.\n\n"
        )
        f.write(
            f"E2 exhibits context sensitivity under regime permutation: comparing `{ctx_base}` against `{ctx_perm}`, "
            f"the observable divergence appears as a shift in κ (κ_base={k_e2b} → κ_perm={k_e2p}), with "
            f"CtxDiv(obj_hamming={obj_h}, Δκ={d_k}, Δρ={d_r}), as reported in Table 3 and visualized in Figure 1.\n\n"
        )
        f.write(
            f"E1 illustrates a safe affine fusion rewrite without altering observables (κ={k_e1}), supporting the "
            f"paper’s distinction between strong equivalence and observable equivalence in practice (Table 1).\n\n"
        )
        f.write(
            f"E3 demonstrates seed-based reproducibility: execution and replay coincide in effective scores r_eff "
            f"and κ (κ={k_e3}), consistent with the manifest+trace contract.\n\n"
        )

        f.write("## Table callouts\n\n")
        f.write("- **Table 1** summarizes, for each run, the applied context, N, ΔT, ρ, κ, and the observed object sequence.\n")
        f.write("- **Table 2** provides event-level comparisons for E2 (base vs permuted): r_eff, obj, κ_loc.\n")
        f.write("- **Table 3** reports contextuality diagnostics (CtxDiv) for E2 under context permutation.\n\n")

        f.write("## Figure captions (copy/paste)\n\n")
        f.write(
            "**Figure 1.** κ divergence in E2 under context permutation (base vs permuted): the same world signal "
            "can yield different outcomes when the measurement regime reorders non-commuting operators.\n\n"
        )
        f.write(
            "**Figure 2.** Effective score trajectories r_eff in E2 (base vs permuted). Reordering the pipeline "
            "changes r_eff and thus the observed classification.\n\n"
        )
        f.write(
            "**Figure 3.** r_eff across all demo runs (E1, E2 base, E2 permuted, E3) as a coherence and sanity view.\n\n"
        )

        f.write("## Artifact pointers\n\n")
        f.write(f"- Figure 1: `{fig1}`\n")
        f.write(f"- Figure 2: `{fig2}`\n")
        f.write(f"- Figure 3: `{fig3}`\n")

    print("OK: wrote", args.out)

if __name__ == "__main__":
    main()
