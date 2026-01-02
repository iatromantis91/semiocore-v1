# Contracts index

This directory contains the normative, human-readable specifications for SemioCore’s stable JSON contracts, alongside their machine-checkable JSON Schemas and golden fixtures.

| Contract ID | Schema file | Spec doc | Golden fixtures |
|---|---|---|---|
| `semiocore.trace.v1` | `schemas/trace.schema.json` | `docs/contract/trace.v1.md` | `expected/**` (trace fixtures, if present) |
| `semiocore.ctxscan.v1` | `schemas/ctxscan.schema.json` | `docs/contract/ctxscan.v1.md` | `expected/**` (ctxscan fixtures, if present) |
| `semiocore.ast.v1` | `schemas/ast.schema.json` | `docs/contract/ast.v1.md` | `expected/ast/*.ast.json` |
| `semiocore.lang.v1` | `schemas/lang.schema.json` | `docs/contract/lang.v1.md` | `expected/lang/*.lang.json` |

## Notes
- Golden fixtures provide strong, deterministic conformance checks.
- JSON Schemas provide portable, machine-verifiable contract validation.
