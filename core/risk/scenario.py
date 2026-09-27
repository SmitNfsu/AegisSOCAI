"""A curated, human-readable alert stream for the demo.

GUIDE proves the engine works at scale on real data but hashes away asset names;
this scenario restores that context — named crown-jewel assets and a real
multi-stage attack chain hidden among benign noise — so the prioritised queue
tells a story an analyst (or judge) can follow end to end.

Asset criticality tiers: 3=crown jewel (prod DB, domain controller),
2=server, 1=workstation, 0=external/unknown.
"""
from __future__ import annotations

import time

# The chain "happened" starting ~95 min ago, so the statutory clocks read live
# in the demo (CERT-In 6h shows ~4.5h left, DPDP 72h shows ~70h left).
T = time.time() - 95 * 60

# Data-sensitivity of named assets — what turns a technical incident into a
# regulatory one. In production this comes from the asset inventory's
# data-classification tags; here it is the demo's crown-jewel labelling.
ASSET_DATA_CLASS = {
    "host:db-prod-01": "PII_HIGH",      # customer records: Aadhaar, PAN, email
    "host:srv-app-07": "FINANCIAL_CDE",  # payment/app server
}


def alerts() -> list[dict]:
    a = []

    # --- Incident A: "Operation Ledger" — full chain onto the prod database (P1)
    a += [
        {"alert_id": "EDR-5521", "ts": T + 0, "source": "CrowdStrike",
         "title": "Phishing attachment opened", "tactic": "InitialAccess",
         "entities": [("user:j.doe", 2), ("host:ws-042", 1)], "confidence": 0.7},
        {"alert_id": "EDR-5522", "ts": T + 240, "source": "CrowdStrike",
         "title": "Malicious macro spawned PowerShell", "tactic": "Execution",
         "technique": "T1059.001", "entities": [("host:ws-042", 1)], "confidence": 0.82,
         "threat_family": True},
        {"alert_id": "EDR-5530", "ts": T + 900, "source": "CrowdStrike",
         "title": "LSASS credential access", "tactic": "CredentialAccess",
         "technique": "T1003.001", "entities": [("host:ws-042", 1), ("user:j.doe", 2)],
         "confidence": 0.88},
        {"alert_id": "NET-8801", "ts": T + 1500, "source": "Zeek",
         "title": "SMB lateral movement to DB server", "tactic": "LateralMovement",
         "entities": [("host:ws-042", 1), ("host:db-prod-01", 3)], "confidence": 0.8},
        {"alert_id": "DLP-1207", "ts": T + 2100, "source": "Purview",
         "title": "Bulk records staged from database", "tactic": "Collection",
         "entities": [("host:db-prod-01", 3)], "confidence": 0.79},
        {"alert_id": "NET-8899", "ts": T + 2700, "source": "Zeek",
         "title": "Large outbound transfer to rare ASN", "tactic": "Exfiltration",
         "technique": "T1048.003", "entities": [("host:db-prod-01", 3), ("ip:203.0.113.9", 0)],
         "confidence": 0.9, "threat_family": True},
    ]

    # --- Incident B: brute force + suspicious login on an app server (P2/P3)
    a += [
        {"alert_id": "IDS-3310", "ts": T + 300, "source": "Suricata",
         "title": "RDP brute force", "tactic": "CredentialAccess",
         "entities": [("host:srv-app-07", 2), ("ip:198.51.100.4", 0)], "confidence": 0.6},
        {"alert_id": "AUTH-77", "ts": T + 1200, "source": "Entra ID",
         "title": "Successful login after many failures", "tactic": "InitialAccess",
         "entities": [("host:srv-app-07", 2)], "confidence": 0.55},
    ]

    # --- benign / low-priority noise (P3/P4) ---
    a += [
        {"alert_id": "IDS-9002", "ts": T + 60, "source": "Suricata",
         "title": "Internal port scan", "tactic": "Discovery",
         "entities": [("host:ws-311", 1), ("ip:10.0.0.5", 0)], "confidence": 0.3},
        {"alert_id": "EDR-6100", "ts": T + 500, "source": "CrowdStrike",
         "title": "EICAR test file quarantined", "tactic": "Malware",
         "entities": [("host:ws-155", 1)], "confidence": 0.35},
        {"alert_id": "DNS-4400", "ts": T + 800, "source": "Umbrella",
         "title": "Lookup to newly-registered domain", "tactic": "CommandAndControl",
         "entities": [("host:ws-208", 1)], "confidence": 0.25},
    ]
    # attach each alert's data-sensitivity from the assets it touches
    for alert in a:
        classes = {ASSET_DATA_CLASS[k] for k, _ in alert["entities"] if k in ASSET_DATA_CLASS}
        if classes:
            alert["data_classes"] = sorted(classes)
    return a
