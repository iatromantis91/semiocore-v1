# semiocore.ast.v1 — Canonical AST Contract (v1)

## Purpose
Defines a stable JSON AST envelope produced by SemioCore tooling. This contract is intentionally minimal: it stabilizes the envelope and top-level structure while allowing extension within nodes.

## Contract ID
- `semiocore.ast.v1`

## Artifact: AST (JSON)
An AST artifact MUST be a JSON object.

### Required fields
- `schema` (string, const): `semiocore.ast.v1`
- `program_file` (string): Source program path/identifier (repo-relative POSIX recommended)
- `ast` (object):
  - `node` (string, const): `"Program"`
  - `body` (array[object]): Statement nodes (may be empty)

## Extensibility
- Additional keys MAY appear at any level (`additionalProperties: true`).
- Consumers MUST ignore unknown fields to remain forward compatible.

## Determinism & Portability
- JSON emission SHOULD be deterministic (sorted keys, stable indentation, final newline).
- `program_file` SHOULD be repo-relative POSIX to support golden conformance tests across OSes.
