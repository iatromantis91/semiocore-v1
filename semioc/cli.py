import argparse
import os
from . import VERSION
from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, make_manifest, write_json

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="semioc", description="SemioCore reference toolchain (v1.0.0)")
    ap.add_argument("--version", action="store_true", help="Print version and exit")

    sub = ap.add_subparsers(dest="cmd", required=False)

    runp = sub.add_parser("run", help="Execute a .sc program (v1: run only)")
    runp.add_argument("program", help="Path to .sc program")
    runp.add_argument("--world", required=True, help="Path to world JSON (fixtures/world/...)")
    runp.add_argument("--emit-manifest", required=True, help="Output manifest JSON path")
    runp.add_argument("--emit-trace", required=True, help="Output trace JSON path")

    sub.add_parser("check", help="Parse + Strict-lite checks (v1 stub)")
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

    if args.cmd != "run":
        print(f"semioc: '{args.cmd}' not implemented yet (v1 scaffold).")
        return 2

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
