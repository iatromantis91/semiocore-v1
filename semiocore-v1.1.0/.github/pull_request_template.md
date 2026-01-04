\# Summary



<!-- What does this PR change? Keep it short and concrete. -->



\## Motivation / Context



<!-- Why is this change needed? Link issues if applicable. -->



\## Type of change (check all that apply)



\- \[ ] Bug fix (no contract/output changes)

\- \[ ] Internal refactor (no contract/output changes)

\- \[ ] Documentation-only change

\- \[ ] Tests-only change

\- \[ ] Contract change (schema/fixtures/docs affected)

\- \[ ] CLI/tooling change (may affect emitted artifacts)

\- \[ ] New contract added



---



\# Contract Discipline (Required)



\## Contracts affected

<!-- List contract IDs, e.g. semiocore.ast.v1, semiocore.lang.v1, semiocore.plasticity.v1 -->

\- Contract IDs:

&nbsp; - \[ ] `semiocore.ast.v1`

&nbsp; - \[ ] `semiocore.lang.v1`

&nbsp; - \[ ] `semiocore.trace.v1`

&nbsp; - \[ ] `semiocore.ctxscan.v1`

&nbsp; - \[ ] `semiocore.plasticity.v1`

&nbsp; - \[ ] Other: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_



\## Does this PR change any contract output?

\- \[ ] No (outputs unchanged; fixtures remain valid)

\- \[ ] Yes (outputs change intentionally)



If \*\*Yes\*\*, provide rationale (required):

<!-- Explain what changed in the emitted artifacts and why it is correct. -->



---



\# Required Checks (must be run locally)



Paste command output or confirm you ran them.



\## Registry / Schemas / Fixtures

\- \[ ] `python -m semioc contracts validate`  ✅

&nbsp; - Output: `OK` (required)



\## Tests

\- \[ ] `pytest -q` ✅



\## Determinism / Reproducibility (if outputs are affected)

\- \[ ] `python -m semioc parse ... --emit-ast --emit-lang` produces \*\*deterministic JSON\*\*

\- \[ ] No volatile fields added (timestamps, hostnames, random IDs)

\- \[ ] JSON ordering is stable / canonical



---



\# Artifacts Updated (Required if outputs change)



Check all that apply:



\## Schemas

\- \[ ] Updated `schemas/\*.schema.json`

\- \[ ] Schema `$id` matches `contract\_id`

\- \[ ] Schema remains Draft 2020-12 valid



\## Golden Fixtures

\- \[ ] Updated `expected/\*`

\- \[ ] Fixture JSON is valid

\- \[ ] Fixture `schema` field matches the contract ID

\- \[ ] Fixture validates against its schema (via `contracts validate`)



\## Documentation

\- \[ ] Updated `docs/contract/\*.md`

\- \[ ] Updated `docs/contract/README.md` index (if a contract was added)



---



\# Versioning / Compatibility



\- \[ ] No breaking changes to `v1` contracts

\- \[ ] If breaking change is required, a `v2` contract is proposed (issue/PR includes migration notes)



Breaking change definition (any of):

\- removing/renaming required fields

\- changing semantics of existing fields

\- changing output shape in a way that breaks downstream consumers



---



\# Non-Goals Check (must remain true)



This PR does \*\*NOT\*\*:

\- \[ ] Add statistical modeling, p-values, regressions, ML, embeddings, predictive optimization

\- \[ ] Add clinical claims (biological age estimation, diagnosis, medical risk classification)

\- \[ ] Hardcode biomarker primitives into the core

\- \[ ] Introduce implicit heuristics/"smart defaults" without contract-level specification

\- \[ ] Add dashboards/GUI as core features



If any box cannot be checked, this PR is out of scope and should be redesigned.



---



\# Notes for Reviewers



<!-- Anything reviewers should pay attention to: contract diffs, tricky edge cases, migration concerns -->



