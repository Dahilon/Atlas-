"""
Valyu proxy and military bases. Requires VALYU_API_KEY in env for Valyu endpoints.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from .. import valyu_client
from ..military_bases_data import MILITARY_BASES
from ..schemas import (
    CountryConflictsResponse,
    MapEventLocation,
    MilitaryBaseResponse,
    ValyuEventResponse,
)

router = APIRouter()

DEFAULT_THREAT_QUERIES = [
    "breaking news conflict military",
    "geopolitical crisis tensions",
    "protest demonstration unrest",
    "natural disaster emergency",
    "terrorism attack security",
    "military deployment troops mobilization",
    "nuclear threat ballistic missile test",
]


def _event_id(url: str, title: str, idx: int) -> str:
    raw = f"valyu:{url}:{title}:{idx}"
    return hashlib.sha256(raw.encode()).hexdigest()[:24]


def _threat_from_content(content: str) -> str:
    c = (content or "").lower()
    if any(x in c for x in ("critical", "nuclear", "war", "invasion")):
        return "critical"
    if any(x in c for x in ("attack", "strike", "bombing", "terrorism")):
        return "high"
    if any(x in c for x in ("protest", "unrest", "tension")):
        return "medium"
    return "medium"


def _normalize_valyu_result(item: Dict[str, Any], idx: int) -> ValyuEventResponse:
    title = item.get("title") or "Untitled"
    url = item.get("url") or ""
    content = item.get("content") or ""
    summary = (content[:500] + "…") if len(content) > 500 else content
    pub = item.get("publishedDate")
    ts = pub if pub else datetime.now(timezone.utc).isoformat()
    threat = _threat_from_content(content)
    return ValyuEventResponse(
        id=_event_id(url, title, idx),
        source="valyu",
        title=title,
        summary=summary,
        category="news",
        threatLevel=threat,
        location=MapEventLocation(latitude=0.0, longitude=0.0, placeName=title[:100], country=None),
        timestamp=ts,
        sourceUrl=url or None,
    )


class ValyuEventsBody(BaseModel):
    queries: Optional[List[str]] = None


@router.post("/valyu/events", response_model=Dict[str, Any])
def post_valyu_events(body: Optional[ValyuEventsBody] = None) -> Dict[str, Any]:
    """
    Proxy to Valyu search; returns events normalized to MapEvent shape.
    If body.queries is empty or omitted, uses default threat queries.
    """
    queries = (body.queries if body and body.queries else None) or DEFAULT_THREAT_QUERIES
    start_date = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    all_results: List[Dict[str, Any]] = []
    seen_urls: set = set()
    for q in queries[:12]:
        results = valyu_client.search(q, max_num_results=15, start_date=start_date)
        for i, item in enumerate(results):
            url = (item.get("url") or "").strip()
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            all_results.append(item)
    events = [ _normalize_valyu_result(r, i) for i, r in enumerate(all_results) ]
    return {"events": [e.model_dump() for e in events], "count": len(events)}


@router.get("/valyu/countries/conflicts", response_model=CountryConflictsResponse)
def get_valyu_country_conflicts(country: str = Query(..., description="Country name or code")) -> CountryConflictsResponse:
    """
    Proxy to Valyu answer for historical and current conflicts for the given country.
    """
    data = valyu_client.get_country_conflicts(country)
    return CountryConflictsResponse(
        country=country,
        past=data["past"],
        current=data["current"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


_bases_cache: Optional[List[Dict[str, Any]]] = None
_bases_cache_ts: Optional[float] = None
CACHE_SEC = 3600


@router.get("/military-bases", response_model=Dict[str, Any])
def get_military_bases() -> Dict[str, Any]:
    """
    Return static list of US and NATO military bases for the map layer. Cached 1h.
    """
    global _bases_cache, _bases_cache_ts
    import time
    now = time.time()
    if _bases_cache is not None and _bases_cache_ts is not None and (now - _bases_cache_ts) < CACHE_SEC:
        return {"bases": _bases_cache, "cached": True}
    out = [
        {
            "country": b["country"],
            "baseName": b["baseName"],
            "latitude": b["latitude"],
            "longitude": b["longitude"],
            "type": b["type"],
        }
        for b in MILITARY_BASES
    ]
    _bases_cache = out
    _bases_cache_ts = now
    return {"bases": out, "cached": False}
