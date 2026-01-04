#!/usr/bin/env python3
import argparse
import csv
import glob
import os
from typing import Any, Dict, List

from paper_figures.trace_utils import load_json, summarize_trace, events_table

def write_csv(path: str, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def md_table(rows: List[Dict[str, Any]], cols: List[str]) ->str:
    header = "| " + " | ".join(cols) + " |\n"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |\n"
    body_lines = []
    for r in rows:
        body_lines.append("| " + " | ".join([str(r.get(c, "")) for c in cols]) + " |")
    return header + sep + "\n".join(body_lines) + "\n"
def _collect_paths(glob_pat: str | None, single_path: str) -> List[str]:
    """Return a list of trace paths. If glob_pat is set, it overrides single_path."""
    if glob_pat:
        ps = sorted(glob.glob(glob_pat, recursive=True))
        if not ps:
            raise SystemExit(f"No files matched --glob: {glob_pat}")
        return ps
    return [single_path]

def _seed_tag(path: str, i: int) -> str:
    """
    Best-effort seed label from path. If you store runs as .../seed_003/... it will surface that.
    Otherwise fallback to index.
    """
    p = path.replace("\\", "/")
    for part in p.split("/"):
        if part.startswith("seed_"):
            return part
    return f"seed_{i:03d}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="out/paper_figures")
    ap.add_argument("--e1", required=True)
    ap.add_argument("--e2", required=True, help="Single E2 base trace (ignored if --e2-glob is set)")
    ap.add_argument("--e2p", required=True, help="Single E2 perm trace (ignored if --e2p-glob is set)")
    ap.add_argument("--e2-glob", default=None, help="Glob for multiple E2 base traces (e.g. out/papergrade/runs/**/e2.trace.json)")
    ap.add_argument("--e2p-glob", default=None, help="Glob for multiple E2 perm traces (e.g. out/papergrade/runs/**/e2p.trace.json)")
    ap.add_argument("--pick", type=int, default=0, help="Which run index to use for Table 2 event-level comparison when using globs (default: 0)")
    ap.add_argument("--e3", required=True)
    ap.add_argument("--ctxreport", required=True)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    e1 = load_json(args.e1)
    e2_paths = _collect_paths(args.e2_glob, args.e2)
    e2p_paths = _collect_paths(args.e2p_glob, args.e2p)
    n = min(len(e2_paths), len(e2p_paths))
    e2_paths = e2_paths[:n]
    e2p_paths = e2p_paths[:n]
    if n == 0:
        raise SystemExit("No E2/E2p traces found.")

    pick = max(0, min(args.pick, n - 1))
    e2 = load_json(e2_paths[pick])
    e2p = load_json(e2p_paths[pick])
    e3 = load_json(args.e3)
    ctxr = load_json(args.ctxreport)


    runs = [
        summarize_trace(e1, "E1 (baseline)"),
    ]
    for i in range(n):
        tag = _seed_tag(e2_paths[i], i)
        runs.append(summarize_trace(load_json(e2_paths[i]), f"E2 base ({tag})"))
        runs.append(summarize_trace(load_json(e2p_paths[i]), f"E2 perm ({tag})"))
    runs += [
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

    # --- Table 3 (ctxreport): derive from ctxscan report + base/permuted traces ---
    # ctxscan report schema uses "baseline_ctx"/"permutations"/"witness"; it does not carry CtxDiv fields.
    base_ctx = (ctxr.get("baseline_ctx") or "")
    witness = ctxr.get("witness") or {}
    if isinstance(witness, dict) and witness.get("ctx"):
        permuted_ctx = witness["ctx"]
    else:
        perms = ctxr.get("permutations") or []
        permuted_ctx = (perms[1].get("ctx") if len(perms) > 1 else "") or ""

    tr_base = load_json(args.e2)
    tr_perm = load_json(args.e2p)

    base_objs = [e.get("obj") for e in (tr_base.get("events") or [])]
    perm_objs = [e.get("obj") for e in (tr_perm.get("events") or [])]
    m = min(len(base_objs), len(perm_objs))
    obj_hamming = sum(1 for i in range(m) if base_objs[i] != perm_objs[i]) + abs(len(base_objs) - len(perm_objs))

    bs = tr_base.get("summary") or {}
    ps = tr_perm.get("summary") or {}
    delta_kappa = (float(ps["kappa"]) - float(bs["kappa"])) if ("kappa" in bs and "kappa" in ps) else None
    delta_rho = (float(ps["rho"]) - float(bs["rho"])) if ("rho" in bs and "rho" in ps) else None

    ctx_rows = [{
        "base_ctx": base_ctx,
        "permuted_ctx": permuted_ctx,
        "obj_hamming": obj_hamming,
        "delta_kappa": (None if delta_kappa is None else round(delta_kappa, 3)),
        "delta_rho": (None if delta_rho is None else round(delta_rho, 3)),
    }]
    cols_ctx = ["base_ctx", "permuted_ctx", "obj_hamming", "delta_kappa", "delta_rho"]
    write_csv(os.path.join(args.outdir, "table_ctxreport.csv"), ctx_rows, cols_ctx)
    with open(os.path.join(args.outdir, "table_ctxreport.md"), "w", encoding="utf-8") as f:
        f.write("# Table 3. Contextuality diagnostics (derived)\n\n")
        f.write(md_table(ctx_rows, cols_ctx))

        # New: per-seed deltas (paper-grade). Does not break existing pipeline.
    seed_rows = []
    for i in range(n):
        tr_b = load_json(e2_paths[i])
        tr_p = load_json(e2p_paths[i])
        b_objs = [e.get("obj") for e in (tr_b.get("events") or [])]
        p_objs = [e.get("obj") for e in (tr_p.get("events") or [])]
        m = min(len(b_objs), len(p_objs))
        ham = sum(1 for j in range(m) if b_objs[j] != p_objs[j]) + abs(len(b_objs) - len(p_objs))
        bs2 = tr_b.get("summary") or {}
        ps2 = tr_p.get("summary") or {}
        dk = (float(ps2["kappa"]) - float(bs2["kappa"])) if ("kappa" in bs2 and "kappa" in ps2) else None
        dr = (float(ps2["rho"]) - float(bs2["rho"])) if ("rho" in bs2 and "rho" in ps2) else None
        seed_rows.append({
            "run": _seed_tag(e2_paths[i], i),
            "obj_hamming": ham,
            "delta_kappa": (None if dk is None else round(dk, 3)),
            "delta_rho": (None if dr is None else round(dr, 3)),
        })
    cols_seed = ["run", "obj_hamming", "delta_kappa", "delta_rho"]
    write_csv(os.path.join(args.outdir, "table_ctxreport_seeds.csv"), seed_rows, cols_seed)
    with open(os.path.join(args.outdir, "table_ctxreport_seeds.md"), "w", encoding="utf-8") as f:
        f.write("# Table 3b. Contextuality deltas by seed/run\n\n")
        f.write(md_table(seed_rows, cols_seed))

    print("OK: tables written to", args.outdir)

if __name__ == "__main__":
    main()
