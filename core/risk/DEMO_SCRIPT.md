# AegisSOC AI — Demo Runbook (Problem E1)

Everything needed to present the explainable, risk-based SOC triage engine in ~3 minutes.
Pull this up on a second screen.

Repo root: `/run/media/ved/B6F06788F0674E25/aegis-work/AegisSOC-AI-main`
Standalone fallback (already live, no stack): `https://claude.ai/artifact/TT7vWYzXWmhcDWShxZmBWP`

---

## 0. Pre-flight (before the room)

```bash
# KAVACH's postgres holds port 5432 — free it first (its data is safe in its volume)
docker stop pgvector
docker rm -f deeptempo-postgres 2>/dev/null

cd /run/media/ved/B6F06788F0674E25/aegis-work/AegisSOC-AI-main
cp env.example .env                                   # first time only
sed -i 's/^DEV_MODE=false/DEV_MODE=true/' .env        # auth bypass for a clean demo
python3 -m core.risk.dashboard > build/dashboard_data.json   # refresh the API cache (~35s)
SKIP_AGENT=1 ./start.sh                                # brings up Postgres + API + web
```
Then open **http://localhost:7788** and confirm the **Risk Queue** nav item loads.
When finished demoing: **`docker start pgvector`** to restore KAVACH.

The console is pre-populated (run once): 110 findings, 11 cases, 12 AI decisions, 6 workflow runs.
Re-seed with `scripts/generate_sample_data.py --api --url http://127.0.0.1:7787 --count 80 --cases 8`.

---

## 1. The 3-minute script

### 0:00–0:30 — Hook  · [on the Risk Queue screen]
> "A SOC analyst drowns in alerts — most are noise, the one that matters is buried. E1 asks for
> risk-based triage with *explainable* reasoning. So we built exactly that: it takes a flood of
> alerts, groups them into incidents, ranks them by real-world impact, and every rank explains
> itself in plain English. And we proved it against real Microsoft SOC analysts."

Point at the KPI tiles: **13.2× reduction · NDCG 0.896 · 132k→10k · 0 LLM in scoring.**

### 0:30–1:15 — Explainability  · [Curated tab → click the P1 "Exfiltration" row]
> "Top of the queue, priority one: a phishing email that walked all the way to data exfiltration
> on our production database. And here's *why* it's number one — not a black-box score, an actual
> breakdown: crown-jewel asset, reached the exfiltration stage, six-stage chain, 90% confidence.
> An analyst can trust this; an auditor can check it."

Scroll to a P3/P4: *"and the noise — a single low-confidence scan on a workstation — correctly sinks."*

### 1:15–1:35 — The novelty: SOC meets GRC  · [still on the expanded P1, scroll to the ⚖ block]
> "And here's what nobody else does — the same incident shows its **regulatory exposure**. This
> hit a personal-data asset, so a **CERT-In 6-hour clock** just started — 4 hours 25 left — and a
> **DPDP breach notice** is owed to the Data Protection Board of India, exposure up to ₹250 crore.
> GDPR runs in parallel. Triage and compliance in one queue — the analyst and the DPO see the
> same #1 incident. And it's deterministic — the clocks come from the incident time, not a guess."

### 1:15–2:00 — Real data at scale  · [Real GUIDE data tab]
> "That was the story version. This is the real thing — Microsoft's GUIDE dataset, real SOC
> telemetry from six thousand organizations. It reads:"

Read the context line: *"9,980 real incidents from 131,954 Microsoft SOC alerts; ordering measured
on 3,000 held-out incidents (NDCG 0.896)."*
> "A 13× cut in analyst workload, every incident still fully explained."

### 2:00–2:40 — The proof, live  · [terminal]
```bash
python3 -m core.risk.benchmark
```
> "Anyone can *claim* good prioritization. Here's the proof, computed live on the real dataset.
> GUIDE ships with the actual priority ordering Microsoft's human analysts assigned. We compare
> our ranking to theirs, on data the model never trained on."

