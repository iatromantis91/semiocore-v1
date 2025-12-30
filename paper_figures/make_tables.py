#!/usr/bin/env python3
import argparse
import csv
import os
from typing import Any, Dict, List

from paper_figures.trace_utils import load_json, summarize_trace, events_table

def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def md_table(rows: List[Dict[str, Any]], cols: List[str]) -> str:
    header = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |\n"
    body_lines = []
    for r in rows:
        body_lines.append("| " + " | ".join([str(r.get(c, "")) for c in cols]) + " |")
    return header + sep + "\n".join(body_lines) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="out/paper_figures")
    ap.add_argument("--e1", required=True)
    ap.add_argument("--e2", required=True)
    ap.add_argument("--e2p", required=True)
    ap.add_argument("--e3", required=True)
    ap.add_argument("--ctxreport", required=True)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    e1 = load_json(args.e1)
    e2 = load_json(args.e2)
    e2p = load_json(args.e2p)
    e3 = load_json(args.e3)
    ctxr = load_json(args.ctxreport)

    runs = [
        summarize_trace(e1, "E1 (baseline)"),
        summarize_trace(e2, "E2 (base: Add>>Sign)"),
        summarize_trace(e2p, "E2 (perm: Sign>>Add)"),
        summarize_trace(e3, "E3 (seeded jitter)"),
    ]
    cols_runs = ["label", "program_file", "ctx", "N", "deltaT", "rho", "kappa", "obj_seq"]
    write_csv(os.path.join(args.outdir, "table_runs.csv"), runs, cols_runs)
    with open(os.path.join(args.outdir, "table_runs.md"), "w", encoding="utf-8") as f:
        f.write("# Table 1. Run summaries (SemioCore paper demo)\n\n")
        f.write(md_table(runs, cols_runs))

    e2_rows = events_table(e2)
    e2p_rows = events_table(e2p)

    rows_cmp = []
    for a, b in zip(e2_rows, e2p_rows):
        rows_cmp.append({
            "step": a.get("step"),
            "t": a.get("t"),
            "s": a.get("s"),
            "base_ctx": a.get("ctx"),
            "base_r_eff": a.get("r_eff"),
            "base_obj": a.get("obj"),
            "base_kappa_loc": a.get("kappa_loc"),
            "perm_ctx": b.get("ctx"),
            "perm_r_eff": b.get("r_eff"),
            "perm_obj": b.get("obj"),
            "perm_kappa_loc": b.get("kappa_loc"),
        })

    cols_cmp = [
        "step","t","s",
        "base_ctx","base_r_eff","base_obj","base_kappa_loc",
        "perm_ctx","perm_r_eff","perm_obj","perm_kappa_loc"
    ]
    write_csv(os.path.join(args.outdir, "table_e2_events.csv"), rows_cmp, cols_cmp)
    with open(os.path.join(args.outdir, "table_e2_events.md"), "w", encoding="utf-8") as f:
        f.write("# Table 2. Event-level comparison (E2 base vs permuted)\n\n")
        f.write(md_table(rows_cmp, cols_cmp))

    ctx_rows = [{
        "base_ctx": ctxr.get("base_ctx"),
        "permuted_ctx": ctxr.get("permuted_ctx"),
        "obj_hamming": ctxr.get("CtxDiv", {}).get("obj_hamming"),
        "delta_kappa": ctxr.get("CtxDiv", {}).get("delta_kappa"),
        "delta_rho": ctxr.get("CtxDiv", {}).get("delta_rho"),
    }]
    cols_ctx = ["base_ctx", "permuted_ctx", "obj_hamming", "delta_kappa", "delta_rho"]
    write_csv(os.path.join(args.outdir, "table_ctxreport.csv"), ctx_rows, cols_ctx)
    with open(os.path.join(args.outdir, "table_ctxreport.md"), "w", encoding="utf-8") as f:
        f.write("# Table 3. Contextuality diagnostics (CtxDiv)\n\n")
        f.write(md_table(ctx_rows, cols_ctx))

    print("OK: tables written to", args.outdir)

if __name__ == "__main__":
    main()
