# AegisSOC AI: Architectural Deep Dive & SOC Tier (L1, L2, L3) Capabilities

---

## 1. Executive Summary

**AegisSOC AI** is an autonomous, agentic Security Operations Center (SOC) platform designed to operate as a self-hosted, 24/7 AI-powered SOC team. Unlike conventional SIEMs or SOAR platforms that rely on rigid static scripts, AegisSOC AI combines:

- **13 Specialized Autonomous AI Agents** (each with dedicated operational roles, security boundaries, and domain methodologies).
- **Multi-Agent Orchestration & Declarative Workflows** (e.g., Triage → Investigator → Responder → Reporter).
- **Model Context Protocol (MCP)** integrations connecting AI agents to enterprise SIEMs, EDRs, Threat Intelligence feeds, and sandboxes.
- **Enterprise LLM Gateway (Bifrost)** with multi-provider routing, budget enforcement, and private-network proxy bridges.
- **Dual-Band Human-in-the-Loop Approval Gates** ensuring high-confidence actions execute autonomously while sensitive containment actions are routed to security analysts for review.

---

## 2. Does AegisSOC AI Solve SOC Levels L1, L2, and L3?

### **Short Answer:**
**YES. AegisSOC AI is purpose-built to address all three tiers of a Modern SOC (Tier 1, Tier 2, and Tier 3), transforming the traditional human-heavy operational hierarchy into an AI-augmented, autonomous defense pipeline.**

---

