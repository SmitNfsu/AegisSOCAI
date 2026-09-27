# Datasets

## Microsoft GUIDE (security incident prediction)

Source: Kaggle `Microsoft/microsoft-security-incident-prediction` (license CDLA-2.0).
Used as the benchmark backbone — 9,980 real incidents with analyst triage grades
(TP/BP/FP) and an analyst queue ranking, so the risk engine can be measured against
real SOC analysts.

### What's committed (small, works out of the box)
- `guide/sample/GUIDE_Test.sample.csv` — first 20,000 rows of the test set (for a quick look)
- `guide/sample/GUIDE_Test_Queue_Rankings.csv` — **full** analyst queue-ranking ground truth (9,981 incidents, 136 KB)

### Getting the full dataset (2.4 GB train + 1 GB test — not committed; GitHub caps files at 100 MB)
```
pip install kaggle
# put your Kaggle API token at ~/.kaggle/kaggle.json, then:
python datasets/guide/download_guide.py
```
This populates `datasets/guide/` with `GUIDE_Train.csv`, `GUIDE_Test.csv`, and
`GUIDE_Test_Queue_Rankings.csv`. The engine auto-discovers this path (override with
`AEGIS_GUIDE_DIR`).

### You don't strictly need it to run the demo
The precomputed benchmark results (NDCG 0.896, 13.2× reduction) ship in
`build/dashboard_data.json`, so the console Risk Queue and the "Real GUIDE data" tab
render immediately. Download the full set only to re-run the benchmark yourself:
```
PYTHONPATH=$PWD python3 -m core.risk.benchmark
```

## Curated scenario ("Operation Ledger")
The live-demo attack chain (phishing → exfiltration on a crown-jewel DB, 6 alerts /
3 tools) is defined in code at `core/risk/scenario.py` — no dataset needed.
