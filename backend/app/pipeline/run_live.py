"""
Live ingest pipeline (Step 1): incremental GDELT pull + full refresh of metrics and risk.

Run on a schedule (e.g. cron every 6h):
  - Download latest 1–2 days of GDELT exports (optionally re-download latest day for updates).
  - Normalize into events (upsert by event ID — no duplicates).
  - Re-aggregate daily_metrics from all events, then run Day 2 (baselines, risk, spikes).
  - Optionally append risk snapshots for history.

Requires an initial Day 1 run (e.g. run_day1 --days 14) so the DB has enough history for rolling baselines.
"""
from __future__ import annotations

import argparse
import logging

from ..config import config
from ..db import get_db_session
from ..logging_config import setup_logging, logger
from .ingest_gdelt import download_daily_exports
from .normalize import normalize_many
from .aggregate_daily import aggregate_daily_metrics
from .day2_baselines_risk import run_day2_pipeline


def run_live_pipeline(snapshot: bool = True) -> None:
    """
    Run live ingest: download latest days → normalize (upsert) → aggregate → Day 2 → optional snapshot.
    """
    setup_logging()

    logger.info(
        "starting live ingest pipeline",
        extra={
            "live_ingest_days": config.live_ingest_days,
            "redownload_latest": config.live_redownload_latest,
        },
    )

    zips = download_daily_exports(
        days=config.live_ingest_days,
        redownload_latest=config.live_redownload_latest,
    )
    if not zips:
        logger.warning("no gdelt zip files from live ingest - nothing to process")
        return

    with get_db_session() as session:
        inserted = normalize_many(zips, session=session)
        logger.info("normalized events (upsert)", extra={"inserted": inserted})

        metrics_rows = aggregate_daily_metrics(session=session)
        logger.info("aggregated daily metrics", extra={"rows": metrics_rows})

        run_day2_pipeline(session)
        logger.info("day2 pipeline (baselines, risk, spikes) completed")

        if snapshot:
            try:
                from .risk_snapshots import append_risk_snapshots

                appended = append_risk_snapshots(session)
                logger.info("risk snapshots appended", extra={"rows": appended})
            except Exception as e:  # noqa: BLE001
                logger.warning("risk snapshots skipped", extra={"error": str(e)})

    logger.info("live ingest pipeline completed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run live GDELT ingest + normalization + aggregation + Day 2 (+ optional risk snapshots).",
    )
    parser.add_argument(
        "--no-snapshot",
        action="store_true",
        help="Skip appending risk snapshots for history.",
    )
    args = parser.parse_args()
    run_live_pipeline(snapshot=not args.no_snapshot)


if __name__ == "__main__":
    main()
