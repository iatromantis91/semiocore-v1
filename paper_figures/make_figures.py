#!/usr/bin/env python3
import argparse
import os
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from paper_figures.trace_utils import load_json, events_table

def line_r_eff(ax, rows: List[Dict[str, Any]], label: str) -> None:
    xs = [r["step"] for r in rows]
    ys = [r["r_eff"] for r in rows]
    ax.plot(xs, ys, marker="o", label=label)

def bar_kappa(ax, labels: List[str], kappas: List[float]) -> None:
    ax.bar(labels, kappas)
    ax.set_ylabel("kappa")
    ax.set_xlabel("run")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="out/paper_figures")
    ap.add_argument("--e2", required=True)
    ap.add_argument("--e2p", required=True)
    ap.add_argument("--e1", required=True)
    ap.add_argument("--e3", required=True)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    e1 = load_json(args.e1)
    e2 = load_json(args.e2)
    e2p = load_json(args.e2p)
    e3 = load_json(args.e3)

    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111)
    k_base = float(e2["summary"]["kappa"])
    k_perm = float(e2p["summary"]["kappa"])
    bar_kappa(ax1, ["E2 base", "E2 perm"], [k_base, k_perm])
    ax1.set_title("E2: kappa divergence under context permutation")
    fig1.tight_layout()
    fig1.savefig(os.path.join(args.outdir, "fig_e2_kappa.png"), dpi=300)
    plt.close(fig1)

    fig2 = plt.figure()
    ax2 = fig2.add_subplot(111)
    line_r_eff(ax2, events_table(e2), "E2 base (Add>>Sign)")
    line_r_eff(ax2, events_table(e2p), "E2 perm (Sign>>Add)")
    ax2.set_xlabel("step")
    ax2.set_ylabel("r_eff")
    ax2.set_title("E2: effective score r_eff (base vs permuted)")
    ax2.legend()
    fig2.tight_layout()
    fig2.savefig(os.path.join(args.outdir, "fig_e2_r_eff.png"), dpi=300)
    plt.close(fig2)

    fig3 = plt.figure()
    ax3 = fig3.add_subplot(111)
    line_r_eff(ax3, events_table(e1), "E1 (fusion)")
    line_r_eff(ax3, events_table(e2), "E2 base")
    line_r_eff(ax3, events_table(e2p), "E2 perm")
    line_r_eff(ax3, events_table(e3), "E3 (seeded jitter)")
    ax3.set_xlabel("step")
    ax3.set_ylabel("r_eff")
    ax3.set_title("SemioCore paper demo: r_eff by run")
    ax3.legend()
    fig3.tight_layout()
    fig3.savefig(os.path.join(args.outdir, "fig_all_r_eff.png"), dpi=300)
    plt.close(fig3)

    print("OK: figures written to", args.outdir)

if __name__ == "__main__":
    main()
