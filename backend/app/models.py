from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    UniqueConstraint,
)

from .db import Base


class Event(Base):
    """
    Normalized event derived from GDELT daily exports.

    Fields are intentionally conservative for Day 1; we can
    extend later while keeping this as the canonical schema.
    """

    __tablename__ = "events"

    # GDELT's GLOBALEVENTID (string for portability)
    id = Column(String, primary_key=True, index=True)

    ts = Column(DateTime, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # ISO-2 country code (primarily ActionGeo_CountryCode)
    country = Column(String(2), nullable=True, index=True)

    # Optional admin region
    admin1 = Column(String, nullable=True)

    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

    event_code = Column(String(4), nullable=True, index=True)
    quad_class = Column(Integer, nullable=True)
    goldstein = Column(Float, nullable=True)  # GDELT Goldstein scale -10 to +10

    avg_tone = Column(Float, nullable=True)

    source_url = Column(String, nullable=True)

    # High-level human-readable category (taxonomy mapping)
    category = Column(String, nullable=True, index=True)


class DailyMetric(Base):
    """
    Daily aggregated metrics for (date, country, category).
    Day 2 v2: rolling_center/dispersion, baseline_quality, risk with reasons_json, pipeline_version.
    """

    __tablename__ = "daily_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)

    date = Column(Date, nullable=False, index=True)
    country = Column(String(2), nullable=False, index=True)
    category = Column(String, nullable=False, index=True)

    event_count = Column(Integer, nullable=False)
    avg_tone = Column(Float, nullable=True)

    # Severity layer (Phase 1): goldstein/tone/quad intensity
    mean_goldstein = Column(Float, nullable=True)
    min_goldstein = Column(Float, nullable=True)
    mean_tone = Column(Float, nullable=True)  # same as avg_tone; kept for clarity
    pct_negative_tone = Column(Float, nullable=True)  # 0-1 fraction of events with tone < 0
    severity_index = Column(Float, nullable=True)  # 0-100 explainable weighted combo
    severity_rolling_center = Column(Float, nullable=True)
    severity_rolling_dispersion = Column(Float, nullable=True)
    z_severity = Column(Float, nullable=True)  # robust z on severity_index
    percentile_180d = Column(Float, nullable=True)  # optional; null if < 180d history

    # Rolling baseline (center = median or mean, dispersion = MAD or std)
    rolling_center = Column(Float, nullable=True)
    rolling_dispersion = Column(Float, nullable=True)
    baseline_quality = Column(String(8), nullable=True)  # "low" | "ok"
    baseline_method = Column(String(16), nullable=True)  # "robust" | "standard"
    baseline_window_days = Column(Integer, nullable=True)
    z_score = Column(Float, nullable=True)

    # Risk (0-100) and explainability
    risk_score = Column(Float, nullable=True)
    reasons_json = Column(String, nullable=True)  # JSON
    computed_at = Column(DateTime, nullable=True)
    pipeline_version = Column(String(32), nullable=True)

    # Legacy (kept for backward compat; prefer rolling_center / rolling_dispersion)
    rolling_mean = Column(Float, nullable=True)
    rolling_std = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("date", "country", "category", name="uq_daily_metrics_key"),
    )


class Spike(Base):
    """
    Detected anomaly: (date, country, category) where z_used > threshold.
    UPSERT key: (date, country, category, baseline_method, baseline_window_days, pipeline_version).
    """

    __tablename__ = "spikes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False, index=True)
    country = Column(String(2), nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    z_score = Column(Float, nullable=False)
    z_used = Column(Float, nullable=True)  # max(0,z) for one_sided
    delta = Column(Float, nullable=True)  # event_count - rolling_center
    rolling_center = Column(Float, nullable=True)
    rolling_dispersion = Column(Float, nullable=True)
    baseline_quality = Column(String(8), nullable=True)
    baseline_method = Column(String(16), nullable=True)
    baseline_window_days = Column(Integer, nullable=True)
    evidence_event_ids = Column(String, nullable=True)  # JSON array
    computed_at = Column(DateTime, nullable=True)
    pipeline_version = Column(String(32), nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "date",
            "country",
            "category",
            "baseline_method",
            "baseline_window_days",
            "pipeline_version",
            name="uq_spikes_baseline_version",
        ),
    )


class RiskSnapshot(Base):
    """
    Per-day, per-country risk snapshot for history/monitoring (Step 1).
    One row per (snapshot_date, country); append after each live Day 2 run.
    """

    __tablename__ = "risk_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    country = Column(String(2), nullable=False, index=True)
    risk_score = Column(Float, nullable=True)
    severity_index = Column(Float, nullable=True)
    event_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("snapshot_date", "country", name="uq_risk_snapshots_date_country"),
    )

