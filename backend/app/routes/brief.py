from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import DailyMetric, Spike
from ..schemas import BriefResponse

router = APIRouter()


@router.get("/brief", response_model=BriefResponse)
def daily_brief(
    for_date: Optional[date] = Query(default=None, alias="date", description="Date for brief (default: latest)"),
    db: Session = Depends(get_db),
) -> BriefResponse:
    """
    Daily intel brief: top risk movers and top spikes with a short summary.
    """
    today = for_date or date.today()

    # Top movers: daily_metrics for that date (or latest) by risk_score desc
    stmt = (
        select(DailyMetric)
        .where(DailyMetric.date <= today)
        .order_by(DailyMetric.date.desc(), DailyMetric.risk_score.desc().nullslast())
        .limit(200)
    )
    metrics = db.execute(stmt).scalars().all()
    # Take latest date present
    by_date: dict = {}
    for m in metrics:
        if m.date not in by_date:
            by_date[m.date] = []
        by_date[m.date].append(m)
    latest_date = max(by_date.keys()) if by_date else today
    movers = by_date.get(latest_date, [])[:15]
    top_movers = [
        {
            "date": str(m.date),
            "country": m.country,
            "category": m.category,
            "risk_score": m.risk_score,
            "event_count": m.event_count,
            "z_score": m.z_score,
            "severity_index": getattr(m, "severity_index", None),
            "z_severity": getattr(m, "z_severity", None),
        }
        for m in movers
    ]

    # Top spikes: recent spikes (last 7 days)
    start = today - timedelta(days=7)
    spike_stmt = (
        select(Spike)
        .where(Spike.date >= start)
        .order_by(Spike.z_used.desc().nulls_last(), Spike.z_score.desc().nulls_last())
        .limit(15)
    )
    spikes = db.execute(spike_stmt).scalars().all()
    top_spikes = [
        {
            "date": str(s.date),
            "country": s.country,
            "category": s.category,
            "z_score": s.z_score,
            "z_used": getattr(s, "z_used", None),
            "delta": s.delta,
        }
        for s in spikes
    ]

    summary = (
        f"Brief for {latest_date}: {len(top_movers)} top risk rows, {len(top_spikes)} spikes in last 7 days."
    )
    return BriefResponse(top_movers=top_movers, top_spikes=top_spikes, summary=summary)
