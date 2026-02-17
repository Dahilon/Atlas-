"""
Combined events endpoint: GDELT + Valyu as unified MapEvent list for map and feed.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..country_centroids import get_centroid
from ..db import get_db
from ..models import Event
from ..schemas import CombinedEventsResponse, MapEventLocation, ValyuEventResponse
from .. import valyu_client
from .valyu import DEFAULT_THREAT_QUERIES, _normalize_valyu_result

router = APIRouter()


def _threat_from_quad_class(qc: Optional[int]) -> str:
    if qc is None:
        return "info"
    if qc >= 4:
        return "critical"
    if qc == 3:
        return "high"
    if qc == 2:
        return "medium"
    if qc == 1:
        return "low"
    return "info"


def _gdelt_to_map_event(e: Event) -> ValyuEventResponse:
    lat = e.lat
    lon = e.lon
    if (lat is None or lon is None) and e.country:
        centroid = get_centroid(e.country)
        if centroid:
            lat, lon = centroid[0], centroid[1]
    lat = lat if lat is not None else 0.0
    lon = lon if lon is not None else 0.0
    title = f"{e.category or 'Event'} {e.country or ''} {e.date}"
    summary = f"{e.category or 'Event'} in {e.country or 'Unknown'}"
    return ValyuEventResponse(
        id=str(e.id),
        source="gdelt",
        title=title,
        summary=summary,
        category=e.category or "event",
        threatLevel=_threat_from_quad_class(e.quad_class),
        location=MapEventLocation(
            latitude=lat,
            longitude=lon,
            placeName=e.admin1 or e.country,
            country=e.country,
        ),
        timestamp=e.ts.isoformat() if isinstance(e.ts, datetime) else str(e.ts),
        sourceUrl=e.source_url,
        severity_index=None,
        risk_score=None,
        event_count=None,
    )


@router.get("/events/combined", response_model=CombinedEventsResponse)
def get_combined_events(
    date_param: Optional[date] = Query(default=None, alias="date"),
    sources: str = Query(default="gdelt,valyu", description="Comma-separated: gdelt, valyu"),
    limit: int = Query(default=500, ge=1, le=2000),
    db: Session = Depends(get_db),
) -> CombinedEventsResponse:
    """
    Combined list for map and feed: GDELT events (with threat level from quad_class) + Valyu events.
    """
    want_gdelt = "gdelt" in (s.strip().lower() for s in sources.split(","))
    want_valyu = "valyu" in (s.strip().lower() for s in sources.split(","))

    events: List[ValyuEventResponse] = []
    counts: Dict[str, int] = {}

    if want_gdelt:
        stmt = select(Event).order_by(Event.date.desc(), Event.ts.desc())
        if date_param:
            stmt = stmt.where(Event.date == date_param)
        else:
            cutoff = (datetime.now(timezone.utc).date() - timedelta(days=14))
            stmt = stmt.where(Event.date >= cutoff)
        stmt = stmt.limit(limit)
        gdelt_rows = db.execute(stmt).scalars().all()
        gdelt_events = [_gdelt_to_map_event(e) for e in gdelt_rows]
        events.extend(gdelt_events)
        counts["gdelt"] = len(gdelt_events)

    if want_valyu:
        start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        all_results: List[Dict[str, Any]] = []
        seen_urls: set = set()
        for q in DEFAULT_THREAT_QUERIES[:8]:
            try:
                results = valyu_client.search(q, max_num_results=10, start_date=start_date)
                for item in results:
                    url = (item.get("url") or "").strip()
                    if url and url in seen_urls:
                        continue
                    if url:
                        seen_urls.add(url)
                    all_results.append(item)
            except Exception:
                continue
        valyu_events = [_normalize_valyu_result(r, i) for i, r in enumerate(all_results)]
        events.extend(valyu_events)
        counts["valyu"] = len(valyu_events)

    threat_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    events.sort(key=lambda x: threat_order.get(x.threatLevel, 5))
    events = events[:limit]

    return CombinedEventsResponse(events=events, count=len(events), sources=counts)
