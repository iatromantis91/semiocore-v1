import re
from typing import Optional, List, Tuple
from .model import Program, Context, Op, Stmt

_RE_SEED = re.compile(r"^\s*seed\s+(\d+)\s*;?\s*$", re.IGNORECASE)
_RE_CONTEXT_OPEN = re.compile(r"^\s*context\s+(.+?)\s*\{\s*$", re.IGNORECASE)
_RE_CONTEXT_CLOSE = re.compile(r"^\s*\}\s*$")
_RE_TICK = re.compile(r"^\s*tick\s+([0-9]*\.?[0-9]+)\s*;?\s*$", re.IGNORECASE)
_RE_SENSE = re.compile(r"^\s*([A-Za-z_]\w*)\s*:=\s*sense\s+([A-Za-z_]\w*)\s*;?\s*$", re.IGNORECASE)
_RE_COMMIT = re.compile(r"^\s*commit\s+([A-Za-z_]\w*)\s*;?\s*$", re.IGNORECASE)
_RE_DO_BIAS = re.compile(r"^\s*do\s+add_bias\(\s*([+-]?[0-9]*\.?[0-9]+)\s*\)\s*;?\s*$", re.IGNORECASE)
_RE_OUT_SUM = re.compile(r"^\s*out\s*:=\s*summarize\s*;?\s*$", re.IGNORECASE)

_RE_OP = re.compile(r"^\s*([A-Za-z_]\w*)\s*(?:\(\s*([+-]?[0-9]*\.?[0-9]+)\s*\))?\s*$")

def _strip_comment(line: str) -> str:
    # Remove everything after '#'
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()

def _parse_ops(ctx_spec: str) -> Context:
    parts = [p.strip() for p in ctx_spec.split(">>") if p.strip()]
    ops: List[Op] = []
    for p in parts:
        m = _RE_OP.match(p)
        if not m:
            raise ValueError(f"Invalid operator in context: '{p}'")
        name = m.group(1)
        arg_s = m.group(2)
        arg = float(arg_s) if arg_s is not None else None
        ops.append(Op(name=name, arg=arg))
    if not ops:
        raise ValueError("Context must contain at least one operator.")
    return Context(ops=ops)

def parse_program(text: str, path: str = "<memory>") -> Program:
    seed: Optional[int] = None
    context: Optional[Context] = None
    body: List[Stmt] = []

    lines = text.splitlines()
    i = 0
    in_ctx = False

    while i < len(lines):
        raw = lines[i]
        line = _strip_comment(raw)
        i += 1
        if not line:
            continue

        # Seed (top-level)
        m = _RE_SEED.match(line)
        if m and not in_ctx:
            seed = int(m.group(1))
            continue

        # Context open
        m = _RE_CONTEXT_OPEN.match(line)
        if m and not in_ctx:
            ctx_spec = m.group(1)
            context = _parse_ops(ctx_spec)
            in_ctx = True
            continue

        # Context close
        if _RE_CONTEXT_CLOSE.match(line) and in_ctx:
            in_ctx = False
            continue

        if not in_ctx:
            # Allow trailing 'out := summarize;' outside block? (v1: require inside)
            if _RE_OUT_SUM.match(line):
                body.append(Stmt(kind="out_summarize"))
                continue
            raise ValueError(f"Unexpected top-level line (outside context) at {path}:{i}: {line}")

        # Inside context block: statements
        m = _RE_TICK.match(line)
        if m:
            body.append(Stmt(kind="tick", x=float(m.group(1))))
            continue

        m = _RE_SENSE.match(line)
        if m:
            var = m.group(1)
            ch = m.group(2)
            body.append(Stmt(kind="sense", a=var, b=ch))
            continue

        m = _RE_COMMIT.match(line)
        if m:
            body.append(Stmt(kind="commit", a=m.group(1)))
            continue

        m = _RE_DO_BIAS.match(line)
        if m:
            body.append(Stmt(kind="do_add_bias", x=float(m.group(1))))
            continue

        if _RE_OUT_SUM.match(line):
            body.append(Stmt(kind="out_summarize"))
            continue

        raise ValueError(f"Unrecognized statement at {path}:{i}: {line}")

    if in_ctx:
        raise ValueError(f"Unclosed context block in {path}")

    if context is None:
        raise ValueError(f"Missing 'context ... {{ ... }}' block in {path}")

    # Minimal Strict-lite: must contain out summarize
    if not any(st.kind == "out_summarize" for st in body):
        raise ValueError(f"Missing 'out := summarize;' in {path}")

    # Minimal Strict-lite: each commit must refer to a var that has been sensed earlier
    sensed = set()
    for st in body:
        if st.kind == "sense":
            sensed.add(st.a)
        if st.kind == "commit":
            if st.a not in sensed:
                raise ValueError(f"commit {st.a} before sensing it in {path}")

    return Program(seed=seed, context=context, body=body)

def parse_program_file(path: str) -> Program:
    with open(path, "r", encoding="utf-8") as f:
        return parse_program(f.read(), path=path)
