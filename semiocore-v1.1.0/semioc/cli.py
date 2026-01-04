import argparse
import json
import os
import sys

from pathlib import Path
from . import VERSION
from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, make_manifest, write_json
from .replay import replay_from_manifest
from .ctxscan import ctxscan
from .parser import parse_program_to_ast
from .plasticity import compute_plasticity_report
from .contract_ids import LANG_SCHEMA_V1, AST_SCHEMA_V1

_ALLOWED_OPS = {"Add", "Sign", "JitterU"}

def cmd_parse(args: argparse.Namespace) -> int:
    program_path = Path(args.program)

    # Lee fuente
    src = program_path.read_text(encoding="utf-8")

    # program_file estable y portable:
    # - si el archivo está bajo el cwd, usa ruta relativa POSIX
    # - si no, usa la ruta tal cual en POSIX
    try:
        program_file = program_path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except Exception:
        program_file = program_path.as_posix()
   
    lang_obj = _make_lang_manifest(program_file)
    ast_obj = parse_program_to_ast(src, program_file=program_file)

    if args.emit_lang:
        Path(args.emit_lang).write_text(_dump_json(lang_obj), encoding="utf-8")

    if args.emit_ast:
        Path(args.emit_ast).write_text(_dump_json(ast_obj), encoding="utf-8")
    else:
        sys.stdout.write(_dump_json(ast_obj))

    return 0

def _dump_json(payload: dict) -> str:
    # JSON determinista para diffs/golden tests y reproducibilidad
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"

def _make_lang_manifest(program_file: str) -> dict:
    # Manifest v1: estable, extensible
    return {
        "schema": LANG_SCHEMA_V1,
        "program_file": program_file,
        "lang_version": "1",
        "features": [],
        "ast_schema": AST_SCHEMA_V1,
        # opcional: vacío por ahora; mantenemos el campo fuera si no se usa
        # "diagnostics": [],
    }

def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 2

