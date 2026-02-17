from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import DailyMetric, Event
from ..schemas import CountryListResponse


router = APIRouter()


@router.get("/countries", response_model=CountryListResponse)
def list_countries(db: Session = Depends(get_db)) -> CountryListResponse:
    """
    Return distinct ISO-2 country codes present in the data.

    Prefer daily_metrics as it reflects aggregated analytics;
    fall back to events if metrics are empty.
    """
    stmt = select(DailyMetric.country).distinct().where(DailyMetric.country.isnot(None))
    rows = db.execute(stmt).scalars().all()

    if not rows:
        stmt = select(Event.country).distinct().where(Event.country.isnot(None))
        rows = db.execute(stmt).scalars().all()

    countries: List[str] = sorted({c for c in rows if c})
    return CountryListResponse(countries=countries)

