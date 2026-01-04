import os
from dataclasses import replace, is_dataclass
from itertools import permutations
from typing import Any, Dict, List, Optional, Tuple

from semioc.contract_ids import CTXSCAN_SCHEMA_V1
from .sc_parser import parse_program_file
from .world import load_world
from .engine import run_program, write_json, canonical_ctx

def _op_key(op: Any) -> Tuple[str, Optional[float]]:
    # Dedupe/ordering key for ops; keep stable across float formatting noise
    name = getattr(op, "name", str(op))
    arg = getattr(op, "arg", None)
    if isinstance(arg, float):
        arg = round(arg, 12)
    return (str(name), arg if arg is None else float(arg))

def _unique_context_permutations(ops: List[Any]) -> List[List[Any]]:
    """
    Generate unique permutations of ops (dedupe identical ops by (name,arg)).
    Deterministic ordering: sort by canonical ctx string.
    """
    if len(ops) <= 1:
        return [ops[:]]

    # Use tuple of keys to dedupe permutations
    seen = set()
    uniq: List[List[Any]] = []
    for perm in permutations(ops, len(ops)):
        k = tuple(_op_key(o) for o in perm)
        if k in seen:
            continue
        seen.add(k)
        uniq.append(list(perm))

    # Sort permutations by stringified op keys to make output deterministic
    uniq.sort(key=lambda perm: tuple(_op_key(o) for o in perm))
    return uniq

def _replace_context(prog: Any, new_ops: List[Any]) -> Any:
    """
    Program/Context are dataclasses (often frozen). We replace them immutably.
    """
    if not is_dataclass(prog):
        raise TypeError("Program is not a dataclass; cannot replace context safely.")
    ctx = getattr(prog, "context", None)
    if ctx is None or not is_dataclass(ctx):
        raise TypeError("Program.context is missing or not a dataclass; cannot replace context safely.")

    ctx2 = replace(ctx, ops=new_ops)
    prog2 = replace(prog, context=ctx2)
    return prog2

def _signature(trace: Dict[str, Any]) -> List[str]:
    # Outcome signature: sequence of obj values (robust to ctx string changes)
    return [str(ev.get("obj")) for ev in trace.get("events", [])]

def ctxscan(program_file: str,
            world_file: str,
            emit_report: str,
            emit_dir: Optional[str] = None,
            max_perms: Optional[int] = None) -> Dict[str, Any]:
    """
    Context-scan:
      - parse program/world
      - enumerate unique permutations of context ops
      - run each permuted context
      - write per-permutation traces (optional)
      - emit a report JSON with baseline + divergence/witness
    """
    prog = parse_program_file(program_file)
    world = load_world(world_file)

    base_ctx_str = canonical_ctx(prog.context)
    base_ops = list(prog.context.ops)

    perms = _unique_context_permutations(base_ops)

    # Ensure baseline context is first (exact op order as written)
    # If baseline already appears (it will), move it to front.
    def _same_order(p: List[Any], q: List[Any]) -> bool:
        return [_op_key(x) for x in p] == [_op_key(x) for x in q]
    baseline_idx = next((i for i, p in enumerate(perms) if _same_order(p, base_ops)), 0)
    if baseline_idx != 0:
        perms.insert(0, perms.pop(baseline_idx))

    if max_perms is not None:
        perms = perms[: int(max_perms)]

    if emit_dir is not None:
        os.makedirs(emit_dir, exist_ok=True)

    # Run baseline first
    base_prog = _replace_context(prog, perms[0])
    base_trace = run_program(base_prog, world.channels, program_file=program_file)
    base_sig = _signature(base_trace)
    base_summary = base_trace.get("summary", {})

    entries: List[Dict[str, Any]] = []
    witness: Optional[Dict[str, Any]] = None
    kappa_base = float(base_summary.get("kappa", 0.0))

    for i, ops in enumerate(perms):
        p2 = _replace_context(prog, ops)
        tr = run_program(p2, world.channels, program_file=program_file)
        ctx_str = canonical_ctx(p2.context)
        summ = tr.get("summary", {})
        sig = _signature(tr)

        trace_path = None
        if emit_dir is not None:
            trace_path = os.path.join(emit_dir, f"perm_{i:02d}.trace.json")
            write_json(trace_path, tr)

        kappa_i = float(summ.get("kappa", 0.0))
        dk = abs(kappa_i - kappa_base)

        entry = {
            "i": int(i),
            "ctx": ctx_str,
            "summary": summ,
            "dkappa": float(dk),
            "trace_file": trace_path,
        }
        entries.append(entry)

        # First witness where outcome signature differs
        if witness is None and sig != base_sig:
            # Locate first differing step (1-indexed)
            j = 0
            for j in range(min(len(sig), len(base_sig))):
                if sig[j] != base_sig[j]:
                    break
            witness = {
                "perm_i": int(i),
                "ctx": ctx_str,
                "diff_step": int(j + 1),
                "baseline_obj": base_sig[j] if j < len(base_sig) else None,
                "obj": sig[j] if j < len(sig) else None,
            }

    dkappa_max = max((float(e.get("dkappa", 0.0)) for e in entries), default=0.0)
    noncontextual = (witness is None)

    report = {
        "schema": CTXSCAN_SCHEMA_V1,
        "program_file": program_file,
        "world_file": world_file,
        "protocol": "Strict",
        "baseline_ctx": base_ctx_str,
        "baseline_summary": base_summary,
        "noncontextual": bool(noncontextual),
        "dkappa_max": float(dkappa_max),
        "witness": witness,
        "permutations": entries,
    }

    os.makedirs(os.path.dirname(emit_report) or ".", exist_ok=True)
    write_json(emit_report, report)
    return report
