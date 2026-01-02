# semiocore.ast.v1 — AST Contract (v1)

## Purpose
Defines the stable, machine-checkable JSON shape of the canonical AST emitted by SemioCore, intended for deterministic parsing and golden conformance testing.

## Contract ID
- `semiocore.ast.v1`

## Artifact: AST (JSON)
An AST artifact MUST be a JSON object with the required fields below.

### Required fields
- `schema` (string, const): `semiocore.ast.v1`
- `program_file` (string): repository-relative POSIX path to the `.sc` source
- `ast` (object): AST root node

### Minimal AST shape (v1)
- `ast.node` (string, const): `"Program"`
- `ast.body` (array): sequence of statement nodes (may be empty)

Implementations MAY extend AST nodes with additional properties as long as the required minimal structure remains valid.

## Determinism
Serializations MUST be deterministic (stable key ordering and whitespace policy are implementation-defined, but golden fixtures assume deterministic output).
