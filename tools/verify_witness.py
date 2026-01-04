#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_witness(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            # header line (e.g., "SemioCore paper-grade witness selection")
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip()
    return data


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--witness", default="out/papergrade/witness.txt")
    args = ap.parse_args()

    wpath = Path(args.witness)
    if not wpath.exists():
        print(f"ERROR: witness not found: {wpath}", file=sys.stderr)
        return 2

    w = parse_witness(wpath)

    for req in ("perm_trace_src", "e2p_trace", "perm_sha256", "e2p_sha256", "sha_match"):
        if req not in w or not w[req]:
            print(f"ERROR: witness missing required field: {req}", file=sys.stderr)
            return 3

    perm = Path(w["perm_trace_src"])
    e2p = Path(w["e2p_trace"])

    if not perm.exists():
        print(f"ERROR: perm_trace_src missing on disk: {perm}", file=sys.stderr)
        return 4
    if not e2p.exists():
        print(f"ERROR: e2p_trace missing on disk: {e2p}", file=sys.stderr)
        return 5

    perm_sha = sha256_file(perm)
    e2p_sha = sha256_file(e2p)

    ok_perm = (perm_sha == w["perm_sha256"])
    ok_e2p = (e2p_sha == w["e2p_sha256"])
    ok_match = (perm_sha == e2p_sha)
    ok_flag = (w["sha_match"].lower() in ("true", "1", "yes"))

    if not ok_perm:
        print("FAIL: perm_sha256 mismatch", file=sys.stderr)
        print(f"  witness: {w['perm_sha256']}", file=sys.stderr)
        print(f"  real   : {perm_sha}", file=sys.stderr)
        return 10

    if not ok_e2p:
        print("FAIL: e2p_sha256 mismatch", file=sys.stderr)
        print(f"  witness: {w['e2p_sha256']}", file=sys.stderr)
        print(f"  real   : {e2p_sha}", file=sys.stderr)
        return 11

    if not ok_match:
        print("FAIL: content mismatch (perm_trace_src != e2p_trace)", file=sys.stderr)
        print(f"  perm: {perm_sha}", file=sys.stderr)
        print(f"  e2p : {e2p_sha}", file=sys.stderr)
        return 12

    if not ok_flag:
        print("FAIL: witness sha_match flag is not True", file=sys.stderr)
        return 13

    print("OK: witness is content-auditable (sha256 match + recorded hashes correct)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
