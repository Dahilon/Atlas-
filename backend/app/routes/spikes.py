from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Spike
from ..schemas import SpikeResponse

router = APIRouter()


@router.get("/spikes", response_model=List[SpikeResponse])
def list_spikes(
    country: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> List[SpikeResponse]:
    """List detected spikes (anomalies) with evidence event IDs."""
    stmt = select(Spike).order_by(Spike.date.desc(), Spike.z_score.desc())
    if country:
        stmt = stmt.where(Spike.country == country)
    if category:
        stmt = stmt.where(Spike.category == category)
    if start:
        stmt = stmt.where(Spike.date >= start)
    if end:
        stmt = stmt.where(Spike.date <= end)
    stmt = stmt.limit(limit)
    spikes = db.execute(stmt).scalars().all()
    return [
        SpikeResponse(
            id=s.id,
            date=s.date,
            country=s.country,
            category=s.category,
            z_score=s.z_score,
            z_used=s.z_used,
            delta=s.delta,
            rolling_center=s.rolling_center,
            rolling_dispersion=s.rolling_dispersion,
            baseline_quality=s.baseline_quality,
            baseline_method=s.baseline_method,
            evidence_event_ids=s.evidence_event_ids,
            computed_at=s.computed_at,
            pipeline_version=s.pipeline_version,
        )
        for s in spikes
    ]
