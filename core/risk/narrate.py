"""Plain-English incident summaries — on top of the deterministic `why`, never
replacing it. Two paths:

  * deterministic  — a template built from the same factors. Always works, no
    network, no secret, no latency. This carries the live demo.
  * llm (optional) — if an OpenAI-compatible endpoint is configured via env
    (AEGIS_LLM_BASE_URL, AEGIS_LLM_API_KEY, AEGIS_LLM_MODEL), enrich the summary.
    Any failure falls back to the deterministic text — the pipeline never breaks.

The LLM sees only the already-computed facts (score, tactics, assets, why) as
data; it phrases, it does not decide. Scoring stays LLM-free.
"""
from __future__ import annotations

import json
import os
import urllib.request

from core.risk.scoring import TACTIC_STAGE, _norm_tactic

_ACTION = {
    "P1": "Isolate the affected asset and open an incident now.",
    "P2": "Assign to an analyst this shift.",
    "P3": "Queue for review; corroborate before acting.",
    "P4": "Auto-close unless new signal corroborates.",
}


def _furthest(inc) -> str:
    return max(inc.tactics, key=lambda t: TACTIC_STAGE.get(_norm_tactic(t), 0.25),
              default="activity")


def _headline_asset(inc) -> str:
    if not inc.assets:
        return "an unknown asset"
    key = max(inc.assets, key=inc.assets.get)
    tier = inc.assets[key]
    label = {3: "crown-jewel ", 2: "server ", 1: "workstation ", 0: ""}[tier]
    extra = len(inc.assets) - 1
    return f"{label}{key}" + (f" and {extra} other asset(s)" if extra else "")


def deterministic(inc, scored) -> str:
    band = scored["band"]
    n_tac = len(inc.tactics)
    descr = f"a {n_tac}-stage attack" if n_tac > 1 else "activity"
    fam = ", linked to a named threat family" if inc.threat_family else ""
    return (f"{band} — {descr} reached {_furthest(inc)} on "
            f"{_headline_asset(inc)}, corroborated by {inc.n_alerts} alert(s)"
            f"{fam}. Recommend: {_ACTION.get(band, 'review.')}")


def _llm(inc, scored) -> str | None:
    base = os.environ.get("AEGIS_LLM_BASE_URL")
    key = os.environ.get("AEGIS_LLM_API_KEY") or os.environ.get("ALIAS_API_KEY")
    if not base or not key:
        return None
    model = os.environ.get("AEGIS_LLM_MODEL", "alias2-mini")
    facts = {
        "priority": scored["band"], "risk_score": scored["score"],
        "tactics": sorted(inc.tactics), "assets": inc.assets,
        "alerts": inc.n_alerts, "why": scored["why"],
    }
    prompt = (
        "You are a SOC triage assistant. In ONE sentence, tell the analyst what "
        "this incident is and what to do first. Use only these facts; do not "
        "invent details:\n" + json.dumps(facts)
    )
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 120, "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None  # endpoint down / misconfigured -> deterministic carries it


def narrate(inc, scored, use_llm: bool = False) -> str:
    if use_llm:
        text = _llm(inc, scored)
        if text:
            return text
    return deterministic(inc, scored)


if __name__ == "__main__":
    from core.risk.correlate import correlate
    from core.risk.scenario import alerts
    from core.risk.scoring import score_incident
    incs = correlate(alerts())
    incs.sort(key=lambda i: score_incident(i)["score"], reverse=True)
    for inc in incs:
        s = score_incident(inc)
        print(narrate(inc, s))
