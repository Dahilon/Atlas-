"""
Day 2 pipeline v2: robust rolling baseline (median+MAD or mean+std), risk scoring, spike detection.

- Step 4: Rolling center/dispersion, baseline_quality (low/ok), z_score with variance floor; bulk update.
- Step 5: z_used (one_sided or two_sided), risk_score + reasons_json + pipeline_version; bulk update.
- Step 6: Spike UPSERT (no table clear), evidence by |avg_tone| desc; store full audit fields.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import List, Optional

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Event, DailyMetric, Spike
from ..pipeline_config import (
    BASELINE_METHOD,
    BASELINE_MIN_PERIODS,
    BASELINE_WINDOW_DAYS_SHORT,
    MAD_SCALE_FOR_NORMAL,
    PIPELINE_VERSION,
    SPIKE_EVIDENCE_N,
    SPIKE_MODE,
    Z_SPIKE_THRESHOLD,
)

logger = logging.getLogger("events-risk-dashboard.day2")

# Category base weights (higher = more severe for risk)
CATEGORY_WEIGHTS = {
    "Armed Conflict": 25,
    "Civil Unrest": 15,
    "Crime / Terror": 20,
    "Diplomacy / Sanctions": 8,
    "Economic Disruption": 12,
    "Infrastructure / Energy": 15,
}
DEFAULT_WEIGHT = 10


def _base_weight(category: Optional[str]) -> float:
    return float(CATEGORY_WEIGHTS.get(category, DEFAULT_WEIGHT))


def _rolling_mad(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    """Rolling Median Absolute Deviation: median(|x - rolling_median|)."""
    center = series.rolling(window, min_periods=min_periods).median()
    abs_dev = (series - center).abs()
    return abs_dev.rolling(window, min_periods=min_periods).median()


def compute_rolling_and_zscore(session: Session) -> int:
    """
    Step 4: Compute rolling_center, rolling_dispersion, baseline_quality, z_score.
    Robust: median + MAD with 0.6745 scaling. Standard: mean + std.
    min_periods=7; before that baseline_quality=low and z_score=null. Variance floor: null z when dispersion==0.
    Bulk update daily_metrics.
    """
    logger.info("computing rolling baselines and z-scores", extra={"method": BASELINE_METHOD})
    stmt = select(DailyMetric).order_by(DailyMetric.country, DailyMetric.category, DailyMetric.date)
    rows = session.execute(stmt).scalars().all()
    if not rows:
        logger.info("no daily_metrics for rolling")
        return 0

    df = pd.DataFrame(
        [
            {
                "id": m.id,
                "date": m.date,
                "country": m.country,
                "category": m.category,
                "event_count": m.event_count,
            }
            for m in rows
        ]
    )
    df = df.sort_values(["country", "category", "date"])
    window = BASELINE_WINDOW_DAYS_SHORT
    min_periods = BASELINE_MIN_PERIODS

    def roll_center(x: pd.Series) -> pd.Series:
        if BASELINE_METHOD == "robust":
            return x.rolling(window, min_periods=min_periods).median()
        return x.rolling(window, min_periods=min_periods).mean()

    def roll_dispersion(x: pd.Series) -> pd.Series:
        if BASELINE_METHOD == "robust":
            return _rolling_mad(x, window, min_periods)
        return x.rolling(window, min_periods=min_periods).std()

    df["rolling_center"] = df.groupby(["country", "category"])["event_count"].transform(roll_center)
    df["rolling_dispersion"] = df.groupby(["country", "category"])["event_count"].transform(
        roll_dispersion
    )
    # baseline_quality: "ok" only when we have at least min_periods in the window
    df["n_in_window"] = (
        df.groupby(["country", "category"])["event_count"]
        .transform(lambda x: x.rolling(window, min_periods=1).count())
    )
    df["baseline_quality"] = df["n_in_window"].apply(lambda n: "ok" if n >= min_periods else "low")

    # Z-score: only when dispersion > 0 and quality ok. Robust: 0.6745 * (x - median) / MAD
    df["z_score"] = None
    ok = (df["baseline_quality"] == "ok") & df["rolling_dispersion"].notna()
    ok = ok & (df["rolling_dispersion"] > 0)
    if BASELINE_METHOD == "robust":
        df.loc[ok, "z_score"] = (
            MAD_SCALE_FOR_NORMAL
            * (df.loc[ok, "event_count"] - df.loc[ok, "rolling_center"])
            / df.loc[ok, "rolling_dispersion"]
        )
    else:
        df.loc[ok, "z_score"] = (
            (df.loc[ok, "event_count"] - df.loc[ok, "rolling_center"])
            / df.loc[ok, "rolling_dispersion"]
        )

    now = datetime.now(timezone.utc)
    mappings = []
    for _, r in df.iterrows():
        mappings.append(
            {
                "id": int(r["id"]),
                "rolling_center": float(r["rolling_center"]) if pd.notna(r["rolling_center"]) else None,
                "rolling_dispersion": float(r["rolling_dispersion"]) if pd.notna(r["rolling_dispersion"]) else None,
                "baseline_quality": r["baseline_quality"],
                "baseline_method": BASELINE_METHOD,
                "baseline_window_days": window,
                "z_score": float(r["z_score"]) if pd.notna(r["z_score"]) else None,
                "computed_at": now,
                "pipeline_version": PIPELINE_VERSION,
                "rolling_mean": float(r["rolling_center"]) if pd.notna(r["rolling_center"]) else None,
                "rolling_std": float(r["rolling_dispersion"]) if pd.notna(r["rolling_dispersion"]) else None,
            }
        )
    session.bulk_update_mappings(DailyMetric, mappings)
    logger.info("rolling and z-score updated", extra={"rows": len(mappings)})
    return len(mappings)


def compute_severity_baseline(session: Session) -> int:
    """
    Phase 1: Rolling baseline on severity_index (robust: median + MAD), z_severity.
    Uses same window/min_periods as count baseline. Only rows with baseline_quality==ok
    and non-null severity_index get z_severity. Bulk update.
    """
    logger.info("computing severity baseline (z_severity)")
    stmt = select(DailyMetric).order_by(DailyMetric.country, DailyMetric.category, DailyMetric.date)
    rows = session.execute(stmt).scalars().all()
    if not rows:
        return 0

    df = pd.DataFrame(
        [
            {
                "id": m.id,
                "date": m.date,
                "country": m.country,
                "category": m.category,
                "severity_index": m.severity_index if m.severity_index is not None else 0.0,
                "baseline_quality": m.baseline_quality or "low",
            }
            for m in rows
        ]
    )
    df = df.sort_values(["country", "category", "date"])
    window = BASELINE_WINDOW_DAYS_SHORT
    min_periods = BASELINE_MIN_PERIODS
    # Use log1p(severity_index+1) for stable scale; store center/dispersion in original scale for interpretability
    df["sev_log"] = np.log1p(df["severity_index"].clip(0, None) + 1)
    df["severity_rolling_center"] = df.groupby(["country", "category"])["sev_log"].transform(
        lambda x: x.rolling(window, min_periods=min_periods).median()
    )
    mad_series = df.groupby(["country", "category"])["sev_log"].transform(
        lambda x: _rolling_mad(x, window, min_periods)
    )
    df["severity_rolling_dispersion"] = mad_series
    df["z_severity"] = None
    ok = (df["baseline_quality"] == "ok") & df["severity_rolling_dispersion"].notna() & (df["severity_rolling_dispersion"] > 0)
    df.loc[ok, "z_severity"] = (
        MAD_SCALE_FOR_NORMAL
        * (df.loc[ok, "sev_log"] - df.loc[ok, "severity_rolling_center"])
        / df.loc[ok, "severity_rolling_dispersion"]
    )
    # Convert center back to original scale for storage (expm1)
    df["severity_rolling_center"] = np.expm1(df["severity_rolling_center"])
    now = datetime.now(timezone.utc)
    mappings = []
    for _, r in df.iterrows():
        mappings.append(
            {
                "id": int(r["id"]),
                "severity_rolling_center": float(r["severity_rolling_center"]) if pd.notna(r["severity_rolling_center"]) else None,
                "severity_rolling_dispersion": float(r["severity_rolling_dispersion"]) if pd.notna(r["severity_rolling_dispersion"]) else None,
                "z_severity": float(r["z_severity"]) if pd.notna(r["z_severity"]) else None,
            }
        )
    session.bulk_update_mappings(DailyMetric, mappings)
    logger.info("severity baseline updated", extra={"rows": len(mappings)})
    return len(mappings)


def compute_risk_scores(session: Session) -> int:
    """
    Step 5 (Phase 1): risk = base_weight * recency_mult * severity_multiplier + spike_bonus, cap 100.
    severity_multiplier = 0.7 + 0.3 * (severity_index/100). reasons_json includes severity_component,
    z_count, z_severity, severity_index, severity_multiplier. Rows with baseline_quality!=ok get risk_score null.
    """
    logger.info("computing risk scores", extra={"spike_mode": SPIKE_MODE})
    stmt = select(DailyMetric)
    rows = session.execute(stmt).scalars().all()
    if not rows:
        return 0

    today = date.today()
    now = datetime.now(timezone.utc)
    mappings = []
    for m in rows:
        if m.baseline_quality != "ok":
            mappings.append(
                {
                    "id": m.id,
                    "risk_score": None,
                    "reasons_json": json.dumps({"note": "baseline not ready", "baseline_quality": m.baseline_quality or "low"}),
                    "computed_at": now,
                    "pipeline_version": PIPELINE_VERSION,
                }
            )
            continue

        z = m.z_score if m.z_score is not None else 0
        z_used = max(0, z) if SPIKE_MODE == "one_sided" else abs(z)
        base_component = _base_weight(m.category)
        days_ago = (today - m.date).days
        recency_component = 1.5 if days_ago <= 7 else (1.2 if days_ago <= 14 else 1.0)
        anomaly_component = 0 if z_used <= 1 else min(25, (z_used - 1) * 10)
        severity_index = m.severity_index if m.severity_index is not None else 0.0
        severity_multiplier = 0.7 + 0.3 * (severity_index / 100.0)
        raw = base_component * recency_component * severity_multiplier + anomaly_component
        risk_score = min(100.0, round(raw, 1))

        reasons = {
            "base_component": round(base_component, 1),
            "recency_component": recency_component,
            "anomaly_component": round(anomaly_component, 1),
            "severity_component": round(severity_multiplier, 3),
            "base_weight": round(base_component, 1),
            "recency_mult": recency_component,
            "severity_multiplier": round(severity_multiplier, 3),
            "severity_index": round(severity_index, 2) if m.severity_index is not None else None,
            "z_count": round(z, 2) if z is not None else None,
            "z_severity": round(m.z_severity, 2) if m.z_severity is not None else None,
            "z_score": round(z, 2) if z is not None else None,
            "z_used": round(z_used, 2),
            "spike_bonus": round(anomaly_component, 1),
            "baseline_method": m.baseline_method or BASELINE_METHOD,
            "baseline_window_days": m.baseline_window_days or BASELINE_WINDOW_DAYS_SHORT,
        }
        mappings.append(
            {
                "id": m.id,
                "risk_score": risk_score,
                "reasons_json": json.dumps(reasons),
                "computed_at": now,
                "pipeline_version": PIPELINE_VERSION,
            }
        )
    session.bulk_update_mappings(DailyMetric, mappings)
    logger.info("risk scores updated", extra={"rows": len(mappings)})
    return len(mappings)


def _get_evidence_event_ids(
    session: Session, dt: date, country: str, category: str, limit: int
) -> List[str]:
    """Top N event IDs for (date, country, category) by strongest absolute tone (desc), nulls last."""
    stmt = (
        select(Event.id)
        .where(
            Event.date == dt,
            Event.country == country,
            Event.category == category,
        )
        .order_by(Event.avg_tone.is_(None), func.abs(Event.avg_tone).desc())
        .limit(limit)
    )
    return [r[0] for r in session.execute(stmt).all()]


def detect_spikes(session: Session) -> int:
    """
    Step 6: Select rows with baseline_quality==ok and z_used > Z_SPIKE_THRESHOLD.
    UPSERT spikes by (date, country, category, baseline_method, baseline_window_days, pipeline_version).
    Evidence: top SPIKE_EVIDENCE_N events by |avg_tone| desc nulls last.
    """
    logger.info("detecting spikes", extra={"z_threshold": Z_SPIKE_THRESHOLD, "spike_mode": SPIKE_MODE})
    stmt = select(DailyMetric).where(
        DailyMetric.baseline_quality == "ok",
        DailyMetric.z_score.isnot(None),
    )
    rows = session.execute(stmt).scalars().all()
    if not rows:
        logger.info("no candidates for spikes")
        return 0

    z_threshold = Z_SPIKE_THRESHOLD
    now = datetime.now(timezone.utc)
    window = BASELINE_WINDOW_DAYS_SHORT
    count = 0
    for m in rows:
        z = m.z_score or 0
        z_used = max(0, z) if SPIKE_MODE == "one_sided" else abs(z)
        if z_used <= z_threshold:
            continue

        evidence_ids = _get_evidence_event_ids(
            session, m.date, m.country, m.category, SPIKE_EVIDENCE_N
        )
        delta = (m.event_count - m.rolling_center) if m.rolling_center is not None else None

        existing = session.execute(
            select(Spike).where(
                Spike.date == m.date,
                Spike.country == m.country,
                Spike.category == m.category,
                Spike.baseline_method == BASELINE_METHOD,
                Spike.baseline_window_days == window,
                Spike.pipeline_version == PIPELINE_VERSION,
            )
        ).scalars().first()

        if existing:
            existing.z_score = z
            existing.z_used = z_used
            existing.delta = float(delta) if delta is not None else None
            existing.rolling_center = m.rolling_center
            existing.rolling_dispersion = m.rolling_dispersion
            existing.baseline_quality = m.baseline_quality
            existing.baseline_method = BASELINE_METHOD
            existing.baseline_window_days = window
            existing.evidence_event_ids = json.dumps(evidence_ids)
            existing.computed_at = now
            existing.pipeline_version = PIPELINE_VERSION
        else:
            session.add(
                Spike(
                    date=m.date,
                    country=m.country,
                    category=m.category,
                    z_score=z,
                    z_used=z_used,
                    delta=float(delta) if delta is not None else None,
                    rolling_center=m.rolling_center,
                    rolling_dispersion=m.rolling_dispersion,
                    baseline_quality=m.baseline_quality,
                    baseline_method=BASELINE_METHOD,
                    baseline_window_days=window,
                    evidence_event_ids=json.dumps(evidence_ids),
                    computed_at=now,
                    pipeline_version=PIPELINE_VERSION,
                )
            )
        count += 1

    logger.info("spikes upserted", extra={"count": count})
    return count


def run_day2_pipeline(session: Session) -> None:
    """Run all Day 2 steps: rolling + z-score, severity baseline, risk scores, spike detection."""
    compute_rolling_and_zscore(session)
    compute_severity_baseline(session)
    compute_risk_scores(session)
    detect_spikes(session)
