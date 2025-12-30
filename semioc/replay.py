import json
import os
from typing import Any, Dict, Optional
from dataclasses import replace, is_dataclass

from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, write_json

def _resolve_path(p: str, base_dir: str) -> str:
    if os.path.isabs(p) and os.path.exists(p):
        return p
    if os.path.exists(p):
        return p
    cand = os.path.normpath(os.path.join(base_dir, p))
    if os.path.exists(cand):
        return cand
    return p

def load_manifest(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def replay_from_manifest(manifest_path: str, emit_trace_path: str) -> None:
    mf = load_manifest(manifest_path)

    if mf.get("schema") != "semiocore.manifest.v1":
        raise ValueError(f"Unsupported manifest schema: {mf.get('schema')!r}")

    base_dir = os.path.dirname(os.path.abspath(manifest_path))

    program_file_str = mf.get("program_file")
    world_file_str = mf.get("world_file")
    if not program_file_str or not world_file_str:
        raise ValueError("Manifest must contain 'program_file' and 'world_file'.")

    program_path = _resolve_path(str(program_file_str), base_dir)
    world_path = _resolve_path(str(world_file_str), base_dir)

    seed: Optional[int] = mf.get("seed", None)
    if seed is not None:
        seed = int(seed)

    prog = parse_program_file(program_path)

    # Program is frozen -> use dataclasses.replace to override seed
    if seed is not None:
        if not is_dataclass(prog):
            raise TypeError("Parsed Program is not a dataclass; cannot replace seed safely.")
        prog = replace(prog, seed=seed)

    world = load_world(world_path)

    # Pass literal program_file string from manifest (fixtures expect it).
    trace = run_program(prog, world.channels, program_file=str(program_file_str))

    os.makedirs(os.path.dirname(emit_trace_path) or ".", exist_ok=True)
    write_json(emit_trace_path, trace)
