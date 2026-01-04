#!/usr/bin/env python3
import argparse, json, math, sys
from typing import Any, Set

def drop_fields(obj: Any, ignore: Set[str]) -> Any:
    if isinstance(obj, dict):
        return {k: drop_fields(v, ignore) for k, v in obj.items() if k not in ignore}
    if isinstance(obj, list):
        return [drop_fields(x, ignore) for x in obj]
    return obj

def eq(a: Any, b: Any, tol: float) -> bool:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isfinite(a) and math.isfinite(b):
            return abs(a - b) <= tol
        return a == b
    if type(a) != type(b):
        return False
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return False
        return all(eq(a[k], b[k], tol) for k in a.keys())
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(eq(x, y, tol) for x, y in zip(a, b))
    return a == b

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("expected")
    ap.add_argument("actual")
    ap.add_argument("--ignore", default="", help="Comma-separated field names to ignore (everywhere).")
    ap.add_argument("--tol", type=float, default=0.0, help="Float tolerance.")
    args = ap.parse_args()

    ignore = set([s.strip() for s in args.ignore.split(",") if s.strip()])
    with open(args.expected, "r", encoding="utf-8") as f:
        exp = json.load(f)
    with open(args.actual, "r", encoding="utf-8") as f:
        act = json.load(f)

    exp2 = drop_fields(exp, ignore)
    act2 = drop_fields(act, ignore)

    if not eq(exp2, act2, args.tol):
        print("JSON MISMATCH")
        print("Expected:", json.dumps(exp2, indent=2, sort_keys=True))
        print("Actual  :", json.dumps(act2, indent=2, sort_keys=True))
        sys.exit(1)

    print("OK:", args.actual)

if __name__ == "__main__":
    main()
