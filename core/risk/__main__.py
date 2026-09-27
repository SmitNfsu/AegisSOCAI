"""AegisSOC AI risk-triage CLI — the full E1 loop, end to end.

  python -m core.risk              # curated demo: alerts -> correlate -> score -> queue
  python -m core.risk --guide 15   # top-15 queue over real Microsoft GUIDE incidents
"""
from __future__ import annotations

import argparse

from core.risk.correlate import correlate
from core.risk.scoring import TACTIC_STAGE, WEIGHTS_CALIBRATED, _norm_tactic, score_incident


def _furthest(inc) -> str:
    return max(inc.tactics, key=lambda t: TACTIC_STAGE.get(_norm_tactic(t), 0.25),
              default="unknown")


def _headline_asset(inc) -> str:
    if not inc.assets:
        return "unknown asset"
    key = max(inc.assets, key=inc.assets.get)
    extra = len(inc.assets) - 1
    return key + (f" (+{extra} more)" if extra else "")


def _print_queue(incidents, weights=None, top=None, show_why=True,
                 narrate=False, use_llm=False):
    scored = []
    for inc in incidents:
        out = score_incident(inc, weights) if weights else score_incident(inc)
        scored.append((out, inc))
    scored.sort(key=lambda x: x[0]["score"], reverse=True)
    if top:
        scored = scored[:top]
    print(f"\n{'#':>2}  {'PRI':<4}{'SCORE':>6}  {'ALRT':>4}  INCIDENT")
    print("─" * 78)
    for rank, (out, inc) in enumerate(scored, 1):
        print(f"{rank:>2}  {out['band']:<4}{out['score']:>6.1f}  {inc.n_alerts:>4}  "
              f"{_furthest(inc):<16} {_headline_asset(inc)}")
        if narrate:
            from core.risk.narrate import narrate as _n
            print(f"       » {_n(inc, out, use_llm=use_llm)}")
        if show_why:
            for w in out["why"][:4]:
                print(f"          └─ {w}")
    print("─" * 78)


def run_demo(narrate=False, use_llm=False):
    from core.risk.scenario import alerts
    stream = alerts()
    incidents = correlate(stream)
    sources = sorted({a.get("source", "?") for a in stream})
    print(f"Ingested {len(stream)} alerts from {len(sources)} sources: {', '.join(sources)}")
    print(f"Correlated → {len(incidents)} incidents "
          f"({len(stream) / len(incidents):.1f}× fewer things to look at)")
    _print_queue(incidents, narrate=narrate, use_llm=use_llm)
    print("Every rank above is a transparent weighted sum — no LLM in the scoring path.")


def run_guide(top: int, narrate=False, use_llm=False):
    from core.risk.guide import aggregate_incidents, load_rankings
    print("Loading real Microsoft GUIDE incidents (streaming)…")
    ranks = load_rankings()
    incs = aggregate_incidents(keep=set(ranks))
    total_alerts = sum(i.n_alerts for i in incs.values())
    print(f"{len(incs)} incidents from {total_alerts} alerts "
          f"({total_alerts / len(incs):.1f}× reduction). Top {top} by risk:")
    _print_queue(list(incs.values()), weights=WEIGHTS_CALIBRATED, top=top,
                 show_why=True, narrate=narrate, use_llm=use_llm)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(prog="core.risk")
    ap.add_argument("--guide", nargs="?", type=int, const=15, default=None,
                    help="run over real GUIDE incidents, show top N (default 15)")
    ap.add_argument("--narrate", action="store_true",
                    help="add a plain-English summary + recommended action per incident")
    ap.add_argument("--llm", action="store_true",
                    help="use the configured LLM for the summary (falls back to template)")
    args = ap.parse_args()
    if args.guide is not None:
        run_guide(args.guide, narrate=args.narrate, use_llm=args.llm)
    else:
        run_demo(narrate=args.narrate, use_llm=args.llm)
