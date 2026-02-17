"""
Map endpoint: per-country aggregates with lat/lon for the combined map (Step 1).
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..country_centroids import get_centroid
from ..db import get_db
from ..models import DailyMetric
from ..schemas import MapCountryResponse


router = APIRouter()


@router.get("/map", response_model=List[MapCountryResponse])
def get_map(
    date_param: Optional[date] = Query(default=None, alias="date", description="Date (YYYY-MM-DD); default latest"),
    db: Session = Depends(get_db),
) -> List[MapCountryResponse]:
    """
    Per-country aggregates for one date: country, lat, lon, severity_index, risk_score, event_count.
    Used by the frontend map to show country-level risk/severity. Countries without a centroid are omitted.
    """
    target = date_param
    if target is None:
        latest = db.execute(
            select(DailyMetric.date).order_by(DailyMetric.date.desc()).limit(1)
        ).scalars().first()
        if not latest:
            return []
        target = latest

    subq = (
        select(
            DailyMetric.country,
            func.max(DailyMetric.severity_index).label("severity_index"),
            func.max(DailyMetric.risk_score).label("risk_score"),
            func.sum(DailyMetric.event_count).label("event_count"),
        )
        .where(DailyMetric.date == target)
        .group_by(DailyMetric.country)
    )
    rows = db.execute(subq).all()

    out: List[MapCountryResponse] = []
    for country, severity_index, risk_score, event_count in rows:
        if not country:
            continue
        centroid = get_centroid(country)
        if centroid is None:
            continue
        lat, lon = centroid[0], centroid[1]
        out.append(
            MapCountryResponse(
                country=country,
                lat=lat,
                lon=lon,
                severity_index=float(severity_index) if severity_index is not None else None,
                risk_score=float(risk_score) if risk_score is not None else None,
                event_count=int(event_count) if event_count is not None else None,
            )
        )
    return out
