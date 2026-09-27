"""Self-check for the risk scorer: it must rank a real multi-stage attack on a
crown-jewel asset far above benign recon, and every rank must carry a reason.
Run: python -m core.risk.test_scoring  (or pytest)."""
from core.risk.scoring import Incident, score_incident, _band


def _p1_crown_jewel_exfil() -> Incident:
    # phishing -> cred access -> lateral -> exfil, landing on the prod DB.
    return Incident(
        incident_id="demo-critical",
        tactics={"InitialAccess", "CredentialAccess", "LateralMovement", "Exfiltration"},
        n_alerts=7,
        assets={"host:db-prod-01": 3, "host:ws-042": 1, "user:svc-backup": 2, "ip:203.0.113.9": 0},
        confidence=0.9,
        threat_family=True,
    )


def _p4_benign_recon() -> Incident:
    # a single low-confidence port-scan hit on one workstation.
    return Incident(
        incident_id="demo-noise",
        tactics={"Discovery"},
        n_alerts=1,
        assets={"host:ws-311": 1},
        confidence=0.2,
    )


def test_critical_outranks_noise():
    crit = score_incident(_p1_crown_jewel_exfil())
    noise = score_incident(_p4_benign_recon())
    assert crit["score"] > noise["score"], (crit["score"], noise["score"])
    assert crit["band"] == "P1", crit
    assert noise["band"] in ("P3", "P4"), noise


def test_every_incident_is_explained():
    for inc in (_p1_crown_jewel_exfil(), _p4_benign_recon()):
        out = score_incident(inc)
        assert out["why"], "an incident with no explanation defeats the whole point"
        assert all(isinstance(w, str) and w for w in out["why"])


def test_reaching_a_later_stage_raises_score():
    base = _p4_benign_recon()
    escalated = Incident(**{**base.__dict__, "tactics": base.tactics | {"Impact"}})
    assert score_incident(escalated)["score"] > score_incident(base)["score"]


def test_bands_are_ordered():
    assert _band(90) == "P1" and _band(60) == "P2" and _band(30) == "P3" and _band(5) == "P4"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    c = score_incident(_p1_crown_jewel_exfil())
    n = score_incident(_p4_benign_recon())
    print(f"CRITICAL  {c['band']}  score={c['score']}")
    for w in c["why"]:
        print(f"    - {w}")
    print(f"NOISE     {n['band']}  score={n['score']}")
    for w in n["why"]:
        print(f"    - {w}")
    print("\nall assertions passed.")