When it prints: **"NDCG 0.9 — the incidents we rank at the top are the ones real analysts prioritized.
And we're honest where we're weaker: the tail is only moderate, because the dataset anonymizes the
asset context analysts use. We rank impact — which is what E1 asked for."**

### 2:40–3:00 — Close
> "A hundred-thirty-thousand alerts to a ranked, explained queue; validated against real Microsoft
> analysts; every decision auditable in plain English — where everyone else on this dataset ships a
> black box. And because the weights are transparent, the calibration *told us* how analysts
> prioritize: asset value and attack progression over raw severity. It's a triage engine that also
> teaches you how your SOC thinks. Explainable, risk-based, proven on real data — that's AegisSOC."

---

## 2. Cheat card

| Beat | Action | Say the number |
|---|---|---|
| Hook | KPI tiles | 13.2×, 0.896, 0 LLM |
| Explainability | expand P1 row | crown-jewel +20, exfil +24 |
| Scale | Real GUIDE tab | 132k → 10k, 13.2× |
| Proof | `python3 -m core.risk.benchmark` | **NDCG 0.896** vs real analysts |
| Close | — | "explainable, risk-based, proven" |

---

## 3. If a judge asks…

- **"Where's the code?"** → `core/risk/` (~1,090 lines). Scoring `scoring.py`, correlation
  `correlate.py`, benchmark `benchmark.py`, API `risk_router.py`, console screen
  `clients/web/src/screens/riskqueue/`.
- **"Run it on the real dataset."** → `python3 -m core.risk --guide 15`
- **"Recompute the metric in front of me."** → `python3 -m core.risk.benchmark` (streams the real
  1 GB CSV in ~16s — the strongest "not hardcoded" move).
- **"Prove it's not overfit."** → `python3 -m core.risk.calibrate` (held-out orgs).
- **"How do the compliance clocks work?"** → deterministic (`core/risk/compliance.py`): incident time + the affected asset's data-classification → applicable frameworks + statutory windows. No LLM.
- **"Which regulations?"** → CERT-In 2022 (6h, in force since Jun 2022 — the live one for India); DPDP Act 2023 §8(6) + Rules 2025 (Board + Data Principals "without delay", detailed report to the Board within 72h; ₹250 Cr safeguards / ₹200 Cr notification; breach provisions phasing in ~2027); GDPR Art.33/34 (72h, €20M/4%). On GUIDE the PII signal is anonymized, so compliance shines on the curated scenario; in production it reads the asset inventory's data-class tags.
- **"Show the raw ground truth."** → `datasets/guide/GUIDE_Test_Queue_Rankings.csv`.
- **"Do your tests pass?"** → `python3 -m core.risk.test_scoring`
- **"Is scoring an LLM?"** → No — deterministic weighted sum, zero LLM in the score path. The
  plain-English summary is generated on top and never changes a score.

## 4. Honest lines (say these — they build credibility)
- The **console demo data** (Cases, AI Decisions, Findings) is generated sample data to fill the
  platform; **Risk Queue is the real, benchmarked E1 work.**
- **Health's** LLM-spend and approvals are empty because this offline demo runs with no LLM
  provider and no agent layer — truthful, not broken.
- Full-queue Spearman (~0.31) is moderate because GUIDE anonymizes asset context; NDCG (top of
  queue, what matters operationally) is strong at 0.896.

## 4b. Data sources & scope (for the tough technical questions)

**"Which endpoints / are you seeing only logs?"**
Multi-source *detections*, not just logs — we sit at the alert/finding layer.
- **Real GUIDE data:** real Microsoft SOC telemetry, 33 entity types — endpoint (device), identity (accounts/SID/UPN), email, files (SHA-256), URLs, IPs, registry, OAuth apps, cloud resources — each alert tagged with MITRE technique + detector + verdict.
- **Curated scenario:** 6 tool types — EDR (CrowdStrike), NDR/network (Zeek), IDS (Suricata), DLP (Purview), identity/auth (Entra ID), DNS (Umbrella).
- **Boundary to state:** "We consume normalized alerts/findings from the detection layer; we don't capture raw packets or run our own sensors. The platform ingests logs/flows/WAF via SIEM, Kafka and MCP connectors, and our engine works on the resulting findings." (E1 is the alert stream, not raw-log parsing.)

