# AegisSOC AI — Risk Engine Build Checklist (E1)

Problem E1: ingest alert stream → correlate → risk-score by impact → explainable prioritised queue.
Working dir: `/run/media/ved/B6F06788F0674E25/aegis-work` · engine at `AegisSOC-AI-main/core/risk/`.
Dataset: Microsoft GUIDE (`datasets/guide/`). Runtime logs: `aegis-work/logs/`.

## Legend: [x] done · [~] in progress · [ ] todo

### Foundation
- [x] Repo reviewed; full rebrand to AegisSOC AI (0 upstream-brand residuals) — commit `7e94588`
- [x] GUIDE acquired: Train 9.5M, Test 4.1M, **Queue_Rankings 9981** (analyst priority ground truth)
- [x] Deterministic explainable scorer + self-check — commit `7b35b17`

### Day 1 — engine (headless, on real data)
- [x] `guide.py` — **scalable streaming** aggregator (chunked `usecols`); 9980 incidents / 131954 alerts in 17.4s @ 332MB peak. Reduction **13.2x**.
- [x] `benchmark.py` — vs QueueRank + TP-surfacing + baselines. Result: **NDCG 0.895** (strong top-of-queue), Spearman 0.299 (modest), TP-AUC 0.532 (≈random; impact≠maliciousness, and confidence/asset factors near-dead on hashed GUIDE).
- [x] `calibrate.py` — NNLS learning-to-rank; held-out Spearman 0.26→0.31, NDCG→0.896; learned profile `WEIGHTS_CALIBRATED` (asset 43 + progression 32 dominate, confidence→0). Scorer takes `weights=` param.
- [x] `correlate.py` — union-find alerts→incidents (shared entity + time window) + self-check
- [x] `scenario.py` — curated demo: 11 alerts/6 sources, "Operation Ledger" crown-jewel exfil chain + noise
- [x] `__main__.py` — CLI: `python -m core.risk` (demo, 11→5 incidents, P1 88.1) and `--guide N` (real data top-N). Full E1 loop.
- [x] `narrate.py` — plain-English summary + recommended action per incident. Deterministic template (always works) + optional LLM enrichment (env: AEGIS_LLM_BASE_URL/API_KEY/MODEL; alias2-mini gateway lives INSIDE the CSI docker image so not host-reachable — set the env to enable). CLI flags `--narrate` / `--llm`. Never in scoring path.

### Novelty — GRC / regulatory-exposure overlay
- [x] `compliance.py` — deterministic DPDP §8(6)+Rules2025 / CERT-In 2022 (6h) / GDPR / PCI / HIPAA mapping: data-class + kill-chain stage + incident time → obligations, live statutory clocks, penalty. Never touches the 6-factor score (benchmark stays valid). Self-check passes.
- [x] Asset data-class tags in `scenario.py` (db-prod-01=PII_HIGH, srv-app-07=FINANCIAL_CDE) + live timestamps; `correlate.py` propagates data_classes + detected_at.
- [x] Surfaced in console Risk Queue (⚖ badge + expandable exposure block w/ colour-coded clocks) AND standalone dashboard. Verified live in browser. Facts corrected (₹250/₹200 Cr, two-stage DPDP, CERT-In in-force).

### Day 2 — demo
- [x] Standalone AegisSOC-branded dashboard (published artifact) — `dashboard.py` + `dashboard_template.html`, real engine JSON, expandable `why`. Live.
- [x] **Console integration**: `/api/risk/queue` auto-discovered router (`risk_router.py`) + `RiskQueueScreen.tsx` wired into nav/SCREENS/TITLES + `riskApi`. Theme-adaptive (currentColor tints). Serves precomputed `build/dashboard_data.json` cache.
- [x] **Fixed rebrand boot-blocker**: `core/config.py` had 10 recursive `aegis_*` property aliases shadowing their own fields → `Settings()` crashed. Removed. Repo scanned: no other such collisions. (commit bcdfb01)
- [x] Web stack up + **console screen visually verified live** (DEV_MODE): nav item, KPI tiles, Curated + Real GUIDE tabs, expandable `why` breakdown, scores render. Layout width fixed (commit b6e4b81). API /api/risk/queue returns 200. Port note: KAVACH `pgvector` holds 5432 — `docker stop pgvector` before start, `docker start pgvector` after.
- [ ] (superseded line below) Console "Risk Queue" view (React) surfacing score + `why`
- [ ] Metrics/demo script; 3-min walkthrough leading with the QueueRank benchmark
- [ ] Rebrand runtime boot-test (Docker+npm) once stack is up

## Validation (last run 2026-09-26, log `logs/validate_*.log`)
- [x] all `core/risk/*.py` compile
- [x] scoring self-check (4 asserts) + correlate self-check pass standalone
- [x] scores deterministic across runs (`[27.6, 33.7, 35.9, 53.2, 88.1]`)
- [x] invariant: scoring path has no LLM/network import (pure)
- [x] invariant: grade/QueueRank never used as scoring inputs
- [x] rebrand integrity: 0 upstream-brand code refs
- note: repo-wide `pytest` hits a pre-existing eventlet/GreenSocket plugin conflict
  (needs the repo dev env); our engine self-validates standalone via the checks above.

## Design invariants (do not break)
- Scoring is deterministic — **no LLM in the score path** (auditability is the E1 differentiator).
- Aggregator streams — never load a full GUIDE CSV into memory.
- `IncidentGrade`/`QueueRank` are **ground truth for evaluation only**, never scoring inputs.
- Weights in `scoring.WEIGHTS` are the calibration knob; fit to QueueRank only if transparent weights underperform.
