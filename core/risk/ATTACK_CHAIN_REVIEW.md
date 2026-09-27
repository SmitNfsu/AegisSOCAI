# AegisSOC AI — Attack-Chain Reconstruction: Review & Panel Q&A

Problem **E1** — AI-driven, risk-based SOC incident triage. This document covers the
**attack-chain reconstruction** feature end-to-end: how to review it, how it works,
the exact numbers, and every question a panel can ask with a complete answer.

All numbers below are pulled from the live engine (`build/dashboard_data.json`), not
asserted. Regenerate any time with:
```
PYTHONPATH=$PWD python3 -m core.risk.dashboard > build/dashboard_data.json
```

---

## PART 1 — HOW TO REVIEW IT

### A. See it in the platform (what the panel sees)
```
docker stop pgvector                 # free port 5432 (a local Postgres container)
cd AegisSOCAI
./demo_up.sh                          # starts Postgres + API + web
# → open http://localhost:7788 → click "Risk Queue" in the nav
# → click the #1 P1 row to expand → "Reconstructed attack chain" block
docker start pgvector                 # restart it when done
```
In the expanded P1 you will see six alerts, in time order, each tagged with the
**tool that raised it** (CrowdStrike, Zeek, Purview), the ATT&CK technique, and the
minute it fired (+0m … +45m). That timeline is the reconstructed chain.

### B. Verify it headless (prove the data is real, no UI)
```
PYTHONPATH=$PWD python3 -m core.risk           # curated queue, every rank explained
PYTHONPATH=$PWD python3 -m core.risk.correlate # correlation self-check passes
PYTHONPATH=$PWD python3 -m core.risk.benchmark # NDCG 0.896 vs real analyst ranking
```
The chain also lives in the API response and the cache:
```
curl -s localhost:7787/api/risk/queue | jq '.curated.queue[0].chain'
jq '.curated.queue[0].chain' build/dashboard_data.json
```

### C. Where the code lives (5 files, all under `core/risk/` + one screen)
| File | Role in the chain |
|---|---|
| `scenario.py` | the curated alert stream — every alert with `source` (tool), `ts`, `tactic`, `title`, `technique`, `confidence` |
| `correlate.py` | **union-find** correlation → stitches alerts sharing an entity within a time window into one incident; retains the time-ordered `members` list |
| `scoring.py` | the `Incident` object (now carries `members`) + the 6-factor impact score |
| `dashboard.py` | `_chain()` serializes the ordered members into the `chain` array the UI reads |
| `clients/web/src/screens/riskqueue/RiskQueueScreen.tsx` | renders the "Reconstructed attack chain" timeline in the expand panel |

---

## PART 2 — END-TO-END PIPELINE

```
 raw alerts (multi-tool)          correlation            scoring            queue
 CrowdStrike / Zeek / Purview  →  union-find on      →  6-factor       →  P1–P4,
 Suricata / Entra ID / Umbrella   shared entity +       impact score      ranked,
                                   time window          (0–100)           each explained
                                        │                                     │
                                        └── retains time-ordered members ─────┘
                                            = the reconstructed attack chain
```

**Stage 1 — Ingest (the tools / data sources).** We consume *already-fired detections*
from real SOC sensor classes, not raw packets:

| Tool (in the demo) | Sensor class | What it detects here |
|---|---|---|
| **CrowdStrike** | EDR (endpoint) | phishing open, malicious macro→PowerShell, LSASS credential dump |
| **Zeek** | NDR (network) | SMB lateral movement, large outbound transfer to a rare ASN |
| **Purview** | DLP (data-loss) | bulk records staged from the database |
| **Suricata** | IDS/IPS (network) | RDP brute force, internal port scan |
| **Entra ID** | Identity | successful login after many failures |
| **Umbrella** | DNS security | lookup to a newly-registered domain |

The point for the panel: **six different vendors/telemetry types, one unified pipeline.**
Each alert carries the entities it touches (host, user, IP) with an asset-criticality tier.

**Stage 2 — Correlate (union-find).** Alerts that share an entity (e.g. `host:ws-042`,
`host:db-prod-01`) and fall within a **60-minute** window of a neighbour are unioned into
one incident. This is the standard SOC heuristic for stitching a multi-stage intrusion.
We keep the correlated alerts as a **time-ordered `members` list** — that ordered list
*is* the reconstructed attack chain.

**Stage 3 — Score (6 factors, fully explainable, no LLM).** Each incident gets a
0–100 impact score = sum of 6 weighted sub-scores, each emitting a plain-English reason.
See Part 3 for the exact math.