def check_strict(program_file: str) -> int:
    try:
        prog = parse_program_file(program_file)
    except Exception as e:
        return _fail(str(e))

    for op in prog.context.ops:
        if op.name not in _ALLOWED_OPS:
            return _fail(f"Unknown operator '{op.name}' in context. Allowed: {sorted(_ALLOWED_OPS)}")

        if op.name in ("Add", "JitterU") and op.arg is None:
            return _fail(f"Operator '{op.name}' requires a numeric argument, e.g. {op.name}(0.5)")

        if op.name == "Sign" and op.arg is not None:
            return _fail("Operator 'Sign' takes no argument; use 'Sign' not 'Sign(x)'")

    out_positions = [i for i, st in enumerate(prog.body) if st.kind == "out_summarize"]
    if len(out_positions) != 1:
        return _fail(f"Program must contain exactly one 'out := summarize;'. Found: {len(out_positions)}")
    if out_positions[0] != len(prog.body) - 1:
        return _fail("'out := summarize;' must be the last statement in the context block (Strict).")

    for st in prog.body:
        if st.kind == "tick" and (st.x is None or float(st.x) <= 0.0):
            return _fail("tick dt must be > 0")

    print(f"OK: {program_file}")
    return 0

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="semioc", description=f"SemioCore reference toolchain (v{VERSION})")
    ap.add_argument("--version", action="store_true", help="Print version and exit")
    sub = ap.add_subparsers(dest="cmd", required=False)

    # check
    chk = sub.add_parser("check", help="Parse + Strict-lite checks")
    chk.add_argument("--strict", action="store_true", help="Enable Strict gate")
    chk.add_argument("program", help="Path to .sc program")

    # run
    runp = sub.add_parser("run", help="Execute a .sc program")
    runp.add_argument("program", help="Path to .sc program")
    runp.add_argument("--world", required=True, help="Path to world JSON (fixtures/world/...)")
    runp.add_argument("--emit-manifest", required=True, help="Output manifest JSON path")
    runp.add_argument("--emit-trace", required=True, help="Output trace JSON path")

    # replay
    rpl = sub.add_parser("replay", help="Replay deterministically from a manifest")
    rpl.add_argument("--manifest", required=True, help="Path to manifest JSON")
    rpl.add_argument("--emit-trace", required=True, help="Output trace JSON path")

    # ctxscan (NEW)
    cxs = sub.add_parser("ctxscan", help="Scan context permutations and report contextuality witness")
    cxs.add_argument("program", help="Path to .sc program")
    cxs.add_argument("--world", required=True, help="Path to world JSON")
    cxs.add_argument("--emit-report", required=True, help="Output ctxscan report JSON path")
    cxs.add_argument("--emit-dir", default=None, help="Optional directory to write per-permutation traces")
    cxs.add_argument("--max-perms", default=None, help="Optional cap on number of permutations")
    # parse (NEW)
    prs = sub.add_parser("parse", help="Parse a .sc program and emit a stable AST JSON")
    prs.add_argument("program", help="Path to the .sc program file")
    prs.add_argument("--emit-ast", dest="emit_ast", help="Write AST JSON to this file (default: stdout)")
    prs.add_argument("--emit-lang", dest="emit_lang", help="Write language manifest JSON to this file (default: no manifest)")


    # plasticity (NEW)
    plc = sub.add_parser("plasticity", help="Compute a semiodynamic plasticity report from trace files")
    plc.add_argument("--traces", nargs="+", required=True, help="One or more trace JSON files (semiocore.trace.v1)")
    plc.add_argument("--ctx", required=True, help="Context ID to analyze (must match trace.events[].ctx)")
    plc.add_argument("--channel", required=True, help="Channel to analyze (must match trace.events[].ch)")
    plc.add_argument("--protocol", default="Strict", help="Protocol label for the report (default: Strict)")
    plc.add_argument("--window-size", type=int, default=10, help="Event window size for stability metrics")
    plc.add_argument("--window-step", type=int, default=10, help="Event window step for stability metrics")
    plc.add_argument("--program-file", default=None, help="Optional program file path to embed in the report")
    plc.add_argument("--emit-report", required=True, help="Output plasticity report JSON path")
    args = ap.parse_args(argv)

    if args.version:
        print(VERSION)
        return 0

    if args.cmd is None:
        ap.print_help()
        return 2

    if args.cmd == "parse":
        try:
            return cmd_parse(args)
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "check":
        if args.strict:
            return check_strict(args.program)
        try:
            parse_program_file(args.program)
            print(f"OK: {args.program}")
            return 0
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "replay":
        try:
            replay_from_manifest(args.manifest, args.emit_trace)
            print(f"OK: {args.emit_trace}")
            return 0
        except Exception as e:
            return _fail(str(e))

    if args.cmd == "ctxscan":
        try:
            maxp = int(args.max_perms) if args.max_perms is not None else None
            ctxscan(args.program, args.world, args.emit_report, emit_dir=args.emit_dir, max_perms=maxp)
            print(f"OK: {args.emit_report}")
            return 0
        except Exception as e:
            return _fail(str(e))


    if args.cmd == "plasticity":
        try:
            trace_paths = [Path(p) for p in args.traces]
            report = compute_plasticity_report(
                trace_paths,
                ctx=args.ctx,
                channel=args.channel,
                protocol=args.protocol,
                window_size=int(args.window_size),
                window_step=int(args.window_step),
                program_file=args.program_file,
            )
            os.makedirs(os.path.dirname(args.emit_report) or ".", exist_ok=True)
            Path(args.emit_report).write_text(_dump_json(report), encoding="utf-8")
            print(f"OK: {args.emit_report}")
            return 0
        except Exception as e:
            return _fail(str(e))

    if args.cmd != "run":
        print(f"semioc: '{args.cmd}' not implemented yet (v1).")
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
