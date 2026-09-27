"""Deterministic, explainable impact-based risk scoring for correlated incidents.

The score is a transparent weighted sum of six factors. No LLM, no black box:
every point an incident earns carries a human-readable reason, so an analyst can
read *why* it sits where it does in the queue. Weights sum to 100; the score is
0-100 and maps to a priority band P1-P4.

This is the E1 core: "risk-score by impact, output explainable prioritised queue."
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


# --- Incident: the unit we score (produced by correlation from raw alerts) ----
@dataclass
class Incident:
    incident_id: str
    org_id: str = ""
    tactics: set[str] = field(default_factory=set)      # ATT&CK tactics seen (GUIDE Category)
    techniques: set[str] = field(default_factory=set)   # ATT&CK technique ids
    n_alerts: int = 1                                    # distinct alerts correlated in
    assets: dict[str, int] = field(default_factory=dict)  # entity_key -> criticality tier 0..3
    confidence: float = 0.0                             # 0..1 detection fidelity (SuspicionLevel/verdict)
    threat_family: bool = False                          # a named malware/actor family attached
    grade: str | None = None                             # ground-truth TP/BP/FP — NEVER a scoring input
    data_classes: set[str] = field(default_factory=set)  # sensitivity of affected data (PII_HIGH, FINANCIAL_CDE, ePHI)
    detected_at: float | None = None                    # epoch seconds of earliest signal — drives statutory clocks
    members: list[dict] = field(default_factory=list)   # the correlated alerts, time-ordered — the reconstructed attack chain


# --- Factor result: points earned + the reason string shown to the analyst ----
@dataclass
class Factor:
    name: str
    points: float
    reason: str


# Weights (sum to 100). Deliberately readable and tunable — this is the knob a
# SOC calibrates to its own environment.
# ponytail: flat weights, no learned model. Fit weights to QueueRank later only
# if the transparent version measurably underperforms.
WEIGHTS = {
    "asset_criticality": 20,
    "kill_chain_stage": 25,
    "kill_chain_progression": 15,
    "blast_radius": 15,
    "detection_confidence": 15,
    "corroboration": 10,
}

# Profile learned by NNLS against Microsoft analyst QueueRank on held-out orgs
# (see calibrate.py). Zeroes detection_confidence because GUIDE leaves that field
# empty; use it for GUIDE-scale runs, keep the hand profile where confidence is
# real (e.g. the curated scenario).
WEIGHTS_CALIBRATED = {
    "asset_criticality": 43.2,
    "kill_chain_stage": 10.0,
    "kill_chain_progression": 31.7,
    "blast_radius": 7.0,
    "detection_confidence": 0.0,
    "corroboration": 8.1,
}

# ATT&CK tactic -> how far down the kill chain (0..1). Later stages = more damage
# already done = higher impact. Names match GUIDE's Category values.
TACTIC_STAGE = {
    "reconnaissance": 0.10, "resourcedevelopment": 0.10,
    "initialaccess": 0.35, "execution": 0.45, "persistence": 0.50,
    "privilegeescalation": 0.60, "defenseevasion": 0.55,
    "credentialaccess": 0.70, "discovery": 0.30, "lateralmovement": 0.75,
    "collection": 0.70, "commandandcontrol": 0.80,
    "exfiltration": 0.95, "impact": 1.00,
    "suspiciousactivity": 0.20, "malware": 0.65,
}

BANDS = [(75, "P1"), (50, "P2"), (25, "P3"), (0, "P4")]


def _norm_tactic(t: str) -> str:
    return t.strip().lower().replace(" ", "").replace("-", "").replace("_", "")


def _band(score: float) -> str:
    for threshold, label in BANDS:
        if score >= threshold:
            return label
    return "P4"


def score_incident(inc: Incident, weights: dict = WEIGHTS) -> dict:
    """Return {score, band, factors:[Factor], why:[str]}. Pure + deterministic.
    `weights` selects the scoring profile (hand default, or WEIGHTS_CALIBRATED)."""
    W = weights
    factors: list[Factor] = []

    # 1. Asset criticality — the impact anchor. Highest tier among affected assets.
    #    Tiers: 3=crown jewel (DC/DB/exec), 2=server, 1=workstation, 0=unknown/test.
    top_tier = max(inc.assets.values(), default=0)
    ac = top_tier / 3
    tier_name = {3: "crown-jewel", 2: "server", 1: "workstation", 0: "low-value/unknown"}[top_tier]
    factors.append(Factor("asset_criticality", ac * W["asset_criticality"],
                          f"highest-value asset is {tier_name}"))

    # 2. Kill-chain stage — furthest tactic reached.
    stages = [TACTIC_STAGE.get(_norm_tactic(t), 0.25) for t in inc.tactics]
    stage = max(stages, default=0.25)
    furthest = max(inc.tactics, key=lambda t: TACTIC_STAGE.get(_norm_tactic(t), 0.25),
                   default="unknown")
    factors.append(Factor("kill_chain_stage", stage * W["kill_chain_stage"],
                          f"reached '{furthest}' stage of the attack"))

    # 3. Kill-chain progression — a stitched multi-stage chain beats isolated alerts.
    n_tac = len(inc.tactics)
    prog = min(n_tac / 5, 1.0)  # 5+ distinct tactics saturates
    factors.append(Factor("kill_chain_progression", prog * W["kill_chain_progression"],
                          f"{n_tac} distinct attack stage(s) correlated"))

    # 4. Blast radius — distinct affected assets, log-scaled (1 asset ~0, 20+ ~full).
    n_assets = len(inc.assets)
    blast = math.log1p(max(n_assets - 1, 0)) / math.log1p(20)
    blast = min(blast, 1.0)
    factors.append(Factor("blast_radius", blast * W["blast_radius"],
                          f"{n_assets} asset(s) affected"))

    # 5. Detection confidence — how sure we are it's real.
    factors.append(Factor("detection_confidence", inc.confidence * W["detection_confidence"],
                          f"detection confidence {inc.confidence:.0%}"))

    # 6. Corroboration — more alerts agreeing (+ a named threat family) raises trust.
    corr = min(math.log1p(inc.n_alerts) / math.log1p(15), 1.0)
    if inc.threat_family:
        corr = min(corr + 0.2, 1.0)
    factors.append(Factor("corroboration", corr * W["corroboration"],
                          f"{inc.n_alerts} correlated alert(s)"
                          + (", named threat family" if inc.threat_family else "")))

    score = round(sum(f.points for f in factors), 1)
    band = _band(score)
    # why[]: the factors that actually moved the needle, biggest first.
    why = [f"{f.reason} (+{f.points:.0f})"
           for f in sorted(factors, key=lambda x: x.points, reverse=True) if f.points >= 1]
    return {"score": score, "band": band, "factors": factors, "why": why}
