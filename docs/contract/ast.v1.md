# semiocore.ast.v1 — AST Contract (v1)

## Purpose
This contract defines the stable, machine-checkable JSON shape of the canonical AST emitted by SemioCore. It is designed for deterministic parsing, golden conformance testing, and SemVer-compatible evolution.

## Contract ID
- `semiocore.ast.v1`

## Related Contracts
- Language manifest contract: `semiocore.lang.v1`

## Artifact: AST (JSON)
An AST artifact MUST be a JSON object with at least the required fields below.

### Required fields
- `schema` (string, const): `semiocore.ast.v1`
- `program_file` (string): Repository-relative POSIX path to the `.sc` source (portable, stable)
- `ast` (object): The AST root node

### AST minimal shape (v1)
- `ast.node` (string, const): `"Program"`
- `ast.body` (array): Sequence of statement nodes (may be empty)

Implementations MAY extend `ast` nodes with additional properties, provided the required minimal structure remains valid.

## Determinism requirements
- Emitted JSON MUST be deterministic for reproducibility and golden tests.
- Keys SHOULD be sorted and output SHOULD end with a newline when serialized.

## Machine schema
- JSON Schema: `schemas/ast.schema.json`
- `$id` MUST equal `semiocore.ast.v1`
- `properties.schema.const` MUST equal `semiocore.ast.v1`

## Example
A minimal valid AST artifact (body empty):

```json
{
  "schema": "semiocore.ast.v1",
  "program_file": "programs/conformance/basic.sc",
  "ast": {
    "node": "Program",
    "body": []
  }
}

