"""
History API: risk snapshots over time (Step 1).
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import RiskSnapshot
from ..schemas import RiskSnapshotResponse


router = APIRouter()


@router.get("/history/risk", response_model=List[RiskSnapshotResponse])
def get_risk_history(
    country: Optional[str] = Query(default=None, description="ISO-2 country code filter"),
    days: int = Query(default=90, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db),
) -> List[RiskSnapshotResponse]:
    """
    Return risk snapshots for monitoring over time. Data is appended by the live ingest pipeline.
    """
    end = date.today()
    start = end - timedelta(days=days)
    stmt = (
        select(RiskSnapshot)
        .where(RiskSnapshot.snapshot_date >= start, RiskSnapshot.snapshot_date <= end)
        .order_by(RiskSnapshot.snapshot_date.desc())
    )
    if country:
        stmt = stmt.where(RiskSnapshot.country == country.upper())
    rows = db.execute(stmt).scalars().all()
    return [
        RiskSnapshotResponse(
            snapshot_date=r.snapshot_date,
            country=r.country,
            risk_score=r.risk_score,
            severity_index=r.severity_index,
            event_count=r.event_count,
        )
        for r in rows
    ]
