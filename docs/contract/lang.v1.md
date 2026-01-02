# semiocore.lang.v1 — Language Manifest Contract (v1)

## Purpose
This contract defines a stable, machine-checkable manifest that declares which language version and features a given `.sc` program uses, and which AST contract it targets. It is designed to support reproducible parsing, conformance testing, and SemVer-compatible evolution.

## Contract ID
- `semiocore.lang.v1`

## Related Contracts
- AST contract: `semiocore.ast.v1`

## Artifact: Language Manifest (JSON)
A manifest MUST be a JSON object with at least the required fields below.

### Required fields
- `schema` (string, const): `semiocore.lang.v1`
- `program_file` (string): Path or identifier of the source program
- `lang_version` (string, const): `"1"`
- `features` (array of strings): Declared feature flags (may be empty)
- `ast_schema` (string, const): `semiocore.ast.v1`

### Optional fields
- `diagnostics` (array): Tooling diagnostics (warnings/info/errors). Intended for reporting, not for control flow.

## Canonical JSON Serialization
Tooling SHOULD emit canonical JSON to support golden tests and stable diffs:
- UTF-8 encoding
- Indentation: 2 spaces
- Newline at EOF
- No ASCII-escaping (`ensure_ascii=false` in Python)

## Compatibility Rules
- The contract ID `semiocore.lang.v1` is stable.
- Adding new optional fields is backward compatible.
- Changing meanings of existing required fields is breaking and requires a new major contract (e.g., `semiocore.lang.v2`).

## CLI Conformance (target)
Tooling SHOULD support emitting this manifest alongside the AST:
- `semioc parse <program.sc> --emit-lang out.lang.json`
