from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import DailyMetric
from ..schemas import MetricResponse


router = APIRouter()


@router.get("/metrics", response_model=List[MetricResponse])
def list_metrics(
    country: Optional[str] = Query(default=None, description="ISO-2 country code filter"),
    start: Optional[date] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(default=None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    db: Session = Depends(get_db),
) -> List[MetricResponse]:
    """
    List daily aggregated metrics with optional filters.
    """
    stmt = select(DailyMetric).order_by(DailyMetric.date.desc())

    if country:
        stmt = stmt.where(DailyMetric.country == country)
    if start:
        stmt = stmt.where(DailyMetric.date >= start)
    if end:
        stmt = stmt.where(DailyMetric.date <= end)
    if category:
        stmt = stmt.where(DailyMetric.category == category)

    metrics = db.execute(stmt).scalars().all()

    return [
        MetricResponse(
            date=m.date,
            country=m.country,
            category=m.category,
            event_count=m.event_count,
            avg_tone=m.avg_tone,
            mean_goldstein=getattr(m, "mean_goldstein", None),
            min_goldstein=getattr(m, "min_goldstein", None),
            mean_tone=getattr(m, "mean_tone", None),
            pct_negative_tone=getattr(m, "pct_negative_tone", None),
            severity_index=getattr(m, "severity_index", None),
            severity_rolling_center=getattr(m, "severity_rolling_center", None),
            severity_rolling_dispersion=getattr(m, "severity_rolling_dispersion", None),
            z_severity=getattr(m, "z_severity", None),
            percentile_180d=getattr(m, "percentile_180d", None),
            rolling_mean=m.rolling_mean,
            rolling_std=m.rolling_std,
            rolling_center=m.rolling_center,
            rolling_dispersion=m.rolling_dispersion,
            baseline_quality=m.baseline_quality,
            baseline_method=m.baseline_method,
            z_score=m.z_score,
            risk_score=m.risk_score,
            reasons_json=m.reasons_json,
            computed_at=m.computed_at,
            pipeline_version=m.pipeline_version,
        )
        for m in metrics
    ]

