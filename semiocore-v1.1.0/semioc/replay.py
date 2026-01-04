import json
from dataclasses import replace
from typing import Any, Dict

from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, write_json

NOTE_REPLAY = "Replay output must match e3.trace.json exactly under fixed seed and LCG32 spec."

def replay_from_manifest(manifest_path: str, emit_trace_path: str) -> Dict[str, Any]:
    with open(manifest_path, "r", encoding="utf-8") as f:
        mf = json.load(f)

    program_file = mf.get("program_file")
    if not program_file:
        raise ValueError("manifest missing 'program_file'")

    world_file = mf.get("world_file") or mf.get("world")
    if not world_file:
        raise ValueError("manifest missing 'world_file' (or 'world')")

    prog = parse_program_file(program_file)

    seed = mf.get("seed")
    if seed is not None:
        prog = replace(prog, seed=int(seed))

    world = load_world(world_file)

    # IMPORTANT: engine.run_program now requires program_file as a keyword-only arg
    trace = run_program(prog, world.channels, program_file=program_file)

    # Fixture requires this explanatory field in replay output.
    trace["note"] = NOTE_REPLAY

    write_json(emit_trace_path, trace)
    return trace
