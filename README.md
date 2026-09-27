# AegisSOC AI

<div align="center">

<img src="clients/web/src/assets/aegis-logo.svg" alt="AegisSOC AI Logo" width="360" />

<p align="center">
  <strong>Intelligent. Autonomous. Resilient.</strong>
</p>

<p align="center">
  <em>An autonomous agentic Security Operations Center (SOC) platform orchestrating 13 specialized AI agents, multi-agent investigation workflows, and 30+ Model Context Protocol (MCP) integrations.</em>
</p>

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](.python-version)
[![Node](https://img.shields.io/badge/Node-18%2B-339933.svg?logo=node.js&logoColor=white)](clients/web/package.json)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](infra/docker/docker-compose.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](services/api/main.py)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript&logoColor=white)](services/agent/package.json)
[![Vite](https://img.shields.io/badge/Vite-5.0%2B-646CFF.svg?logo=vite&logoColor=white)](clients/web/)

</div>

---

## Overview

**AegisSOC AI** is a next-generation, autonomous AI SOC platform designed to stand watch alongside modern security teams. Rather than a closed black-box subscription, AegisSOC AI provides an extensible, auditable, and self-hosted capability:

- **13 Specialized AI Agents**: Autonomous agents for rapid alert triage, in-depth root cause investigation, hypothesis-driven threat hunting, containment execution, and automated executive reporting.
- **Declarative Workflows**: Human-readable, markdown-defined multi-agent playbooks with step-by-step approval gates and dynamic confidence scoring.
- **Open Standard Integrations**: Extensible through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) connecting to SIEMs (Splunk), EDRs (CrowdStrike), threat intelligence providers, sandboxes, and ticketing platforms.
- **Human-in-the-Loop Safeguards**: Dual-band confidence thresholds that execute high-confidence actions autonomously while routing sensitive decisions to human analysts for review.

---

## 13 Specialized AI Agents

Every agent operates with dedicated domain prompts and access to both backend core tools and MCP servers:

| Agent | Role | Thinking Mode | Core Capabilities |
|---|---|---|---|
| **Triage** | Rapid Alert Assessment | Fast | Severity evaluation, false-positive filtering, alert escalation |
| **Investigator** | Root Cause Analysis | Deep | Evidence timeline reconstruction, cross-signal correlation, source attribution |
| **Threat Hunter** | Proactive Threat Hunting | Deep | Hypothesis generation, anomaly detection across 7,200+ detection rules |
| **Correlator** | Multi-Signal Linking | Deep | Attack chain reconstruction, campaign discovery, lateral movement tracking |
| **Responder** | Containment Execution | Fast | NIST IR containment actions, blast radius calculation, confidence-gated approvals |
| **Reporter** | Documentation & Reporting | Balanced | Technical incident dossiers, executive briefings, audit-ready summaries |
| **MITRE Analyst** | ATT&CK Matrix Mapping | Deep | Technique identification, detection coverage scoring, gap analysis |
| **Forensics** | Digital Forensics & Artifacts | Deep | Artifact collection, memory/disk inspection, chain-of-custody tracking |
| **Threat Intel** | IOC Enrichment & Attribution | Deep | Threat actor profiling, IOC scoring, external OSINT correlation |
| **Compliance** | Regulatory Validation | Balanced | Framework checks for NIST CSF, ISO 27001, SOC 2, HIPAA, and GDPR |
| **Malware Analyst** | Malware & Binary Inspection | Deep | Static & dynamic analysis, behavior heuristics, C2 protocol extraction |
| **Network Analyst** | Traffic & Telemetry Analysis | Deep | Protocol anomaly detection, beaconing discovery, network flow inspection |
| **Adjudicator** | Decision & Review Auditing | Balanced | Quality evaluation, response plan auditing, consensus verification |

---

## Multi-Agent Workflows

Workflows are defined as plain Markdown documents in `core/workflows/definitions/`. The orchestration engine executes them deterministically across phases:

```
core/workflows/definitions/
├── incident-response/WORKFLOW.md       # Triage → Investigator → Responder → Reporter
├── full-investigation/WORKFLOW.md      # Investigator → MITRE Analyst → Correlator → Responder → Reporter
├── threat-hunt/WORKFLOW.md             # Threat Hunter → Network Analyst → Malware Analyst → Threat Intel
├── forensic-analysis/WORKFLOW.md       # Forensics → Malware Analyst → Network Analyst → Reporter
├── root-cause-analysis/WORKFLOW.md     # Deep dive into alert provenance and attack vectors
├── cloud-incident/WORKFLOW.md          # Cloud identity, IAM drift, and infrastructure anomalies
└── shadow-adjudication/WORKFLOW.md     # Secondary validation and quality control
```

### Example: Creating a Workflow in Seconds

Workflows use YAML frontmatter with natural language objectives and instructions:

```markdown
---
name: phishing-triage
description: "Triage and investigate phishing reports from user submissions."
trigger_examples:
  - "Run phishing triage on finding f-20260401-abc123"
phases:
  - id: assess
    agent: triage
    name: "Assess the Report"
    tools: [get_finding, list_findings]
    instructions: Extract sender, domain, and URLs. Score severity against known-bad indicators.

  - id: investigate
    agent: investigator
    name: "Investigate Root Cause"
    tools: [get_finding, search_detections]
    instructions: Correlate with detection rules and construct an evidence timeline.

  - id: contain
    agent: responder
    name: "Containment"
    tools: [get_case, update_case]
    approval_required: true
    instructions: Quarantine matching mailbox messages and submit domain blocks.
---
```

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AegisSOC AI Web Console                         │
│             React 18 + Vite + TypeScript (Dashboard & Alerts)          │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTP / REST (:7787)
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend Core                          │
│        Case Management │ Security Detections │ RBAC & JWT Auth         │
│           Pydantic v2 Config │ BullMQ Job Enqueueing (:6379)           │
└──────────────────┬─────────────────┬─────────────────┬─────────────────┘
                   │                 │                 │
                   ▼                 ▼                 ▼
          ┌────────────────┐ ┌───────────────┐ ┌───────────────┐
          │  PostgreSQL 16 │ │    Redis 7    │ │    Bifrost    │
          │ Relational DB  │ │ Queue & Leases│ │  LLM Gateway  │
          │   (Port 5432)  │ │  (Port 6379)  │ │  (Port 8080)  │
          └────────────────┘ └───────┬───────┘ └───────┬───────┘
                                     │                 │
                                     ▼                 ▼
          ┌────────────────────────────────────────────────────┐
          │               TypeScript Agent Layer               │
          │  Worker (Port :6990) │ HTTP Chat Server (:6989)    │
          │  Harness Factory │ OpenAiSurface │ MCP Dispatcher  │
          └──────────────────────────┬─────────────────────────┘
                                     │
                                     ▼
          ┌────────────────────────────────────────────────────┐
          │              MCP Integration Servers               │
          │  Splunk │ CrowdStrike │ VirusTotal │ Shodan │ Jira │
          └────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Clone the Repository

```bash
git clone git@github.com:SmitNfsu/AegisSOC-AI.git
cd AegisSOC-AI
```

### 2. Environment Configuration

Copy the example environment configuration:

```bash
cp env.example .env
```

Generate a secure token for agent-backend communication:

```bash
# Generate and set AGENT_INTERNAL_TOKEN in .env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. Start the Stack

Ensure **Docker Desktop** is running, then launch the full platform:

```bash
./start.sh
```

The startup script handles all provisioning:
1. Provisions an isolated Python 3.12 virtual environment via `uv`.
2. Starts containerized infrastructure: **PostgreSQL**, **Redis**, and the **Bifrost LLM Gateway**.
3. Initializes database schema and reference data.
4. Builds and serves the **AegisSOC AI** web client.
5. Launches the backend API and agent workers.

---

## Access & Endpoints

Once started, the following services are available locally:

| Service | URL | Description |
|---|---|---|
| **Web Console** | [http://localhost:7788](http://localhost:7788) | Rebranded AegisSOC AI Analyst Dashboard |
| **REST API** | [http://localhost:7787](http://localhost:7787) | FastAPI Backend (`/api/health`, `/api/auth`) |
| **Interactive API Docs** | [http://localhost:7787/docs](http://localhost:7787/docs) | Swagger UI & OpenAPI Specification |
| **Agent Worker Health** | [http://localhost:6990/healthz](http://localhost:6990/healthz) | BullMQ durable run worker probe |
| **Agent Chat Server** | [http://localhost:6989/healthz](http://localhost:6989/healthz) | Synchronous chat turn handler |
| **Bifrost Gateway** | [http://localhost:8080](http://localhost:8080) | Multi-provider LLM routing gateway |

---

## Integrations (Model Context Protocol)

AegisSOC AI connects agents to industry-standard tools via MCP:

- **SIEM**: Splunk (Natural language SPL queries, host/user drilldowns)
- **EDR / XDR**: CrowdStrike Falcon (Host containment, sensor telemetry)
- **Threat Intel**: VirusTotal, Shodan, AlienVault OTX, MISP
- **Sandbox Analysis**: Hybrid Analysis, Joe Sandbox, ANY.RUN
- **Timeline & Forensics**: Timesketch forensic timeline correlation
- **Detection Engineering**: 7,200+ detection rules across Sigma, Splunk, Elastic, and KQL

Add custom integrations easily using the MCP specification or by extending vendor slices under `core/integrations/`.

---

## Stopping the Services

To shut down the native processes and containers:

```bash
# Stop native processes (Docker remains running)
./shutdown_all.sh

# Stop native processes and Docker containers
./shutdown_all.sh -d

# Full teardown (stops and removes containers and volume data)
./shutdown_all.sh -d --full
```

---

## Contributing

Contributions, bug reports, and suggestions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-capability`)
3. Commit your changes (`git commit -m "feat: add capability"`)
4. Push to the branch (`git push origin feature/new-capability`)
5. Open a Pull Request

---

## License

This project is licensed under the [Apache 2.0 License](LICENSE).
