"""Regulatory-exposure overlay for incidents — the GRC half of triage.

Deterministic (no LLM): given an incident's affected data classes, kill-chain
stage, and detection time, it derives which statutory obligations attach, the
live breach clocks, and the penalty exposure — so the SOC analyst and the DPO
see the same #1 incident. It never touches the 6-factor risk score; it is a
parallel dimension surfaced beside it.

Facts (verified 2026): CERT-In Directions 2022 — 6h reporting, in force since
Jun 2022. DPDP Act 2023 §8(6) + DPDP Rules 2025 (notified Nov 2025, breach
provisions phasing in ~2027) — intimate the Data Protection Board of India +
affected Data Principals "without delay", then a detailed report to the Board
within 72h; penalties up to ₹250 Cr (failure of reasonable safeguards) / ₹200 Cr
(failure to notify). GDPR Art.33/34 — 72h to the DPA; up to €20M or 4% turnover.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from core.risk.scoring import Incident, _norm_tactic

# tactics that mean data was (likely) compromised, not merely accessed
_BREACH_STAGES = {"collection", "exfiltration", "impact"}
# tactics that make it a reportable cyber incident at all (a real intrusion)
_INTRUSION_STAGES = {"initialaccess", "execution", "persistence", "privilegeescalation",
                     "credentialaccess", "lateralmovement", "commandandcontrol",
                     "collection", "exfiltration", "impact", "malware"}


@dataclass
class Clock:
    label: str          # e.g. "6h to CERT-In"
    hours: float        # statutory window
    remaining_h: float  # hours left (may be negative = overdue)
    status: str         # "green" | "amber" | "red" | "overdue"


@dataclass
class Obligation:
    framework: str          # "CERT-In Directions 2022"
    regulator: str
    jurisdiction: str
    duty: str               # what must be done
    clock: Clock | None
    penalty: str
    in_force: str           # "in force" | "phasing in (~2027)" | ...


@dataclass
class Assessment:
    pii_exposed: bool
    breach: bool                       # data compromised, not just accessed
    reportable: bool                   # a reportable cyber incident
    data_classes: list[str]
    obligations: list[Obligation] = field(default_factory=list)
    penalty_headline: str = ""
    notice_required: bool = False
    summary: str = ""


def _clock(label: str, window_h: float, detected_at: float | None, now: float) -> Clock | None:
    if detected_at is None:
        return None
    remaining = window_h - (now - detected_at) / 3600
    frac = remaining / window_h
    status = ("overdue" if remaining < 0 else "red" if frac <= 1 / 6
              else "amber" if frac <= 1 / 2 else "green")
    return Clock(label=label, hours=window_h, remaining_h=round(remaining, 2), status=status)


def assess(inc: Incident, now: float | None = None) -> Assessment:
    now = time.time() if now is None else now
    tactics = {_norm_tactic(t) for t in inc.tactics}
    dc = {c.upper() for c in inc.data_classes}
    pii = any(c in dc for c in ("PII_HIGH", "PII"))
    financial = "FINANCIAL_CDE" in dc
    ephi = "EPHI" in dc
    breach = pii and bool(tactics & _BREACH_STAGES)
    reportable = bool(tactics & _INTRUSION_STAGES)

    obs: list[Obligation] = []

    # CERT-In — any reportable cyber incident on Indian infra. Live today.
    if reportable:
        obs.append(Obligation(
            framework="CERT-In Directions 2022", regulator="CERT-In (MeitY)",
            jurisdiction="India",
            duty="Report the incident to CERT-In within 6 hours of becoming aware (Annexure I).",
            clock=_clock("CERT-In report", 6, inc.detected_at, now),
            penalty="Non-compliance punishable under IT Act §70B(7)",
            in_force="in force (since Jun 2022)"))

    # DPDP — personal-data breach.
    if breach:
        obs.append(Obligation(
            framework="DPDP Act 2023 §8(6) · Rules 2025", regulator="Data Protection Board of India",
            jurisdiction="India",
            duty="Intimate the Board + affected Data Principals without delay; detailed report to the Board within 72h.",
            clock=_clock("DPDP Board report", 72, inc.detected_at, now),
            penalty="Up to ₹250 Cr (safeguards) / ₹200 Cr (notification)",
            in_force="Rules 2025 notified; breach provisions phasing in (~2027)"))
        # GDPR runs in parallel where EU data subjects are involved.
        obs.append(Obligation(
            framework="GDPR Art. 33/34", regulator="EU Supervisory Authority",
            jurisdiction="EU (if EU data subjects)",
            duty="Notify the DPA within 72h; notify data subjects if high risk.",
            clock=_clock("GDPR DPA notice", 72, inc.detected_at, now),
            penalty="Up to €20M or 4% of global turnover",
            in_force="in force"))

    if financial and reportable:
        obs.append(Obligation(
            framework="PCI-DSS v4.0 · RBI", regulator="Card schemes / RBI (India)",
            jurisdiction="Global / India",
            duty="Invoke IR (Req 12.10); notify acquirer/card brands and RBI per directions.",
            clock=None, penalty="Fines + loss of card-processing privileges",
            in_force="in force"))
    if ephi and breach:
        obs.append(Obligation(
            framework="HIPAA Breach Notification Rule", regulator="US HHS OCR",
            jurisdiction="US", duty="Notify affected individuals and HHS (≤60 days).",
            clock=_clock("HIPAA notice", 60 * 24, inc.detected_at, now),
            penalty="Tiered civil penalties up to $1.9M/yr per violation",
            in_force="in force"))

    # headline penalty = the largest single exposure that applies
    penalty_headline = ("up to ₹250 Cr (DPDP)" if breach
                        else "IT Act §70B (CERT-In)" if reportable else "—")
    notice_required = breach
    if breach:
        summary = (f"Personal-data breach ({', '.join(sorted(dc)) or 'PII'}). "
                   f"DPDP + CERT-In obligations triggered — statutory clocks running.")
    elif reportable:
        summary = "Reportable cyber incident — CERT-In 6-hour clock running."
    else:
        summary = "No statutory reporting obligation identified."

    return Assessment(pii_exposed=pii, breach=breach, reportable=reportable,
                      data_classes=sorted(dc), obligations=obs,
                      penalty_headline=penalty_headline, notice_required=notice_required,
                      summary=summary)


def notice(inc: Incident, framework: str = "dpdp") -> str:
    """Deterministic draft of a statutory breach notice, filled from incident facts.
    A template preview — the 'one-click filing' without an LLM."""
    assets = ", ".join(sorted(inc.assets)) or "unknown assets"
    techs = ", ".join(sorted(inc.techniques)) or "—"
    dc = ", ".join(sorted(c.upper() for c in inc.data_classes)) or "personal data"
    if framework == "certin":
        return (
            "CERT-In Incident Report (Annexure I) — DRAFT\n"
            f"• Incident: {max(inc.tactics, default='activity')} across {inc.n_alerts} correlated alerts\n"
            f"• Affected systems: {assets}\n"
            f"• Techniques (MITRE ATT&CK): {techs}\n"
            "• Category: Unauthorised access / data exfiltration (Annexure I)\n"
            "• Reporting window: within 6 hours of awareness\n"
            "• Mitigation: containment initiated; see incident timeline for evidence hashes.")
    return (
        "DPDP Act 2023 §8(6) — Personal Data Breach Intimation (DRAFT)\n"
        "• To: Data Protection Board of India + affected Data Principals\n"
        f"• Nature of breach: unauthorised access & exfiltration affecting {dc}\n"
        f"• Affected assets: {assets}\n"
        f"• Techniques observed: {techs}\n"
        "• Safeguards affected; remedial action: containment + credential reset initiated\n"
        "• Timeline: intimate without delay; detailed report to the Board within 72 hours.")


def demo() -> None:
    # a PII exfiltration detected 90 min ago must trigger DPDP+CERT-In with live clocks
    now = 1_000_000.0
    inc = Incident("t", tactics={"InitialAccess", "Exfiltration"},
                   assets={"host:db-prod-01": 3}, data_classes={"PII_HIGH"},
                   detected_at=now - 90 * 60)
    a = assess(inc, now=now)
    assert a.breach and a.notice_required, a
    fw = {o.framework.split()[0] for o in a.obligations}
    assert "CERT-In" in fw and "DPDP" in fw, fw
    certin = next(o for o in a.obligations if o.framework.startswith("CERT-In"))
    assert certin.clock and 4.4 < certin.clock.remaining_h < 4.6, certin.clock
    # an access-only incident with no data class: reportable, but no breach notice
    inc2 = Incident("t2", tactics={"Discovery"}, assets={"host:ws-1": 1}, detected_at=now)
    a2 = assess(inc2, now=now)
    assert not a2.breach and not a2.reportable, a2
    print("compliance self-check passed:",
          f"{len(a.obligations)} obligations, CERT-In {certin.clock.remaining_h}h left,",
          f"penalty {a.penalty_headline}")


if __name__ == "__main__":
    demo()
