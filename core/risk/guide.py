"""Scalable loader/aggregator for the Microsoft GUIDE dataset.

GUIDE ships one row per *evidence*; an incident is many rows. We stream the CSV
in bounded chunks (never loading the whole file) and fold evidence rows into
per-incident features the scorer consumes. Memory stays flat regardless of file
size — the same shape the platform's Kafka ingestion would feed in production.

ponytail: chunked pandas is the scalable-enough tool here. Swap to Kafka/Spark
only when a single box can't keep up — the aggregation is already streaming.
"""
from __future__ import annotations

import os
import pathlib

import pandas as pd

from core.risk.scoring import Incident

# Dataset location, resolved from this file (survives the drive re-mounting at a
# different /run/media path). Prefer a repo-internal datasets/guide (fresh clone),
# fall back to the sibling aegis-work/datasets/guide (dev layout). Override with
# AEGIS_GUIDE_DIR.
_HERE = pathlib.Path(__file__).resolve()
_CANDIDATES = [_HERE.parents[2] / "datasets" / "guide",   # <repo>/datasets/guide
               _HERE.parents[3] / "datasets" / "guide"]   # aegis-work/datasets/guide
_DEFAULT_GUIDE = next((c for c in _CANDIDATES if c.exists()), _CANDIDATES[0])
DATA_DIR = pathlib.Path(os.environ.get("AEGIS_GUIDE_DIR", str(_DEFAULT_GUIDE)))
TEST_CSV = DATA_DIR / "GUIDE_Test.csv"
TRAIN_CSV = DATA_DIR / "GUIDE_Train.csv"
RANKINGS_CSV = DATA_DIR / "GUIDE_Test_Queue_Rankings.csv"

# Only the columns we actually use — the single biggest memory win on a 1GB CSV.
USECOLS = [
    "OrgId", "IncidentId", "AlertId", "Category", "MitreTechniques", "IncidentGrade",
    "EntityType", "DeviceId", "IpAddress", "Url", "AccountSid", "AccountUpn", "Sha256",
    "ThreatFamily", "Roles", "SuspicionLevel", "LastVerdict",
]

# EntityType/kind -> base asset-criticality tier (0..3). GUIDE entities are
# hashed with no readable asset value, so this is a coarse proxy; the curated
# demo scenario carries the real crown-jewel tiers. Admin-ish Roles bump to 3.
_ENTITY_TIER = {
    "user": 2, "account": 2, "mailbox": 2, "machine": 2, "device": 2, "host": 2,
    "ip": 1, "url": 1, "file": 1, "process": 1,
}
_CONF = {  # textual confidence signals -> 0..1
    "high": 0.9, "medium": 0.6, "moderate": 0.6, "low": 0.3,
    "malicious": 0.95, "suspicious": 0.6, "clean": 0.1, "benign": 0.1,
}
_ADMIN_HINT = ("admin", "domaincontroller", "dc", "server", "privileged")


def _s(v) -> str:
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()


def _entity(row) -> tuple[str, int] | None:
    """Pick this evidence row's asset (key, tier), preferring the specific id."""
    et = _s(row.get("EntityType")).lower()
    roles = _s(row.get("Roles")).lower()
    for kind, col in (("host", "DeviceId"), ("user", "AccountSid"), ("user", "AccountUpn"),
                      ("ip", "IpAddress"), ("url", "Url"), ("file", "Sha256")):
        val = _s(row.get(col))
        if val:
            tier = _ENTITY_TIER.get(kind, 1)
            if et in _ENTITY_TIER:
                tier = max(tier, _ENTITY_TIER[et])
            if any(h in roles for h in _ADMIN_HINT):
                tier = 3
            return f"{kind}:{val}", tier
    return None


def _confidence(row) -> float:
    best = 0.0
    for col in ("SuspicionLevel", "LastVerdict"):
        best = max(best, _CONF.get(_s(row.get(col)).lower(), 0.0))
    return best


class _Agg:
    __slots__ = ("tactics", "techniques", "alerts", "assets", "conf", "family", "grade")

    def __init__(self):
        self.tactics: set[str] = set()
        self.techniques: set[str] = set()
        self.alerts: set[str] = set()
        self.assets: dict[str, int] = {}
        self.conf = 0.0
        self.family = False
        self.grade = ""

    def finalize(self, org: str, inc: str) -> Incident:
        return Incident(
            incident_id=inc, org_id=org,
            tactics=self.tactics, techniques=self.techniques,
            n_alerts=max(len(self.alerts), 1), assets=self.assets or {},
            confidence=self.conf if self.conf else 0.5,  # baseline when GUIDE gives no signal
            threat_family=self.family, grade=self.grade or None,
        )


def load_rankings(path: pathlib.Path = RANKINGS_CSV) -> dict[tuple[str, str], int]:
    df = pd.read_csv(path, dtype=str)
    return {(r.OrgId, r.IncidentId): int(r.QueueRank) for r in df.itertuples(index=False)}


def aggregate_incidents(csv_path: pathlib.Path = TEST_CSV,
                        keep: set[tuple[str, str]] | None = None,
                        chunksize: int = 300_000) -> dict[tuple[str, str], Incident]:
    """Stream `csv_path`, fold evidence -> incidents. If `keep` given, only those
    (OrgId, IncidentId) pairs are aggregated (the rest are dropped per chunk)."""
    keepset = {f"{o}|{i}" for (o, i) in keep} if keep else None
    aggs: dict[str, _Agg] = {}
    rows_seen = 0
    for chunk in pd.read_csv(csv_path, usecols=USECOLS, dtype=str, chunksize=chunksize):
        rows_seen += len(chunk)
        chunk["_k"] = chunk["OrgId"].astype(str) + "|" + chunk["IncidentId"].astype(str)
        if keepset is not None:
            chunk = chunk[chunk["_k"].isin(keepset)]
            if chunk.empty:
                continue
        for row in chunk.to_dict("records"):
            k = row["_k"]
            a = aggs.get(k)
            if a is None:
                a = aggs[k] = _Agg()
            cat = _s(row.get("Category"))
            if cat:
                a.tactics.add(cat)
            mt = _s(row.get("MitreTechniques"))
            if mt:
                a.techniques.update(t for t in mt.replace(",", ";").split(";") if t)
            aid = _s(row.get("AlertId"))
            if aid:
                a.alerts.add(aid)
            ent = _entity(row)
            if ent:
                key, tier = ent
                a.assets[key] = max(a.assets.get(key, 0), tier)
            a.conf = max(a.conf, _confidence(row))
            if _s(row.get("ThreatFamily")):
                a.family = True
            g = _s(row.get("IncidentGrade"))
            if g and not a.grade:
                a.grade = g
    return {tuple(k.split("|", 1)): a.finalize(*k.split("|", 1)) for k, a in aggs.items()}


if __name__ == "__main__":
    import time
    t0 = time.time()
    ranks = load_rankings()
    print(f"ranked incidents: {len(ranks)}")
    incs = aggregate_incidents(keep=set(ranks))
    dt = time.time() - t0
    matched = len(incs)
    total_alerts = sum(i.n_alerts for i in incs.values())
    print(f"aggregated {matched} incidents from {total_alerts} alerts in {dt:.1f}s")
    grades = {}
    for i in incs.values():
        grades[i.grade] = grades.get(i.grade, 0) + 1
    print("grade distribution:", grades)
    print(f"alert->incident reduction: {total_alerts}/{matched} = "
          f"{total_alerts / max(matched,1):.1f}x")
