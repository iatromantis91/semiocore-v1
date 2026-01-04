import json
from typing import Dict, Any, Optional, Tuple, List

from .model import Program, Context
from .util import sha256_file
from semioc.contract_ids import TRACE_SCHEMA_V1

LCG_A = 1664525
LCG_C = 1013904223
LCG_M = 2**32

def canonical_ctx(ctx: Context) -> str:
    parts = []
    for op in ctx.ops:
        if op.arg is None:
            parts.append(f"{op.name}")
        else:
            parts.append(f"{op.name}({op.arg:g})")
    return ">>".join(parts)

def lcg32_next(state: int) -> int:
    return (LCG_A * (state & 0xFFFFFFFF) + LCG_C) & 0xFFFFFFFF

def lcg32_u01(state: int) -> Tuple[float, int]:
    state2 = lcg32_next(state)
    u = (state2 / LCG_M)
    return u, state2

def _q(x: float) -> float:
    # Quantize to avoid decimal-add binary artefacts (E1)
    return float(round(float(x), 10))

def apply_context(r: float, ctx: Context, rng_state: Optional[int]) -> Tuple[float, Optional[int], Optional[float]]:
    noise_out: Optional[float] = None
    for op in ctx.ops:
        name = op.name
        arg = op.arg
        if name == "Add":
            if arg is None:
                raise ValueError("Add requires an argument.")
            r = r + float(arg)
        elif name == "Sign":
            r = 1.0 if r > 0.0 else -1.0
        elif name == "JitterU":
            if arg is None:
                raise ValueError("JitterU requires an argument.")
            if rng_state is None:
                raise ValueError("JitterU requires a seed (rng_state).")
            eps = float(arg)
            u, rng_state = lcg32_u01(rng_state)
            noise = (2.0 * u - 1.0) * eps
            r = r + noise
            noise_out = noise
        else:
            raise ValueError(f"Unknown operator: {name}")
    return r, rng_state, noise_out

def run_program(program: Program, world_channels: Dict[str, float], *, program_file: str) -> Dict[str, Any]:
    t = 0.0
    bias = 0.0
    rng_state: Optional[int] = (program.seed & 0xFFFFFFFF) if program.seed is not None else None

    ctx_str = canonical_ctx(program.context)
    events: List[Dict[str, Any]] = []

    sensed: Dict[str, Tuple[str, float]] = {}
    step = 0

    for st in program.body:
        k = st.kind
        if k == "tick":
            dt = float(st.x)
            if dt <= 0:
                raise ValueError("tick dt must be > 0")
            t += dt
        elif k == "sense":
            var = st.a
            ch = st.b
            if ch not in world_channels:
                raise KeyError(f"Unknown channel in world: {ch}")
            s = float(world_channels[ch])
            sensed[var] = (ch, s)
        elif k == "do_add_bias":
            bias = float(st.x)
        elif k == "commit":
            var = st.a
            if var not in sensed:
                raise ValueError(f"commit {var} before sensing it")
            ch, s = sensed[var]

            r_raw = s + bias
            r_eff, rng_state, noise = apply_context(r_raw, program.context, rng_state)

            obj = "AFFIRM" if r_eff > 0.0 else "NEGATE"
            expected_obj = "AFFIRM" if s > 0.0 else "NEGATE"
            kappa_loc = 1.0 if obj == expected_obj else 0.0

            step += 1

            # If there is jitter noise, do NOT quantize noise/r_eff (fixtures expect full precision).
            if noise is None:
                ev = {
                    "step": int(step),
                    "t": _q(t),
                    "ctx": ctx_str,
                    "ch": ch,
                    "s": _q(s),
                    "r_raw": _q(r_raw),
                    "r_eff": _q(r_eff),
                    "obj": obj,
                    "expected_obj": expected_obj,
                    "kappa_loc": _q(kappa_loc),
                }
            else:
                ev = {
                    "step": int(step),
                    "t": float(t),
                    "ctx": ctx_str,
                    "ch": ch,
                    "s": float(s),
                    "r_raw": float(r_raw),
                    "noise": float(noise),
                    "r_eff": float(r_eff),
                    "obj": obj,
                    "expected_obj": expected_obj,
                    "kappa_loc": float(kappa_loc),
                }

            events.append(ev)
        elif k == "out_summarize":
            pass
        else:
            raise ValueError(f"Unknown stmt kind: {k}")

    N = len(events)
    if t <= 0.0:
        raise ValueError("Total time (t) must be > 0 to compute rho.")
    rho = (N / t) if N > 0 else 0.0
    kappa = (sum(ev["kappa_loc"] for ev in events) / N) if N > 0 else 0.0

    # Summary: keep quantized for stability (matches E1 fixtures)
    summary = {
        "N": int(N),
        "deltaT": _q(t),
        "rho": _q(rho),
        "kappa": _q(kappa),
    }

    trace = {
        "schema": TRACE_SCHEMA_V1,
        "program_file": program_file,
        "events": events,
        "summary": summary,
    }
    return trace

def make_manifest(program_file: str, world_file: str, seed: Optional[int]) -> Dict[str, Any]:
    prog_hash = sha256_file(program_file)
    world_hash = sha256_file(world_file)

    rng = None
    if seed is not None:
        rng = {
            "type": "LCG32",
            "a": LCG_A,
            "c": LCG_C,
            "m": LCG_M,
            "state0": int(seed) & 0xFFFFFFFF,
        }

    manifest = {
        "schema": "semiocore.manifest.v1",
        "semio_version": "1.0.0",
        "stdlib_version": "1.0.0",
        "program_file": program_file,
        "program_hash_sha256": prog_hash,
        "world_file": world_file,
        "world_hash_sha256": world_hash,
        "protocol": "Strict",
        "seed": seed,
        "rng": rng,
        "run_id": f"run-{prog_hash[:8]}",
        "timestamp": "1970-01-01T00:00:00+00:00",
    }
    return manifest

def write_json(path: str, obj: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")
