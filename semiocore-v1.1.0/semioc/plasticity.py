from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _mode(values: List[str]) -> str:
    # deterministic mode: tie-breaker by lexical order
    counts: Dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    maxc = max(counts.values())
    winners = sorted([k for k, c in counts.items() if c == maxc])
    return winners[0]

def _variance(xs: List[float]) -> float:
    if not xs:
        return 0.0
    mu = sum(xs) / float(len(xs))
    return sum((x - mu) ** 2 for x in xs) / float(len(xs))

def compute_plasticity_report(
    trace_paths: List[Path],
    *,
    ctx: str,
    channel: str,
    protocol: str = "Strict",
    window_size: int = 10,
    window_step: int = 10,
    program_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compute a semiodynamic plasticity report from one or more SemioCore trace files.
    This is intentionally deterministic and auditable: no randomness, stable ordering,
    explicit thresholds, and evidence digests.
    """
    if window_size <= 0 or window_step <= 0:
        raise ValueError("window_size and window_step must be > 0")
    if not trace_paths:
        raise ValueError("trace_paths must be non-empty")

    # load traces and collect evidence digests
    traces: List[Dict[str, Any]] = []
    digests: List[str] = []
    for p in trace_paths:
        if not p.is_file():
            raise FileNotFoundError(str(p))
        digests.append(_sha256_file(p))
        traces.append(json.loads(p.read_text(encoding="utf-8")))

    # provenance: prefer explicit program_file, else first trace's program_file, else empty
    if program_file is None:
        program_file = str(traces[0].get("program_file", ""))

    # collect events filtered by ctx+channel; sort deterministically by (t, step, idx)
    all_events: List[Tuple[float, int, int, Dict[str, Any]]] = []
    for ti, tr in enumerate(traces):
        events = tr.get("events", [])
        for ei, ev in enumerate(events):
            if ev.get("ctx") == ctx and ev.get("ch") == channel:
                t = float(ev.get("t", 0.0))
                step = int(ev.get("step", 0))
                all_events.append((t, step, ti * 1_000_000 + ei, ev))
    all_events.sort(key=lambda x: (x[0], x[1], x[2]))
    events = [ev for *_ , ev in all_events]

    if not events:
        raise ValueError(f"No events for ctx={ctx!r} and channel={channel!r} in provided traces")

    # Observables
    objs: List[str] = [str(ev.get("obj", "UNKNOWN")) for ev in events]
    sigs: List[float] = []
    kappas: List[float] = []
    undetermined_count = 0

    for ev in events:
        if "r_raw" in ev:
            sigs.append(float(ev["r_raw"]))
        elif "s" in ev:
            sigs.append(float(ev["s"]))
        else:
            sigs.append(0.0)

        if "kappa_loc" in ev:
            kappas.append(float(ev["kappa_loc"]))

        o = str(ev.get("obj", "UNKNOWN"))
        if o.upper() in {"UNDETERMINED", "UNKNOWN"}:
            undetermined_count += 1

    # Metric A: partition stability over event windows
    n = len(objs)
    stabilities: List[float] = []
    for start in range(0, n, window_step):
        window = objs[start:start + window_size]
        if not window:
            continue
        m = _mode(window)
        stabilities.append(sum(1 for v in window if v == m) / float(len(window)))
    partition_stability = sum(stabilities) / float(len(stabilities)) if stabilities else 1.0

    # Metric B: noise sensitivity
    deltaP = 0.0
    denom = 0.0
    for i in range(1, n):
        if objs[i] != objs[i - 1]:
            deltaP += 1.0
        denom += abs(sigs[i] - sigs[i - 1])
    noise_sensitivity = (deltaP / (denom + 1e-9)) if n > 1 else 0.0

    # Metric C: indeterminacy rate
    indeterminacy_rate = undetermined_count / float(n) if n else 0.0

    # Metric D: coherence loss (variance of kappa_loc if available)
    coherence_loss = _variance(kappas) if kappas else 0.0

    # Trend: compare first half vs second half partition stability (simple and deterministic)
    half = n // 2
    def _stab_for(segment: List[str]) -> float:
        if not segment:
            return 1.0
        m = _mode(segment)
        return sum(1 for v in segment if v == m) / float(len(segment))

    s1 = _stab_for(objs[:half])
    s2 = _stab_for(objs[half:])
    if s2 < s1 - 0.05:
        trend = "declining"
    elif s2 > s1 + 0.05:
        trend = "improving"
    else:
        trend = "stable"

    # Verdict (thresholds are part of the contract semantics)
    reasons: List[str] = []
    if partition_stability < 0.85:
        reasons.append("low_partition_stability")
    if noise_sensitivity > 2.0:
        reasons.append("high_noise_sensitivity")
    if indeterminacy_rate > 0.05:
        reasons.append("high_indeterminacy_rate")
    if coherence_loss > 0.05:
        reasons.append("high_coherence_loss")

    if not reasons:
        plasticity_state = "stable"
    elif partition_stability >= 0.70 and indeterminacy_rate <= 0.20:
        plasticity_state = "fragile"
    else:
        plasticity_state = "degraded"

    confidence = min(1.0, n / 50.0)

    report: Dict[str, Any] = {
        "schema": "semiocore.plasticity.v1",
        "program_file": program_file,
        "protocol": protocol,
        "ctx": ctx,
        "channel": channel,
        "windowing": {"mode": "fixed", "size": window_size, "step": window_step},
        "metrics": {
            "partition_stability": float(partition_stability),
            "noise_sensitivity": float(noise_sensitivity),
            "indeterminacy_rate": float(indeterminacy_rate),
            "coherence_loss": float(coherence_loss),
        },
        "verdict": {
            "plasticity_state": plasticity_state,
            "trend": trend,
            "confidence": float(confidence),
            "reasons": reasons,
        },
        "evidence": {
            "N_traces": int(len(trace_paths)),
            "N_events": int(n),
            "trace_digests": digests,
        },
    }
    return report
