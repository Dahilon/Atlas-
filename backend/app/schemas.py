from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class EventResponse(BaseModel):
    id: str
    ts: datetime
    date: date
    country: Optional[str]
    admin1: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    event_code: Optional[str]
    quad_class: Optional[int]
    goldstein: Optional[float] = None
    avg_tone: Optional[float]
    source_url: Optional[str]
    category: Optional[str]


class MetricResponse(BaseModel):
    date: date
    country: str
    category: str
    event_count: int
    avg_tone: Optional[float]
    mean_goldstein: Optional[float] = None
    min_goldstein: Optional[float] = None
    mean_tone: Optional[float] = None
    pct_negative_tone: Optional[float] = None
    severity_index: Optional[float] = None
    severity_rolling_center: Optional[float] = None
    severity_rolling_dispersion: Optional[float] = None
    z_severity: Optional[float] = None
    percentile_180d: Optional[float] = None
    rolling_mean: Optional[float] = None
    rolling_std: Optional[float] = None
    rolling_center: Optional[float] = None
    rolling_dispersion: Optional[float] = None
    baseline_quality: Optional[str] = None
    baseline_method: Optional[str] = None
    z_score: Optional[float] = None
    risk_score: Optional[float] = None
    reasons_json: Optional[str] = None
    computed_at: Optional[datetime] = None
    pipeline_version: Optional[str] = None


class SpikeResponse(BaseModel):
    id: int
    date: date
    country: str
    category: str
    z_score: float
    z_used: Optional[float] = None
    delta: Optional[float] = None
    rolling_center: Optional[float] = None
    rolling_dispersion: Optional[float] = None
    baseline_quality: Optional[str] = None
    baseline_method: Optional[str] = None
    evidence_event_ids: Optional[str] = None  # JSON array
    computed_at: Optional[datetime] = None
    pipeline_version: Optional[str] = None


class BriefResponse(BaseModel):
    top_movers: List[dict]  # [{ "country": "US", "risk_score": 45, "change": "+12" }, ...]
    top_spikes: List[dict]  # [{ "date", "country", "category", "z_score", "delta" }, ...]
    summary: str


class CountryListResponse(BaseModel):
    countries: List[str]


class RiskSnapshotResponse(BaseModel):
    snapshot_date: date
    country: str
    risk_score: Optional[float] = None
    severity_index: Optional[float] = None
    event_count: Optional[int] = None


class MapCountryResponse(BaseModel):
    country: str
    lat: float
    lon: float
    severity_index: Optional[float] = None
    risk_score: Optional[float] = None
    event_count: Optional[int] = None


class MapEventLocation(BaseModel):
    latitude: float
    longitude: float
    placeName: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None


class ValyuEventResponse(BaseModel):
    id: str
    source: str = "valyu"
    title: str
    summary: str
    category: str
    threatLevel: str
    location: MapEventLocation
    timestamp: str
    sourceUrl: Optional[str] = None
    severity_index: Optional[float] = None
    risk_score: Optional[float] = None
    event_count: Optional[int] = None


class ConflictSection(BaseModel):
    conflicts: str
    sources: List[dict]


class CountryConflictsResponse(BaseModel):
    country: str
    past: ConflictSection
    current: ConflictSection
    timestamp: Optional[str] = None


class MilitaryBaseResponse(BaseModel):
    country: str
    baseName: str
    latitude: float
    longitude: float
    type: str


class CombinedEventsResponse(BaseModel):
    """Combined GDELT + Valyu events for map and feed (MapEvent shape)."""
    events: List[ValyuEventResponse]
    count: int
    sources: Dict[str, int] = {}