**Stage 4 — Prioritise.** Score → band: **P1 ≥ 75, P2 ≥ 50, P3 ≥ 25, P4 < 25** →
recommended action (P1 isolate now, P2 assign this shift, P3 queue for review, P4 auto-close).

---

## PART 3 — THE P1 WORKED EXAMPLE (memorise this)

Curated scenario "Operation Ledger": **11 alerts / 6 sources → 5 incidents (2.2× fewer).**
The #1 incident is the crown-jewel exfiltration, **P1 = 88.1**.

### The reconstructed chain (6 alerts, 3 tools, 45 minutes)
| Time | Stage (ATT&CK) | Tool | Technique | Alert |
|---|---|---|---|---|
| +0m | InitialAccess | CrowdStrike | — | Phishing attachment opened |
| +4m | Execution | CrowdStrike | T1059.001 | Malicious macro spawned PowerShell |
| +15m | CredentialAccess | CrowdStrike | T1003.001 | LSASS credential access |
| +25m | LateralMovement | Zeek | — | SMB lateral movement to DB server |
| +35m | Collection | Purview | — | Bulk records staged from database |
| +45m | Exfiltration | Zeek | T1048.003 | Large outbound transfer to rare ASN |

Each of these six, alone, is low/medium noise. **Chained onto a crown-jewel database,
they become the top P1.** That is the whole thesis of the feature.

### Why 88.1 — the factor math (hand-tuned weights, real confidence)
| Factor | Weight | Formula | Value | Points | Reason shown |
|---|---|---|---|---|---|
| asset_criticality | 20 | tier/3 (crown-jewel=3) | 3/3 | **20.0** | highest-value asset is crown-jewel |
| kill_chain_stage | 25 | furthest tactic (Exfiltration=0.95) | 0.95 | **23.8** | reached 'Exfiltration' stage |
| kill_chain_progression | 15 | min(n_tactics/5, 1) → 6/5 caps at 1 | 1.0 | **15.0** | 6 distinct attack stages correlated |
| detection_confidence | 15 | max alert confidence (0.90) | 0.90 | **13.5** | detection confidence 90% |
| corroboration | 10 | log-scaled alert count + named family | — | **9.0** | 6 alerts, named threat family |
| blast_radius | 15 | log-scaled distinct assets (4) | — | **6.8** | 4 assets affected |
| | | | **Total** | **88.1** | → **P1** (≥75) |

**Compliance overlay** (separate, does NOT touch the score): db-prod-01 is `PII_HIGH`, so
the P1 also shows **DPDP up to ₹250 Cr + CERT-In + GDPR** obligations with live statutory
clocks. Say: "the risk score is impact; the regulatory clock is a second, independent lens."

### The rest of the queue (proves it discriminates, not just flags everything)
- **#2 P2 53.2** — CredentialAccess on srv-app-07 (server): RDP brute force (Suricata) +
  successful login (Entra ID). 2 alerts stitched → escalated above single alerts, but no
  crown jewel and stops at credential access → P2, not P1.
- **#3–#5 P3** — single isolated alerts (C2 DNS lookup / EICAR test file / port scan) on
  workstations. No chain, low asset value → correctly parked at the bottom.

---

## PART 4 — COMPLETE PANEL Q&A

### On the attack chain (the new feature)

**Q: "Do you turn low-level alerts into a full attack chain?"**
**Yes — defensive attack-chain reconstruction.** Correlation stitches individually-minor
alerts that share entities within a time window into one multi-stage incident, and the
kill-chain-progression factor escalates the chain above isolated alerts. The P1 is the
proof: six low/medium alerts from three different tools become one P1 (88.1) because they
chain phishing → execution → LSASS credential dump → lateral move → staging → exfiltration
onto a crown-jewel database. *[Point at the timeline on screen.]*

**Q: "Is that the same as predicting an exploit path from vulnerabilities?"**
No — be precise here. We chain **alerts that already fired** into an attack narrative and
prioritise by impact. That is *detection-side* reconstruction. Predicting exploit paths
from raw vulnerabilities + AD topology is offensive attack-graph work (BloodHound
territory) — that is on our roadmap, not a claim we make today. Never say "we chain
vulnerabilities into exploits."

**Q: "How do you correlate the alerts into one incident?"**
Union-find (disjoint-set). We index every alert by the entities it touches (host, user,
IP). For each entity, alerts within a **60-minute** window of a neighbour are unioned.
Transitive unions merge the whole chain: the phishing alert and the exfil alert never share
a timestamp, but they're linked through `host:ws-042` → `host:db-prod-01`. It's O(n·α(n)),
deterministic, and needs no training.

