#!/usr/bin/env python3
import json
from typing import Any, Dict, List, Optional

def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def summarize_trace(trace: Dict[str, Any], label: str) -> Dict[str, Any]:
    summary = trace.get("summary", {})
    events = trace.get("events", [])
    ctx = events[0].get("ctx") if events else None
    obj_seq = "".join(["1" if e.get("obj") == "AFFIRM" else "0" for e in events])
    return {
        "label": label,
        "program_file": trace.get("program_file"),
        "ctx": ctx,
        "N": summary.get("N", len(events)),
        "deltaT": summary.get("deltaT"),
        "rho": summary.get("rho"),
        "kappa": summary.get("kappa"),
        "obj_seq": obj_seq,
    }

def events_table(trace: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for e in trace.get("events", []):
        rows.append({
            "step": e.get("step"),
            "t": e.get("t"),
            "ctx": e.get("ctx"),
            "ch": e.get("ch"),
            "s": e.get("s"),
            "r_raw": e.get("r_raw"),
            "r_eff": e.get("r_eff"),
            "obj": e.get("obj"),
            "expected_obj": e.get("expected_obj"),
            "kappa_loc": e.get("kappa_loc"),
            "noise": e.get("noise", None),
        })
    return rows
