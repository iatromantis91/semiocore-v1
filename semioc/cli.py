import argparse
import os
import sys

from . import VERSION
from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, make_manifest, write_json

_ALLOWED_OPS = {"Add", "Sign", "JitterU"}

def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2

def check_strict(program_file: str) -> int:
    """
    Strict-lite checker:
      - Parses program
      - Validates operator whitelist + arity
      - Validates 'out := summarize;' appears exactly once and is last statement
      - Validates tick dt > 0 (parser already checks, but keep as gate)
      - Validates commits refer to previously sensed vars (parser already checks)
    """
    try:
        prog = parse_program_file(program_file)
    except Exception as e:
        return _fail(str(e))

    # 1) Context operator whitelist + arity
    for op in prog.context.ops:
        if op.name not in _ALLOWED_OPS:
            return _fail(f"Unknown operator '{op.name}' in context. Allowed: {sorted(_ALLOWED_OPS)}")

        if op.name in ("Add", "JitterU"):
            if op.arg is None:
                return _fail(f"Operator '{op.name}' requires a numeric argument, e.g. {op.name}(0.5)")
        if op.name == "Sign":
            if op.arg is not None:
                return _fail("Operator 'Sign' takes no argument; use 'Sign' not 'Sign(x)'")

    # 2) Statement discipline
    out_positions = [i for i, st in enumerate(prog.body) if st.kind == "out_summarize"]
    if len(out_positions) != 1:
        return _fail(f"Program must contain exactly one 'out := summarize;'. Found: {len(out_positions)}")

    if out_positions[0] != len(prog.body) - 1:
        return _fail("'out := summarize;' must be the last statement in the context block (Strict).")

    # 3) Tick dt > 0 (defensive; parser should already ensure)
    for st in prog.body:
        if st.kind == "tick":
            if st.x is None or float(st.x) <= 0.0:
                return _fail("tick dt must be > 0")

    # If we reach here, Strict-lite passes
    print(f"OK: {program_file}")
    return 0

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="semioc", description="SemioCore reference toolchain (v1.0.0)")
    ap.add_argument("--version", action="store_true", help="Print version and exit")

    sub = ap.add_subparsers(dest="cmd", required=False)

    # check (implemented)
    chk = sub.add_parser("check", help="Parse + Strict-lite checks")
    chk.add_argument("--strict", action="store_true", help="Enable Strict gate (recommended)")
    chk.add_argument("program", help="Path to .sc program")

    # run (already implemented)
    runp = sub.add_parser("run", help="Execute a .sc program")
    runp.add_argument("program", help="Path to .sc program")
    runp.add_argument("--world", required=True, help="Path to world JSON (fixtures/world/...)")
    runp.add_argument("--emit-manifest", required=True, help="Output manifest JSON path")
    runp.add_argument("--emit-trace", required=True, help="Output trace JSON path")

    # Stubs (not implemented yet)
    sub.add_parser("opt", help="Optimization + proof emission (v1 stub)")
    sub.add_parser("verify-proof", help="Verify proof file (v1 stub)")
    sub.add_parser("ctxscan", help="Context permutation scan (v1 stub)")
    sub.add_parser("ctxwitness", help="Emit context witness (v1 stub)")
    sub.add_parser("replay", help="Replay run from manifest (v1 stub)")

    args = ap.parse_args(argv)

    if args.version:
        print(VERSION)
        return 0

    if args.cmd is None:
        ap.print_help()
        return 2

    if args.cmd == "check":
        if args.strict:
            return check_strict(args.program)
        # Non-strict: just parse
        try:
            parse_program_file(args.program)
            print(f"OK: {args.program}")
            return 0
        except Exception as e:
            return _fail(str(e))

    if args.cmd != "run":
        print(f"semioc: '{args.cmd}' not implemented yet (v1 scaffold).")
        return 2

    # run
    program_file = args.program
    world_file = args.world

    prog = parse_program_file(program_file)
    world = load_world(world_file)

    trace = run_program(prog, world.channels, program_file=program_file)
    manifest = make_manifest(program_file=program_file, world_file=world_file, seed=prog.seed)

    os.makedirs(os.path.dirname(args.emit_manifest) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.emit_trace) or ".", exist_ok=True)

    write_json(args.emit_manifest, manifest)
    write_json(args.emit_trace, trace)

    return 0
