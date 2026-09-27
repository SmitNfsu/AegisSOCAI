"""Interpretable learning-to-rank: earn the scorer's weights from analyst QueueRank.

The model stays a transparent weighted sum of the same six factors — we only
replace the hand-picked weights with ones fit to real analyst prioritization via
non-negative least squares (NNLS keeps every weight >= 0, so no factor flips into
a nonsensical negative contribution and the `why` breakdown stays honest).

Fit on a random split of *organizations*, evaluate on the held-out orgs, and
compare Spearman/NDCG before vs after. IncidentGrade is never used here.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import nnls
from scipy.stats import spearmanr
from sklearn.metrics import ndcg_score

from core.risk.guide import aggregate_incidents, load_rankings
from core.risk.scoring import WEIGHTS, score_incident

FACTORS = list(WEIGHTS)  # stable order


def _raw_factors(inc) -> np.ndarray:
    """The six factor values in [0,1] BEFORE weighting (points / weight)."""
    out = score_incident(inc)
    by = {f.name: f.points for f in out["factors"]}
    return np.array([by[name] / WEIGHTS[name] for name in FACTORS])


def _build(incs: dict, ranks: dict):
    """Return X (n,6), org ids, and per-org normalized relevance y in [0,1]."""
    rows, orgs, y = [], [], []
    per_org_max: dict[str, int] = {}
    for (org, inc) in incs:
        r = ranks.get((org, inc))
        if r is not None:
            per_org_max[org] = max(per_org_max.get(org, 0), r)
    for (org, inc), incident in incs.items():
        r = ranks.get((org, inc))
        if r is None:
            continue
        n = per_org_max[org]
        rows.append(_raw_factors(incident))
        orgs.append(org)
        y.append((n - r + 1) / n)  # QueueRank 1 -> relevance 1.0
    return np.array(rows), np.array(orgs), np.array(y)


def _eval(X, orgs, ranks_by_row, weights) -> dict:
    scores = X @ weights
    by_org: dict[str, list[tuple[float, int]]] = {}
    for s, org, r in zip(scores, orgs, ranks_by_row):
        by_org.setdefault(org, []).append((s, r))
    sp_w = nd_w = n_w = 0.0
    for org, pairs in by_org.items():
        if len(pairs) < 3:
            continue
        sc = np.array([p[0] for p in pairs]); qr = np.array([p[1] for p in pairs])
        rho, _ = spearmanr(sc, -qr)
        if np.isnan(rho):
            continue
        rel = (qr.max() - qr + 1).reshape(1, -1)
        nd = ndcg_score(rel, sc.reshape(1, -1))
        w = len(pairs); sp_w += rho * w; nd_w += nd * w; n_w += w
    return {"spearman": sp_w / n_w, "ndcg": nd_w / n_w, "incidents": int(n_w)}


def run(seed: int = 0) -> dict:
    ranks = load_rankings()
    incs = aggregate_incidents(keep=set(ranks))
    X, orgs, y = _build(incs, ranks)
    ranks_by_row = np.array([ranks[(o, i)] for (o, i) in
                             [(org, inc) for (org, inc) in incs if (org, inc) in ranks]])

    rng = np.random.default_rng(seed)
    uniq = np.unique(orgs)
    rng.shuffle(uniq)
    train_orgs = set(uniq[: int(len(uniq) * 0.7)])
    tr = np.array([o in train_orgs for o in orgs])
    te = ~tr

    # current (hand) weights, in FACTORS order
    hand = np.array([WEIGHTS[f] for f in FACTORS], dtype=float)
    # fit new weights on TRAIN only
    w_fit, _ = nnls(X[tr], y[tr])
    if w_fit.sum() > 0:
        w_scaled = w_fit / w_fit.sum() * 100  # keep the 0-100 scale
    else:
        w_scaled = hand

    before = _eval(X[te], orgs[te], ranks_by_row[te], hand)
    after = _eval(X[te], orgs[te], ranks_by_row[te], w_scaled)
    return {
        "held_out_incidents": before["incidents"],
        "hand_weights": {f: round(v, 1) for f, v in zip(FACTORS, hand)},
        "learned_weights": {f: round(v, 1) for f, v in zip(FACTORS, w_scaled)},
        "spearman_before": before["spearman"], "spearman_after": after["spearman"],
        "ndcg_before": before["ndcg"], "ndcg_after": after["ndcg"],
    }


if __name__ == "__main__":
    import json, time
    t0 = time.time()
    rep = run()
    print(json.dumps(rep, indent=2))
    print(f"spearman {rep['spearman_before']:.3f} -> {rep['spearman_after']:.3f} | "
          f"ndcg {rep['ndcg_before']:.3f} -> {rep['ndcg_after']:.3f} "
          f"({time.time()-t0:.1f}s)")
