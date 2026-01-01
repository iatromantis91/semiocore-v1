# semiocore.trace.v1 — Contract (Normative)

**Status:** Stable (frozen)  
**Schema ID (payload):** `semiocore.trace.v1`  
**JSON Schema (validation):** `schemas/trace.schema.json`

## 1. Scope
This document defines the normative contract for the `semiocore.trace.v1` JSON artifact emitted by the `semioc run` command. Any producer/consumer claiming conformance to `semiocore.trace.v1` MUST follow this contract.

## 2. Required fields (MUST)
A conforming `semiocore.trace.v1` payload MUST include:

- `schema` (string) — MUST be exactly `semiocore.trace.v1`.

Additional required keys may be specified by the JSON Schema in `schemas/trace.schema.json`. When in doubt, the JSON Schema is the machine-checkable contract, and this document is the human-readable normative description.

## 3. Field semantics (Normative)
### 3.1 `schema`
- **Type:** string
- **Constraint:** MUST equal `semiocore.trace.v1`.
- **Meaning:** Declares the payload contract version. Consumers MUST reject or route-to-compat logic any payload whose `schema` differs.

### 3.2 Path-like fields (if present)
Any field whose name ends in `_file` (e.g., `program_file`) is informational metadata. Producers MAY emit absolute or relative paths depending on runtime environment. Consumers MUST NOT interpret these paths as stable identifiers.

(If you later want stronger guarantees, introduce a separate stable identifier field; do not strengthen `_file` semantics inside v1.)

## 4. Compatibility rules (v1 policy)
`semiocore.trace.v1` is **frozen** under Semantic Versioning discipline:

### 4.1 Allowed (backward compatible) changes within v1
- Adding new OPTIONAL fields.
- Adding new OPTIONAL enum members or cases, if and only if consumers can safely ignore unknown values.
- Extending the JSON Schema while keeping existing payloads valid.

### 4.2 Disallowed changes (require v2)
Any of the following requires a new contract version `semiocore.trace.v2`:
- Removing or renaming any existing field.
- Changing the meaning/semantics of any existing field.
- Tightening constraints such that previously valid v1 payloads become invalid.
- Changing numeric units, normalization, rounding conventions, event ordering semantics, etc., in a way that affects interpretation.

## 5. Conformance
A payload conforms to `semiocore.trace.v1` if:
1) `schema == "semiocore.trace.v1"`, and  
2) it validates against `schemas/trace.schema.json`.

## 6. Notes
This contract is intentionally permissive about extensions. For forward extensibility without breaking v1, prefer either:
- namespaced extension keys (e.g., `x_*`), or
- an `extensions` object.

Do not overload existing fields to carry new semantics.
