# semiocore.ctxscan.v1 — Contract (Normative)

**Status:** Stable (frozen)  
**Schema ID (payload):** `semiocore.ctxscan.v1`  
**JSON Schema (validation):** `schemas/ctxscan.schema.json`

## 1. Scope
This document defines the normative contract for the `semiocore.ctxscan.v1` JSON artifact emitted by the `semioc ctxscan` command.

## 2. Required fields (MUST)
A conforming `semiocore.ctxscan.v1` payload MUST include:

- `schema` (string) — MUST be exactly `semiocore.ctxscan.v1`.

Additional required keys may be specified by the JSON Schema in `schemas/ctxscan.schema.json`.

## 3. Field semantics (Normative)
### 3.1 `schema`
- **Type:** string
- **Constraint:** MUST equal `semiocore.ctxscan.v1`.
- **Meaning:** Declares the payload contract version. Consumers MUST reject or route-to-compat logic any payload whose `schema` differs.

### 3.2 `perms` ordering and determinism (guidance)
The report may include lists of permutations / contexts. Producers SHOULD emit a deterministic ordering where feasible; however, consumers MUST NOT assume list order is semantically meaningful unless the schema explicitly states it.

(Your tests already compute a stable view for cross-platform hashing; keep that discipline for conformance.)

### 3.3 Path-like fields (if present)
Fields such as `trace_file` are informational. Producers MAY emit platform-dependent path separators and runtime-dependent directories. Consumers MUST NOT treat them as stable identifiers.

## 4. Compatibility rules (v1 policy)
`semiocore.ctxscan.v1` is **frozen**:

### 4.1 Allowed (backward compatible) changes within v1
- Adding new OPTIONAL fields.
- Adding new OPTIONAL sections/objects that consumers can ignore.
- Extending the JSON Schema while keeping existing payloads valid.

### 4.2 Disallowed changes (require v2)
Requires `semiocore.ctxscan.v2`:
- Removing or renaming any existing field.
- Changing semantics of existing fields (including interpretation of contexts/perms).
- Tightening constraints such that previously valid v1 payloads become invalid.

## 5. Conformance
A payload conforms to `semiocore.ctxscan.v1` if:
1) `schema == "semiocore.ctxscan.v1"`, and  
2) it validates against `schemas/ctxscan.schema.json`.