**Q: "How do you know the order of the chain — how do you reconstruct it?"**
We keep every correlated alert's timestamp and sort the members chronologically. The
displayed sequence is the real firing order across all tools, so the analyst reads the
intrusion as a story: entry → execution → credentials → movement → collection → exfil.

**Q: "Which tools / data sources does it work with?"**
Multi-source detections, not raw packets: **EDR (CrowdStrike), NDR (Zeek), IDS/IPS
(Suricata), DLP (Purview), Identity (Entra ID), DNS security (Umbrella)** in the demo. The
schema is vendor-neutral — any detection with an entity, a timestamp and an ATT&CK tactic
plugs in. For scale we also validate on Microsoft's **GUIDE** dataset (9,980 real incidents).

### On the scoring / prioritisation

**Q: "How is the risk score computed? Is it a black box / ML model?"**
No — it's a deterministic weighted sum of **six impact factors**, each with a visible
sub-score and a plain-English reason: asset criticality, kill-chain stage, kill-chain
progression, blast radius, detection confidence, corroboration. Zero LLM calls in the
scoring path. Every rank is auditable — that is exactly what E1 asks for and what a
black-box XGBoost/SHAP classifier can't give you cleanly.

**Q: "Aren't your weights just made up?"**
Two profiles. The **hand profile** is transparent and tunable — the knob a SOC calibrates.
The **calibrated profile** is learned by non-negative least squares (NNLS) against real
Microsoft analyst queue rankings on held-out orgs — no hand-tuning, still interpretable
(it's just weights). It confirmed analysts prioritise by **asset value (43.2) + attack
progression (31.7)** over single-tactic severity, and it zeroed detection_confidence
because GUIDE leaves that field empty. We use the hand profile where confidence is real
(curated) and the calibrated one at GUIDE scale.

**Q: "How good is it — do you have evidence?"**
On 3,000 held-out real incidents our transparent scorer reproduces Microsoft analyst
priority ordering at **NDCG 0.896** (strong top-of-queue agreement), with a **13.2×**
alert→incident reduction, in ~17s over a 1GB stream at flat memory. And unlike the
black-box baselines, every ranking carries its rationale.

**Q: "Why is incident #2 a P2 and not a P1, if it's also a chain?"**
Because impact is graded, not binary. #2 chains 2 alerts on a *server* (not a crown jewel)
and stops at credential access — it never reaches lateral movement, collection or exfil,
and touches one asset. Lower asset tier + shorter chain + smaller blast radius = 53.2 = P2.
That discrimination is the value: it doesn't flag everything red.

**Q: "What does the analyst actually do with each band?"**
P1 → isolate the asset and open an incident now. P2 → assign this shift. P3 → queue for
review, corroborate first. P4 → auto-close unless new signal corroborates. The
recommendation ships with the score.

### On scope / honesty (protects credibility)

**Q: "Did you build this whole SOC platform?"**
No, and I won't claim that. AegisSOC runs on a real production-grade agentic SOC platform.
**What we built is the missing piece E1 asks for**: the deterministic, explainable,
impact-based risk-triage and attack-chain-reconstruction engine on top of it. The base
platform's triage was LLM-prompt-driven — a black box — and explainability was the gap.

**Q: "What are the limits / what's next?"**
Honest ceiling: on GUIDE the asset context is hashed/anonymised, so Spearman is modest
(0.31) even though top-of-queue NDCG is strong — the curated scenario restores named-asset
context. Detection confidence is dead on GUIDE (empty field). Roadmap: offensive
exploit-path prediction (attack graphs), and a live LLM narration layer (the deterministic
narration carries the demo today; LLM only rephrases, never decides).

**Q: "Does the model ever see the ground-truth label?"**
Never. The analyst grade (TP/BP/FP) and the analyst QueueRank are used only to *measure*
us after the fact — they are never scoring inputs. That's asserted by our validation
invariants and you can see it in the code: `score_incident` takes only the incident.

---

## PART 5 — ONE-LINE VERIFICATION CHEATSHEET
```
PYTHONPATH=$PWD python3 -m core.risk.correlate   # chain correlation self-check
PYTHONPATH=$PWD python3 -m core.risk             # full explained queue, P1 88.1
PYTHONPATH=$PWD python3 -m core.risk.benchmark   # NDCG 0.896 vs real analysts
jq '.curated.queue[0].chain' build/dashboard_data.json   # the 6-step chain JSON
```
