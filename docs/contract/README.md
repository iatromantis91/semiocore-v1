# SemioCore contracts index

This directory contains the normative contract specifications for SemioCore’s stable JSON artifacts.
Contracts are versioned and treated as compatibility surfaces (SemVer-guided evolution).

## Contracts

| Artifact | Contract ID | Spec (human) | Schema (machine) | Golden fixtures |
|---|---|---|---|---|
| AST | `semiocore.ast.v1` | `ast.v1.md` | `schemas/ast.schema.json` | `expected/ast/*.ast.json` |
| Language manifest | `semiocore.lang.v1` | `lang.v1.md` | `schemas/lang.schema.json` | `expected/lang/*.lang.json` |
| Trace | `semiocore.trace.v1` | `trace.v1.md` | (see `schemas/`) | (see fixtures/expected) |
| Ctxscan report | `semiocore.ctxscan.v1` | `ctxscan.v1.md` | (see `schemas/`) | (see fixtures/expected) |

Notes:
- JSON emission is deterministic: `sort_keys=true`, `ensure_ascii=false`, `indent=2`, trailing newline.
- `program_file` is repository-relative and POSIX-normalized for cross-OS stability.
