"""Correlate a raw alert stream into incidents.

Two alerts belong to the same incident if they share an entity (host/user/ip/…)
within a time window — the standard SOC heuristic for stitching a multi-stage
attack out of individual detections. Union-find over shared entities does it in
near-linear time.

ponytail: O(alerts) per entity, single box. The platform's Kafka ingestion feeds
the same alert shape at volume; swap to a windowed stream-join only if one node
can't keep the window in memory.
"""
from __future__ import annotations

from collections import defaultdict

from core.risk.scoring import Incident

# An alert is a plain dict:
#   {alert_id, ts (epoch s), tactic, technique?, entities:[(key,tier)],
#    confidence (0..1), threat_family?(bool), title?, source?}


class _UF:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def correlate(alerts: list[dict], window_s: int = 3600) -> list[Incident]:
    uf = _UF(len(alerts))
    by_entity: dict[str, list[int]] = defaultdict(list)
    for i, a in enumerate(alerts):
        for key, _tier in a["entities"]:
            by_entity[key].append(i)
    # link alerts that share an entity and fall within the window of a neighbour
    for idxs in by_entity.values():
        idxs.sort(key=lambda i: alerts[i]["ts"])
        for a_i, b_i in zip(idxs, idxs[1:]):
            if alerts[b_i]["ts"] - alerts[a_i]["ts"] <= window_s:
                uf.union(a_i, b_i)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(alerts)):
        groups[uf.find(i)].append(i)

    incidents = []
    for gi, members in groups.items():
        assets: dict[str, int] = {}
        tactics, techniques, alert_ids, data_classes = set(), set(), set(), set()
        conf, family = 0.0, False
        earliest: float | None = None
        for i in members:
            a = alerts[i]
            tactics.add(a["tactic"])
            if a.get("technique"):
                techniques.add(a["technique"])
            alert_ids.add(a["alert_id"])
            conf = max(conf, a.get("confidence", 0.0))
            family = family or bool(a.get("threat_family"))
            data_classes.update(a.get("data_classes", ()))
            ts = a.get("ts")
            if ts is not None:
                earliest = ts if earliest is None else min(earliest, ts)
            for key, tier in a["entities"]:
                assets[key] = max(assets.get(key, 0), tier)
        # the reconstructed attack chain: the correlated alerts in the order they
        # fired, keeping the fields the analyst needs to read the story.
        chain = sorted(
            ({"alert_id": alerts[i]["alert_id"], "ts": alerts[i].get("ts"),
              "source": alerts[i].get("source"), "title": alerts[i].get("title"),
              "tactic": alerts[i]["tactic"], "technique": alerts[i].get("technique")}
             for i in members),
            key=lambda m: (m["ts"] is None, m["ts"]),
        )
        incidents.append(Incident(
            incident_id=f"inc-{gi}", tactics=tactics, techniques=techniques,
            n_alerts=len(alert_ids), assets=assets, confidence=conf, threat_family=family,
            data_classes=data_classes, detected_at=earliest, members=chain,
        ))
    return incidents


if __name__ == "__main__":
    # tiny self-check: two alerts on one host within the window merge; a far-off
    # alert on another host stays separate.
    base = 1_000_000
    alerts = [
        {"alert_id": "a1", "ts": base, "tactic": "InitialAccess", "entities": [("host:h1", 2)],
         "confidence": 0.6},
        {"alert_id": "a2", "ts": base + 600, "tactic": "Exfiltration", "entities": [("host:h1", 2)],
         "confidence": 0.9},
        {"alert_id": "a3", "ts": base + 99999, "tactic": "Discovery", "entities": [("host:h2", 1)],
         "confidence": 0.3},
    ]
    incs = correlate(alerts)
    assert len(incs) == 2, [i.incident_id for i in incs]
    merged = max(incs, key=lambda i: i.n_alerts)
    assert merged.n_alerts == 2 and merged.tactics == {"InitialAccess", "Exfiltration"}
    # the reconstructed chain carries every member, time-ordered
    assert [m["alert_id"] for m in merged.members] == ["a1", "a2"], merged.members
    print("correlate self-check passed:", [(i.incident_id, i.n_alerts) for i in incs])
