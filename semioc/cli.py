from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .parser import parse_program_to_ast

def _dump(payload: dict) -> str:
    # Determinismo para golden diffs / reproducibilidad
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2) + "\n"

def cmd_parse(args: argparse.Namespace) -> int:
    program_path = Path(args.program)

    # Lee el archivo
    src = program_path.read_text(encoding="utf-8")

    # IMPORTANT: program_file estable y portable (relativo y POSIX)
    program_file = Path(args.program).as_posix()

    ast_obj = parse_program_to_ast(src, program_file=program_file)

    if args.emit_ast:
        Path(args.emit_ast).write_text(_dump(ast_obj), encoding="utf-8")
    else:
        sys.stdout.write(_dump(ast_obj))

    return 0

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="semioc")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("parse", help="Parse a .sc program and emit a stable AST JSON")
    sp.add_argument("program")
    sp.add_argument("--emit-ast", dest="emit_ast")
    sp.set_defaults(fn=cmd_parse)

    return p

def main(argv: list[str] | None = None) -> int:
    p = build_parser()
    args = p.parse_args(argv)
    return int(args.fn(args))
