# AegisSOC AI — Start Here (Problem E1)

**AI-driven, risk-based SOC incident triage:** ingest a multi-tool alert stream →
correlate related alerts into incidents → score by impact → output an **explainable,
prioritised queue** with the reconstructed attack chain.

## Run the demo
```bash
./demo_up.sh                 # first run provisions a venv + installs deps (a few min)
# → open http://localhost:7788  → click "Risk Queue" → expand the top P1 incident
```

## See it without the stack (headless, instant)
```bash
PYTHONPATH=$PWD python3 -m core.risk            # the full explained queue (P1 = 88.1)
PYTHONPATH=$PWD python3 -m core.risk.benchmark  # NDCG 0.896 vs real Microsoft analysts
```

## The engine (our core work) lives in `core/risk/`
| File | Role |
|---|---|
| `scenario.py` | curated demo alert stream (6 tools) |
| `correlate.py` | union-find correlation → reconstructed attack chain |
| `scoring.py` | deterministic 6-factor impact score (no LLM) → P1–P4 |
| `guide.py` / `benchmark.py` / `calibrate.py` | scale + evaluation on Microsoft GUIDE |
| `compliance.py` | DPDP / CERT-In / GDPR regulatory-exposure overlay |
| `dashboard.py` | serialises the queue for the console + API |

## Read this for the full walkthrough + panel Q&A
`core/risk/ATTACK_CHAIN_REVIEW.md` — end-to-end explanation, the P1 worked example
with exact scoring math, and every likely judge question with a complete answer.
Proof screenshot: `docs/RiskQueue_AttackChain.png`.

## Dataset
See `datasets/README.md`. The demo works out of the box (precomputed results ship in
`build/dashboard_data.json`); download the full GUIDE set only to re-run the benchmark.
