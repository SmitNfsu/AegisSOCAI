"""Ingestion domain package (Reorg R5 / #486).

Pulling external security data into AegisSOC — SIEM, Kafka, and
S3-dropped findings.

Callers import directly from ``core.ingestion.<module>``; the legacy
``services.*`` paths were removed with this move.
"""
