"""Emit the dashboard's data as JSON — real engine output, not mock numbers.

Produces: the curated demo queue, the top real-GUIDE incidents, and the headline
KPIs (alert->incident reduction + agreement with analyst QueueRank). The static
dashboard HTML embeds this so what a judge sees is exactly what the engine
computes.

  python -m core.risk.dashboard > build/dashboard_data.json
"""
from __future__ import annotations

import json
import sys

from core.risk.correlate import correlate
from core.risk.narrate import narrate
from core.risk.scoring import (TACTIC_STAGE, WEIGHTS, WEIGHTS_CALIBRATED,
                               _norm_tactic, score_incident)


def _furthest(inc):
    return max(inc.tactics, key=lambda t: TACTIC_STAGE.get(_norm_tactic(t), 0.25),
              default="activity")


def _headline_asset(inc):
    if not inc.assets:
        return "unknown"
    return max(inc.assets, key=inc.assets.get)


def _compliance(inc):
    from core.risk.compliance import assess
    a = assess(inc)
    return {
        "breach": a.breach, "reportable": a.reportable, "pii_exposed": a.pii_exposed,
        "data_classes": a.data_classes, "notice_required": a.notice_required,
        "penalty_headline": a.penalty_headline, "summary": a.summary,
        "obligations": [{
            "framework": o.framework, "regulator": o.regulator, "jurisdiction": o.jurisdiction,
            "duty": o.duty, "penalty": o.penalty, "in_force": o.in_force,
            "clock": ({"label": o.clock.label, "remaining_h": o.clock.remaining_h,
                       "status": o.clock.status, "window_h": o.clock.hours}
                      if o.clock else None),
        } for o in a.obligations],
    }


def _chain(inc):
    """The reconstructed attack chain: correlated alerts in the order they fired,
    each with a relative time from the first signal — this is the multi-stage
    story the analyst reads, not just a set of tactics."""
    base = inc.members[0]["ts"] if inc.members and inc.members[0].get("ts") is not None else None
    steps = []
    for m in inc.members:
        ts, rel = m.get("ts"), None
        if base is not None and ts is not None:
            rel = f"+{round((ts - base) / 60)}m"
        steps.append({"tactic": m["tactic"], "source": m.get("source"),
                      "title": m.get("title"), "technique": m.get("technique"),
                      "alert_id": m.get("alert_id"), "at": rel})
    return steps


def _serialize(inc, weights):
    out = score_incident(inc, weights)
    return {
        "compliance": _compliance(inc),
        "band": out["band"], "score": out["score"], "n_alerts": inc.n_alerts,
        "furthest_tactic": _furthest(inc),
        "headline_asset": _headline_asset(inc),
        "n_assets": len(inc.assets),
        "tactics": sorted(inc.tactics),
        "chain": _chain(inc),
        "why": out["why"],
        "narrative": narrate(inc, out),
        "grade": inc.grade,
        "factors": [{"name": f.name, "points": round(f.points, 1), "reason": f.reason}
                    for f in out["factors"]],
    }


def build(include_guide: bool = True):
    from core.risk.scenario import alerts
    stream = alerts()
    cur_incs = correlate(stream)
    curated = sorted((_serialize(i, WEIGHTS) for i in cur_incs),
                     key=lambda d: d["score"], reverse=True)
    sources = sorted({a.get("source", "?") for a in stream})

    data = {
        "brand": "AegisSOC AI",
        "problem": "E1 — AI-driven, risk-based SOC incident triage",
        "curated": {
            "alerts": len(stream), "sources": sources,
            "incidents": len(cur_incs),
            "reduction": round(len(stream) / len(cur_incs), 1),
            "queue": curated,
        },
    }

    if not include_guide:
        return data

    # Real GUIDE — optional (skip gracefully if the dataset isn't present).
    # Headline ordering metrics come from calibrate.run() = held-out orgs (the
    # rigorous number), not the in-sample fit.
    try:
        from core.risk.calibrate import run as calibrate_run
        from core.risk.guide import aggregate_incidents, load_rankings
        ranks = load_rankings()
        incs = aggregate_incidents(keep=set(ranks))
        total_alerts = sum(i.n_alerts for i in incs.values())
        top = sorted((_serialize(v, WEIGHTS_CALIBRATED) for v in incs.values()),
                     key=lambda d: d["score"], reverse=True)[:12]
        cal = calibrate_run()
        data["guide"] = {
            "incidents": len(incs), "alerts": total_alerts,
            "reduction": round(total_alerts / len(incs), 1),
            "ndcg_vs_analyst": round(cal["ndcg_after"], 3),
            "spearman_vs_analyst": round(cal["spearman_after"], 3),
            "held_out_incidents": cal["held_out_incidents"],
            "metrics_note": "held-out orgs (never seen during weight fit)",
            "top": top,
        }
    except (FileNotFoundError, OSError, ImportError) as e:
        # dataset absent or an optional dep (scipy) missing → the GUIDE tab is
        # simply "not loaded"; the curated queue must still ship.
        data["guide"] = {"unavailable": str(e)}
    return data


def render_html(out_path: str) -> None:
    """Inject the engine JSON into dashboard_template.html -> a standalone page."""
    import pathlib
    here = pathlib.Path(__file__).parent
    tmpl = (here / "dashboard_template.html").read_text()
    html = tmpl.replace("__DATA__", json.dumps(build()))
    assert "__DATA__" not in html, "template placeholder missing"
    pathlib.Path(out_path).write_text(html)


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--html":
        render_html(sys.argv[2])
        print(f"wrote {sys.argv[2]}")
    else:
        json.dump(build(), sys.stdout, indent=2)
        sys.stdout.write("\n")
