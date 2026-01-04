# semiocore.biomed.qc_regime.v1

## Purpose
**Quality-control regime**. QC flag score (normalized). Positive indicates data acceptable; negative indicates reject.

SemioCore treats this regime as an **interpretive contract** over *pre-computed* biomedical proxy scores.
It does **not** compute CRP/IL-6/NLR/etc. from raw assays; instead it audits the *stability* and *context-sensitivity*
of the decision rule applied to such scores.

## Inputs (channels)
- `chQCFlag`

## Normalization assumption
All channels are assumed to be **normalized proxy scores**:
- Positive values indicate *evidence toward* the target state (risk / disruption / frailty / rejection).
- Negative values indicate *evidence against*.
The concrete mapping from raw biomarkers to these scores is **external** to SemioCore and must be documented by the user.

## Decision rule (SemioCore layer)
This contract is implemented as a `.sc` program plus a fixed context operator chain (e.g., `Add(...) >> Sign`),
yielding a deterministic verdict (`AFFIRM` / `NEGATE`) under the declared regime.

## Scope and limitations
- This contract **does not** diagnose disease, estimate biological age, or infer mechanisms.
- Outputs are only meaningful **relative to the declared contract**, its context, and the input score definitions.
- Clinical or causal claims require independent validation.

