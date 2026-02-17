from __future__ import annotations

import argparse
import logging

from ..db import get_db_session
from .ingest_gdelt import download_daily_exports
from .normalize import normalize_many
from .aggregate_daily import aggregate_daily_metrics
from ..config import config
from ..logging_config import setup_logging, logger


def run_pipeline(days: int) -> None:
    """
    Run the full Day 1 pipeline:
    - download last N days of GDELT exports
    - normalize into events table
    - aggregate into daily_metrics
    """
    setup_logging()

    logger.info("starting day1 pipeline", extra={"days": days})

    zips = download_daily_exports(days=days)
    if not zips:
        logger.warning("no gdelt zip files downloaded - nothing to process")
        return

    with get_db_session() as session:
        inserted = normalize_many(zips, session=session)
        logger.info("normalized events", extra={"inserted": inserted})

        metrics_rows = aggregate_daily_metrics(session=session)
        logger.info("aggregated daily metrics", extra={"rows": metrics_rows})

    logger.info("day1 pipeline completed")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run Day 1 GDELT ingestion + normalization + aggregation pipeline.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=config.default_ingest_days,
        help="Number of days of GDELT daily exports to ingest (default: %(default)s).",
    )
    args = parser.parse_args()
    run_pipeline(days=args.days)


if __name__ == "__main__":
    main()