**"Do you turn low-level alerts into a full attack chain?"**
- ✅ **YES — defensive attack-chain reconstruction (claim this hard).** Correlation stitches individually-minor alerts sharing entities within a time window into one multi-stage incident, and the kill-chain-progression factor escalates the chain above isolated alerts. The P1 is the proof: phishing→execution→LSASS cred-dump→lateral move→staging→exfiltration = six low/medium alerts that alone sit in the noise, but chained onto a crown-jewel DB become P1 (88.1). Point at the tactic chips as the reconstructed path.
- ❌ **NOT vulnerability→exploit-path prediction (disown cleanly).** We don't scan for CVEs, execute exploits, or predict attack paths from vulnerabilities + AD topology (BloodHound / attack-graph territory). Say: "We chain **alerts that already fired** into an attack narrative and prioritize by impact — that's detection-side. Predicting exploit paths from raw vulnerabilities is offensive attack-graph work; that's our roadmap (Pillar 3), not a claim we make today."
- **The trap:** never say "we chain vulnerabilities into exploits" — if probed for a CVE-to-exploit path you have nothing. Say "we reconstruct the attack chain from correlated alerts and escalate by impact — here's the six-stage P1."

**"How do you correlate the alerts?"**
Union-find over shared entities within a time window (`correlate.py`). (1) every alert starts alone; (2) index alerts by the entities they touch (host/user/IP); (3) link alerts that share an entity within 60 min; (4) each connected group = one incident. Transitive: in the P1, the **lateral-movement alert (NET-8801) touches both ws-042 AND db-prod-01** — that single pivot merges the workstation cluster and the database cluster into one 6-alert incident. Time window stops false links (a scan on an IP today won't merge with an unrelated hit last month). Validated on GUIDE against Microsoft analysts' own `IncidentId` grouping.

**"You depend on an external API provider — isn't that a risk?"**
The triage core has **zero external dependency.** Correlation, scoring, and the DPDP/CERT-In clocks are pure deterministic Python — no LLM, no external calls, runs **air-gapped**. The only optional external touch is the plain-English summary, which (a) falls back to a template needing no LLM, and (b) can run on a **local on-prem model** (Ollama/vLLM) via the Bifrost gateway. For DPDP-sensitive data this is the point: *"Sending Aadhaar/PAN telemetry to a foreign cloud LLM is itself a compliance risk — our core is deterministic and any LLM can run entirely on-prem, so sensitive data never leaves the org."* No lock-in — gateway routes Anthropic/OpenAI/Ollama/custom.

**"How are the agents deployed — LangGraph?"**
No — **not** LangGraph/LangChain/CrewAI. Your E1 engine uses **no agents at all** (deterministic Python). The platform's 13 agents run on a **custom event-sourced TypeScript harness**: Markdown playbooks (`WORKFLOW.md`) define ordered phases (one agent each); durable runs via BullMQ/Redis; every run is an **append-only Ledger that folds to state** (deterministic, replayable, tamper-evident); tools via MCP; LLM via Bifrost. Say: *"We chose an event-sourced harness over LangGraph specifically for determinism, replay, and an audit trail — you can rebuild exactly what any decision saw. SOC and compliance work demand that; a general agent framework doesn't give it out of the box."* Honest framing: the harness is the platform we built on; **our contribution is the deterministic risk + compliance engine on top.**

## 5. If the stack dies mid-demo
Open the standalone artifact: `https://claude.ai/artifact/TT7vWYzXWmhcDWShxZmBWP` — same queue,
same explainable breakdowns, no backend. Never let a Docker hiccup cost the demo.

## 6. Headline dataset facts
Microsoft GUIDE (Kaggle "Microsoft Security Incident Prediction", CDLA-2.0): real SOC telemetry,
6,100+ orgs, 13M evidence rows, 441 MITRE techniques. Ground truth we benchmark against:
`IncidentId` (correlation), `IncidentGrade` TP/BP/FP (triage), `QueueRank` (prioritisation).
