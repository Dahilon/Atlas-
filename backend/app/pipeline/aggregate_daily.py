"""
Aggregate events into daily_metrics (date x country x category).

Phase 1: Adds severity layer — mean_goldstein, min_goldstein, mean_tone,
pct_negative_tone, severity_index (0-100 explainable weighted combo of
negative goldstein magnitude, negative tone, quad_class intensity).
"""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from ..models import Event, DailyMetric

logger = logging.getLogger("events-risk-dashboard.aggregate")

# Severity index weights (explainable): neg_goldstein, neg_tone, quad_intensity
SEV_WEIGHT_GOLDSTEIN = 0.4
SEV_WEIGHT_TONE = 0.3
SEV_WEIGHT_QUAD = 0.3


def _severity_index_row(
    min_goldstein: float | None,
    mean_tone: float | None,
    pct_negative_tone: float,
    quad_intensity: float,
) -> float | None:
    """
    Compute 0-100 severity index from components.
    neg_goldstein_norm: max(0, -min_goldstein)/10 capped at 1.
    neg_tone_norm: pct_negative_tone (0-1) or magnitude from mean_tone when < 0.
    quad_intensity_norm: quad_intensity already 0-1 (mean of quad_class/4).
    """
    if min_goldstein is not None and not pd.isna(min_goldstein):
        neg_g = min(1.0, max(0.0, -min_goldstein) / 10.0)
    else:
        neg_g = 0.5  # neutral when missing
    if mean_tone is not None and not pd.isna(mean_tone) and mean_tone < 0:
        neg_t = min(1.0, -mean_tone / 100.0)
    else:
        neg_t = float(pct_negative_tone) if pct_negative_tone is not None else 0.0
    q = min(1.0, max(0.0, float(quad_intensity))) if quad_intensity is not None else 0.0
    return round(100.0 * (SEV_WEIGHT_GOLDSTEIN * neg_g + SEV_WEIGHT_TONE * neg_t + SEV_WEIGHT_QUAD * q), 2)


def aggregate_daily_metrics(session: Session) -> int:
    """
    Aggregate events into daily_metrics for all available dates.
    Includes severity layer: mean_goldstein, min_goldstein, mean_tone,
    pct_negative_tone, severity_index. Bulk write.
    """
    logger.info("aggregating daily metrics")

    stmt = select(
        Event.date,
        Event.country,
        Event.category,
        Event.avg_tone,
        Event.goldstein,
        Event.quad_class,
    ).where(Event.category.isnot(None))

    rows = session.execute(stmt).all()
    if not rows:
        logger.info("no events to aggregate")
        return 0

    df = pd.DataFrame(
        rows,
        columns=["date", "country", "category", "avg_tone", "goldstein", "quad_class"],
    )
    df["country"] = df["country"].fillna("XX").replace("", "XX")
    df["quad_class"] = pd.to_numeric(df["quad_class"], errors="coerce")
    df["quad_frac"] = (df["quad_class"] / 4.0).clip(0, 1).fillna(0)
    df["negative_tone"] = (df["avg_tone"] < 0).astype(float)

    grouped = (
        df.groupby(["date", "country", "category"])
        .agg(
            event_count=("date", "size"),
            avg_tone=("avg_tone", "mean"),
            mean_goldstein=("goldstein", "mean"),
            min_goldstein=("goldstein", "min"),
            pct_negative_tone=("negative_tone", "mean"),
            quad_intensity=("quad_frac", "mean"),
        )
        .reset_index()
    )
    grouped["mean_tone"] = grouped["avg_tone"]
    grouped["severity_index"] = grouped.apply(
        lambda r: _severity_index_row(
            r.get("min_goldstein"),
            r.get("mean_tone"),
            r.get("pct_negative_tone", 0),
            r.get("quad_intensity", 0),
        ),
        axis=1,
    )

    session.execute(delete(DailyMetric))
    count = 0
    for _, row in grouped.iterrows():
        dm = DailyMetric(
            date=row["date"],
            country=row["country"],
            category=row["category"],
            event_count=int(row["event_count"]),
            avg_tone=float(row["avg_tone"]) if pd.notna(row["avg_tone"]) else None,
            mean_tone=float(row["mean_tone"]) if pd.notna(row["mean_tone"]) else None,
            mean_goldstein=float(row["mean_goldstein"]) if pd.notna(row["mean_goldstein"]) else None,
            min_goldstein=float(row["min_goldstein"]) if pd.notna(row["min_goldstein"]) else None,
            pct_negative_tone=float(row["pct_negative_tone"]) if pd.notna(row["pct_negative_tone"]) else None,
            severity_index=float(row["severity_index"]) if pd.notna(row["severity_index"]) else None,
        )
        session.add(dm)
        count += 1

    logger.info("finished aggregating daily metrics", extra={"rows": count})
    return count
