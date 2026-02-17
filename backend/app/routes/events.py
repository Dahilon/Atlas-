from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Event
from ..schemas import EventResponse


router = APIRouter()


@router.get("/events", response_model=List[EventResponse])
def list_events(
    country: Optional[str] = Query(default=None, description="ISO-2 country code filter"),
    start: Optional[date] = Query(default=None, description="Start date (YYYY-MM-DD)"),
    end: Optional[date] = Query(default=None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    limit: int = Query(default=200, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> List[EventResponse]:
    """
    List normalized events with optional filters.
    """
    stmt = select(Event).order_by(Event.date.desc())

    if country:
        stmt = stmt.where(Event.country == country)
    if start:
        stmt = stmt.where(Event.date >= start)
    if end:
        stmt = stmt.where(Event.date <= end)
    if category:
        stmt = stmt.where(Event.category == category)

    stmt = stmt.limit(limit)

    events = db.execute(stmt).scalars().all()

    return [
        EventResponse(
            id=e.id,
            ts=e.ts,
            date=e.date,
            country=e.country,
            admin1=e.admin1,
            lat=e.lat,
            lon=e.lon,
            event_code=e.event_code,
            quad_class=e.quad_class,
            goldstein=getattr(e, "goldstein", None),
            avg_tone=e.avg_tone,
            source_url=e.source_url,
            category=e.category,
        )
        for e in events
    ]