### Detailed Tier-by-Tier Mapping

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AegisSOC AI Coverage                              │
├───────────────────────┬─────────────────────────────┬───────────────────────┤
│    Tier 1 (L1 SOC)    │       Tier 2 (L2 SOC)       │    Tier 3 (L3 SOC)    │
│  Triage & Monitoring  │ Incident Investigation & IR │ Threat Hunt & Forensic│
├───────────────────────┼─────────────────────────────┼───────────────────────┤
│ • Automated Ingestion │ • Root-Cause Analysis       │ • Hypothesis Hunting  │
│ • Alert Deduplication │ • Attack Timeline Building  │ • MITRE Matrix Mapping│
│ • False Positive Drop │ • Lateral Movement Tracking │ • Deep Forensic Memory│
│ • IOC Fast Reputation │ • Blast Radius Evaluation   │ • 7,200+ Sigma Rules  │
│ • Auto-Containment    │ • Guided Containment Plan   │ • Board Risk Briefings│
│ • 24/7 Fast Response  │ • Analyst Approval Gates    │ • Regulatory Audit    │
└───────────────────────┴─────────────────────────────┴───────────────────────┘
```

---

### **Tier 1 (L1) — Alert Monitoring, Triage & First Response**

#### Traditional L1 Problem:
L1 analysts face severe alert fatigue, sorting through thousands of alerts per day from EDRs, firewalls, and SIEMs. Most alerts are false positives or low-fidelity noise. High turnover, missed critical alerts, and delayed mean-time-to-triage (MTTT) are standard problems.

#### How AegisSOC AI Solves L1:
1. **Automated Continuous Ingestion**:
   - Ingests raw security alerts via Syslog, Webhooks, Kafka, or REST API into the PostgreSQL findings repository.
2. **Autonomous Triage Agent (`triage`)**:
   - Evaluates the alert context, assesses severity, and normalizes evidence into structured findings (`f-YYYYMMDD-XXXXXXXX`).
   - Cross-references internal asset history and distilled memory to identify benign anomalies and discard known false positives.
3. **Automated IOC Reputation & Threat Intel (`threat_intel`)**:
   - Instantly queries VirusTotal, Shodan, and AlienVault OTX via MCP tools to score IP, domain, and hash observables.
4. **Auto-Responder Agent (`auto_responder`)**:
   - If an alert has clear, unambiguous malicious evidence exceeding the `$auto_approve` threshold (e.g. ransomware beacon or credential dumper), it immediately isolates the host or blocks the IP without waiting for human intervention.
5. **Outcome**:
   - **90%+ reduction in manual alert fatigue**.
   - Near-zero MTTT (seconds instead of minutes/hours).

---

### **Tier 2 (L2) — Deep Incident Investigation & Coordinated Response**

#### Traditional L2 Problem:
When an incident is confirmed, L2 analysts must correlate events across endpoints, network traffic, identity providers, and cloud logs to reconstruct the full attack story and execute safe containment.

#### How AegisSOC AI Solves L2:
1. **Investigator Agent (`investigator`)**:
   - Performs automated root-cause analysis (RCA). Reconstructs chronological attack timelines showing patient zero, entry vector, and affected user accounts.
2. **Network Analyst Agent (`network_analyst`)**:
   - Analyzes network telemetry, flow volumes, protocol anomalies (DNS tunneling, suspicious HTTP/S beacons), and C2 traffic patterns.
3. **Malware Analyst Agent (`malware_analyst`)**:
   - Evaluates suspicious binaries, scripts, and command-line executions (e.g., PowerShell encoded commands, process injection).
4. **Correlator Agent (`correlator`)**:
   - Discovers related findings sharing common hosts, users, or IOCs to map multi-stage lateral movement.
5. **Responder Agent (`responder`)**:
   - Generates surgical containment plans (quarantining endpoints, revoking authenticated user tokens, blocking C2 domain at Cloudflare Gateway).
6. **Human-in-the-Loop Approval System**:
   - Containment plans that fall below the `$auto_approve` threshold are submitted as **Approval Actions** with full evidence and rationale. The human analyst reviews and clicks **Approve** in the web console.
7. **Outcome**:
   - Rapid Mean-Time-to-Remediate (MTTR).
   - Prevents attacker dwell time and halts lateral movement.

---

### **Tier 3 (L3) — Proactive Threat Hunting, Digital Forensics & Security Engineering**

#### Traditional L3 Problem:
L3 analysts are the most experienced and expensive security engineers. They hunt for stealthy Advanced Persistent Threats (APTs) that never triggered an alert, conduct disk/memory forensics, and audit MITRE ATT&CK coverage.

#### How AegisSOC AI Solves L3:
1. **Threat Hunter Agent (`threat_hunter`)**:
   - Operates hypothesis-driven threat hunts (e.g., *"Hunt for scheduled tasks or WMI subscriptions created within the last 7 days"*).
   - Leverages **7,200+ built-in detection rules** across Sigma, Splunk SPL, Elastic, and Microsoft KQL.
2. **MITRE ATT&CK Analyst Agent (`mitre_analyst`)**:
   - Dynamically maps attack techniques to the MITRE ATT&CK matrix.
   - Calculates technique rollups and coverage gaps to guide detection engineering.
3. **Forensic Specialist Agent (`forensics`)**:
   - Analyzes memory and disk artifacts, file modification timestamps, and maintains digital chain-of-custody tracking.
4. **Compliance Analyst Agent (`compliance`)**:
   - Evaluates incident impact against compliance standards: **NIST CSF, ISO 27001, SOC 2, HIPAA, and GDPR**.
5. **Reporter Agent (`reporter`)**:
   - Automatically writes comprehensive incident investigation dossiers and generates executive **Board Briefs** in clean business language.
6. **Multi-Agent Workflows**:
   - Executes complex cross-functional workflows like `threat-hunt`, `forensic-analysis`, `root-cause-analysis`, and `shadow-adjudication`.

---

## 3. Platform Architecture & Components

```
┌────────────────────────────────────────────────────────────────────────────┐
│                          AegisSOC AI Web Console                           │
│     React 18 + Vite + TypeScript (Dashboard, Cases, Chat, Approvals)       │
│                             (Port 7788)                                    │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │ HTTP / WebSockets (:7787)
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                            FastAPI Backend Core                            │
│   Auth & RBAC │ Findings API │ Case Management │ LLM Router │ Integrations │
│                             (Port 7787)                                    │
└──────────────┬──────────────────────┬──────────────────────┬───────────────┘
               │                      │                      │
               ▼                      ▼                      ▼
      ┌────────────────┐     ┌────────────────┐     ┌─────────────────┐
      │  PostgreSQL 16 │     │    Redis 7     │     │     Bifrost     │
      │  Primary Store │     │ Job Queue &    │     │   LLM Gateway   │
      │  (Port 5432)   │     │ Leases (:6379) │     │   (Port 8080)   │
      └────────────────┘     └────────┬───────┘     └────────┬────────┘
                                      │                      │
                                      ▼                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           TypeScript Agent Layer                           │
│    Durable Worker (Port 6990) │ Synchronous Interactive Chat (Port 6989)   │
│           Harness Factory │ Prompt Renderer │ Workflow Runner              │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
                                      ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                    Model Context Protocol (MCP) Servers                    │
