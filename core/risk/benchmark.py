"""Benchmark the transparent risk scorer against GUIDE ground truth.

Two questions, both answered on real Microsoft SOC data:
  1. Ordering  — does our impact score reproduce analysts' QueueRank ordering?
                 (per-org Spearman + NDCG)
  2. Triage    — does a high score mean a real threat (TruePositive)?
                 (ROC-AUC, average precision, top-decile precision)

Naive baselines (alert-count, kill-chain-stage alone) show the six-factor model
earns its complexity. IncidentGrade/QueueRank are evaluation-only, never inputs.
"""
from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr
from sklearn.metrics import average_precision_score, ndcg_score, roc_auc_score

from core.risk.guide import aggregate_incidents, load_rankings
from core.risk.scoring import Incident, TACTIC_STAGE, _norm_tactic, score_incident


def _stage_only(inc: Incident) -> float:
    return max((TACTIC_STAGE.get(_norm_tactic(t), 0.25) for t in inc.tactics), default=0.0)


def ordering_metrics(scored: dict[tuple[str, str], float],
                     ranks: dict[tuple[str, str], int]) -> dict:
    """Per-org agreement between our score and analyst QueueRank."""
    by_org: dict[str, list[tuple[float, int]]] = {}
    for (org, inc), s in scored.items():
        r = ranks.get((org, inc))
        if r is not None:
            by_org.setdefault(org, []).append((s, r))
    sp_w, ndcg_w, n_w, n_orgs = 0.0, 0.0, 0, 0
    for org, pairs in by_org.items():
        if len(pairs) < 3:  # tiny orgs are noisy
            continue
        scores = np.array([p[0] for p in pairs])
        qrank = np.array([p[1] for p in pairs])
        rho, _ = spearmanr(scores, -qrank)  # high score should track low rank-number
        if np.isnan(rho):
            continue
        relevance = (qrank.max() - qrank + 1).reshape(1, -1)  # rank1 -> highest relevance
        nd = ndcg_score(relevance, scores.reshape(1, -1))
        w = len(pairs)
        sp_w += rho * w
        ndcg_w += nd * w
        n_w += w
        n_orgs += 1
    return {"spearman": sp_w / n_w, "ndcg": ndcg_w / n_w,
            "orgs_evaluated": n_orgs, "incidents_evaluated": n_w}


def triage_metrics(incs: dict, score_fn) -> dict:
    y = np.array([1 if i.grade == "TruePositive" else 0 for i in incs.values()])
    s = np.array([score_fn(i) for i in incs.values()])
    order = np.argsort(-s)
    top10 = order[: max(1, len(order) // 10)]
    base = y.mean()
    return {
        "roc_auc": roc_auc_score(y, s),
        "avg_precision": average_precision_score(y, s),
        "top_decile_precision": y[top10].mean(),
        "base_rate_TP": base,
        "lift": y[top10].mean() / base if base else float("nan"),
    }


def run() -> dict:
    ranks = load_rankings()
    incs = aggregate_incidents(keep=set(ranks))
    scored = {k: score_incident(v)["score"] for k, v in incs.items()}

    full = triage_metrics(incs, lambda i: score_incident(i)["score"])
    naive_alerts = triage_metrics(incs, lambda i: i.n_alerts)
    naive_stage = triage_metrics(incs, _stage_only)
    order = ordering_metrics(scored, ranks)

    total_alerts = sum(i.n_alerts for i in incs.values())
    report = {
        "incidents": len(incs),
        "alerts": total_alerts,
        "alert_to_incident_reduction": round(total_alerts / max(len(incs), 1), 1),
        "ordering_vs_analyst_QueueRank": order,
        "triage_full_model": full,
        "triage_baseline_alert_count": naive_alerts,
        "triage_baseline_stage_only": naive_stage,
    }
    return report


def _fmt(d: dict, indent=0) -> str:
    out = []
    for k, v in d.items():
        pad = "  " * indent
        if isinstance(v, dict):
            out.append(f"{pad}{k}:")
            out.append(_fmt(v, indent + 1))
        elif isinstance(v, float):
            out.append(f"{pad}{k}: {v:.3f}")
        else:
            out.append(f"{pad}{k}: {v}")
    return "\n".join(out)


if __name__ == "__main__":
    import time
    t0 = time.time()
    rep = run()
    print(_fmt(rep))
    print(f"\n(benchmark completed in {time.time() - t0:.1f}s)")
