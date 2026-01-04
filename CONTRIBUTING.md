# Contributing to SemioCore

Thank you for considering a contribution to SemioCore.

SemioCore is a domain-specific, declarative language and toolchain for **machine-verifiable regimes of biomedical interpretation and decision**. Contributions are welcome, but the project is governed by strict constraints to preserve determinism, auditability, and contract stability.

Before contributing, please read: [MANIFESTO.md](MANIFESTO.md).

---

## 1. Scope and Non-Goals

SemioCore is **not**:
- a statistics platform (no regressions, p-values, modeling toolkits)
- an ML framework (no embeddings, neural nets, predictive optimization)
- a clinical diagnostic tool (no biological age, disease diagnosis, risk scoring)
- a GUI/dashboard project
- a biomarker library (no hardcoded biomarker primitives)

If your contribution moves SemioCore toward these areas, it will be rejected.

**Rule of thumb:** if it can be done better in R/Python/Stan/ML, SemioCore should not do it.

---

## 2. Core Principles (What We Protect)

All accepted contributions must preserve:

1) **Explicitness:** If a rule is not in a contract, it does not exist.  
2) **Determinism:** Same inputs + same contracts → identical artifacts.  
3) **Machine-verifiable contracts:** versioned IDs, JSON Schema validation, docs, and fixtures.  
4) **Replayability:** regimes must be re-applicable and comparable over time and traces.  
5) **Separation of concerns:** signals (biomarkers) are inputs; SemioCore formalizes interpretation regimes; semiodynamics is the measured dynamic.

---

## 3. Getting Started (Local Setup)

### 3.1 Clone and install
```bash
git clone <REPO_URL>
cd <REPO_DIR>
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -e ".[test]"
