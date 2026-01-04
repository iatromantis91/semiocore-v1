from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class Op:
    name: str
    arg: Optional[float] = None

@dataclass(frozen=True)
class Context:
    ops: List[Op]

@dataclass(frozen=True)
class Stmt:
    kind: str
    a: Optional[str] = None
    b: Optional[str] = None
    x: Optional[float] = None

@dataclass(frozen=True)
class Program:
    seed: Optional[int]
    context: Context
    body: List[Stmt]
