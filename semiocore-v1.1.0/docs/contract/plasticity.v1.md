# semiocore.plasticity.v1

## Purpose

`semiocore.plasticity.v1` specifies the JSON shape for a **plasticity report** computed from one or more `semiocore.trace.v1` traces under a fixed `(ctx, channel)` regime. The report is intended to be **deterministic, auditable, and replayable**.

This contract is bioinformatics/biomedicine-oriented: it treats semiosis operationally as *interpretation under an explicit regime* and quantifies *interpretive stability* over traces and time windows.

## Artifact

- Schema: `schemas/plasticity.schema.json`
- Golden fixture: `expected/plasticity/basic.plasticity.json`

## Contract ID

- `schema` MUST be exactly: `semiocore.plasticity.v1`

## Inputs

The report is computed from:
- A set of trace files conforming to `semiocore.trace.v1`
- A selected context string `ctx` (matched against `trace.events[].ctx`)
- A selected channel `channel` (matched against `trace.events[].ch`)
- Windowing parameters (`window_size`, `window_step`) interpreted as **event-count windows**

## Determinism

Implementations MUST:
- Avoid volatile fields (timestamps, hostnames, random IDs) in the report payload
- Preserve deterministic ordering where relevant (e.g., `evidence.trace_digests` order matches the input trace order)
- Compute digests over raw trace bytes using SHA-256

## Top-level fields

### `program_file` (string)

Provenance path for the program that generated the traces or the analysis context. Implementations MAY set this to:
- a user-provided path, or
- a value derived from the first trace (if present), or
- a stable placeholder

### `protocol` (string)

A label for the evaluation protocol. Recommended: `"Strict"`.

### `ctx` (string)

The context selector. This MUST match the context string used in the trace events being analyzed (exact string match).

### `channel` (string)

The channel selector. This MUST match the channel name used in the trace events being analyzed (exact string match).

### `windowing` (object)

Window configuration. Minimum fields:
- `mode`: `"fixed"`
- `size`: integer (event count)
- `step`: integer (event count)

### `metrics` (object)

Numerical metrics computed deterministically. Current v1 set:
- `partition_stability`: [0, 1]
- `noise_sensitivity`: >= 0
- `indeterminacy_rate`: [0, 1]
- `coherence_loss`: >= 0

### `verdict` (object)

Deterministic qualitative summary:
- `plasticity_state`: `"stable" | "fragile" | "degraded"`
- `trend`: `"stable" | "declining" | "improving"`
- `confidence`: [0, 1]
- `reasons`: array of strings (machine- and human-readable flags)

### `evidence` (object)

Machine-auditable evidence bundle:
- `N_traces`: integer
- `N_events`: integer (after filtering by `(ctx, channel)`)
- `trace_digests`: array of `{path, sha256}` objects in input order

## Metric definitions

These definitions are intended to be implementable without machine learning, and to be auditable via traces.

### `partition_stability`

Measures how consistently a categorical output stays within the dominant partition per window.

Operational definition (recommended):
- Extract an event label `obj` for each event in `(ctx, channel)`
- For each window, compute the mode label
- Report the fraction of events equal to their window’s mode label

### `noise_sensitivity`

Measures how frequently the categorical label changes per unit of signal variation.

Operational definition (recommended):
- For adjacent events, compute:
  - `ΔP = 1` if `obj` changes, else `0`
  - `|Δs|` from an event scalar field (e.g., `s` or `r_raw`) if present
- `noise_sensitivity = ΣΔP / (Σ|Δs| + ε)`

### `indeterminacy_rate`

Measures the frequency of indeterminate interpretations.

Operational definition (recommended):
- Count events whose `obj` is a designated indeterminate token (e.g., `UNKNOWN`, `UNDETERMINED`)
- Divide by total events in `(ctx, channel)`

### `coherence_loss`

Measures loss of internal coherence via dispersion of an internal parameter.

Operational definition (recommended):
- If present, use `kappa_loc` from events
- Compute variance over `kappa_loc` in `(ctx, channel)`

## Versioning rules

- v1 is **stable**: breaking changes require `semiocore.plasticity.v2`
- Additive compatible extensions (optional fields, new metrics) may be introduced without breaking v1 if schema remains compatible

## Notes

- This contract deliberately focuses on **regimes of interpretation** rather than raw signals.
- The authoritative definition is the JSON Schema plus the golden fixtures.