│   CrowdStrike EDR │ Splunk SIEM │ VirusTotal │ Shodan │ Timesketch │ Jira  │
└────────────────────────────────────────────────────────────────────────────┘
```

### Component Breakdown:
1. **Frontend Web Console (Port 7788)**:
   - Modern dark-mode interface with live Findings telemetry, ATT&CK Matrix, Case Timelines, Auto Ops, and the **Ask AegisSOC** conversational AI copilot.
2. **FastAPI Backend (Port 7787)**:
   - Core orchestrator providing REST endpoints, authentication (JWT with HttpOnly cookies and CSRF protection), case and finding models, and the local AI bridge proxy.
3. **Bifrost LLM Gateway (Port 8080)**:
   - Enterprise AI proxy handling model routing, cost tracking, token budgeting, and fallback management across OpenAI, Anthropic, Ollama, and custom models.
4. **TypeScript Agent Layer (Ports 6990 & 6989)**:
   - The autonomous reasoning engine executing BullMQ multi-agent background jobs and live chat sessions.
5. **Model Context Protocol (MCP)**:
   - Standardized interface allowing AI agents to query security tools safely and deterministically without hardcoding API integrations.

---

## 4. The 13 Built-in AegisSOC AI Agents

| # | Agent Name | ID | Thinking Mode | Primary Specialization |
|---|---|---|---|---|
| 1 | **Triage Agent** | `triage` | Fast | Ingests alerts, filters false positives, and assigns initial risk scores. |
| 2 | **Investigation Agent** | `investigator` | Deep | Gathers multi-source evidence, traces provenance, and maps timelines. |
| 3 | **Threat Hunter** | `threat_hunter` | Deep | Proactively hunts hypotheses across 7,200+ Sigma/Splunk detection rules. |
| 4 | **Signal Correlator** | `correlator` | Deep | Identifies common pivots across hosts, identities, and attack campaigns. |
| 5 | **Response Agent** | `responder` | Fast | Generates NIST SP 800-61 containment, eradication, and recovery plans. |
| 6 | **Reporting Agent** | `reporter` | Balanced | Compiles technical incident reports and board-level risk briefs. |
| 7 | **MITRE ATT&CK Analyst** | `mitre_analyst` | Deep | Maps techniques to the matrix, scores defense coverage, and finds gaps. |
| 8 | **Forensic Specialist** | `forensics` | Deep | Inspects endpoint artifacts, memory, disk snapshots, and preserves evidence. |
| 9 | **Threat Intel Agent** | `threat_intel` | Deep | Profiles adversaries, enriches indicators (IP/domain/hash), and OSINT. |
| 10 | **Compliance Analyst** | `compliance` | Balanced | Validates regulatory obligations (NIST CSF, ISO 27001, SOC 2, HIPAA, GDPR). |
| 11 | **Malware Analyst** | `malware_analyst` | Deep | Analyzes malicious binaries, script macros, and identifies C2 protocols. |
| 12 | **Network Analyst** | `network_analyst` | Deep | Evaluates network traffic patterns, beaconing, flow anomalies, and exfiltration. |
| 13 | **Auto-Response Agent** | `auto_responder` | Fast | Autonomous containment for verified high-confidence threats. |

---

## 5. Security & Safety Architecture

- **Prompt-Injection Defense**:
  - Tool outputs, alerts, and external data are enclosed within strict `<aegis:tool_result>` security boundaries. Agents treat tool outputs as untrusted evidence rather than executable instructions.
- **Audit Trails**:
  - Every agent action, decision, prompt, token count, and reasoning step is recorded in `agent_events`, `agent_directives`, and the Bifrost interaction log for compliance and accountability.
- **Zero Plaintext Secrets**:
  - All API keys (OpenAI, Anthropic, Alias Robotics, CrowdStrike, Splunk) are encrypted in the local secrets vault (`~/.aegis/secrets.enc`) and dynamically passed at runtime.

---

## 6. Summary Matrix: Traditional SOC vs. AegisSOC AI

| Feature / Capability | Traditional SOC | AegisSOC AI |
|---|---|---|
| **Alert Triage (L1)** | Manual, repetitive, alert fatigue (15–45 min/alert) | Autonomous AI Triage (< 5 seconds/alert) |
| **False Positive Filtering** | Rule exceptions written manually | In-context reasoning and memory recognition |
| **Investigation (L2)** | Manual queries in 5+ separate dashboards | Automated cross-tool correlation via MCP |
| **Containment Action** | Manual ticket escalation or static SOAR playbook | AI-generated plan with dual-band human approval |
| **Threat Hunting (L3)** | Ad-hoc, requires senior engineers | Proactive hypothesis hunting with 7,200+ rules |
| **MITRE Mapping** | Done after incident closure in spreadsheets | Dynamic, real-time ATT&CK matrix scoring |
| **Incident Reporting** | Hours spent assembling Word/PDF reports | Auto-generated audit dossiers and board briefs |
| **Availability** | Requires 24/7 rotating human shifts | Continuous 24/7 autonomous daemon |
