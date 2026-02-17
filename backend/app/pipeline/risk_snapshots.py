"""
Append per-country risk snapshots for the latest date in daily_metrics (Step 1 history).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..models import DailyMetric, RiskSnapshot

logger = logging.getLogger("events-risk-dashboard.risk_snapshots")


def append_risk_snapshots(session: Session) -> int:
    """
    For the latest date in daily_metrics, compute per-country max risk/severity and sum event_count,
    then upsert into risk_snapshots (replace any existing rows for that date).
    Returns number of rows written.
    """
    latest = session.execute(
        select(DailyMetric.date).order_by(DailyMetric.date.desc()).limit(1)
    ).scalars().first()
    if not latest:
        logger.info("no daily_metrics; skipping risk snapshots")
        return 0

    rows = (
        session.execute(
            select(
                DailyMetric.country,
                DailyMetric.risk_score,
                DailyMetric.severity_index,
                DailyMetric.event_count,
            ).where(DailyMetric.date == latest)
        )
        .all()
    )
    if not rows:
        return 0

    # Per-country: max(risk_score), max(severity_index), sum(event_count)
    by_country: dict[str, dict] = {}
    for country, risk_score, severity_index, event_count in rows:
        if country not in by_country:
            by_country[country] = {
                "risk_score": risk_score,
                "severity_index": severity_index,
                "event_count": event_count or 0,
            }
        else:
            r = by_country[country]
            if risk_score is not None and (r["risk_score"] is None or risk_score > r["risk_score"]):
                r["risk_score"] = risk_score
            if severity_index is not None and (
                r["severity_index"] is None or severity_index > r["severity_index"]
            ):
                r["severity_index"] = severity_index
            r["event_count"] = (r["event_count"] or 0) + (event_count or 0)

    now = datetime.now(timezone.utc)
    session.execute(delete(RiskSnapshot).where(RiskSnapshot.snapshot_date == latest))
    for country, r in by_country.items():
        session.add(
            RiskSnapshot(
                snapshot_date=latest,
                country=country,
                risk_score=r["risk_score"],
                severity_index=r["severity_index"],
                event_count=r["event_count"],
                created_at=now,
            )
        )
    session.flush()
    return len(by_country)
