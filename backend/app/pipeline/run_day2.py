"""
Run Day 2 pipeline: rolling baselines, z-scores, risk scores, spike detection.

Requires daily_metrics to already be populated (run Day 1 pipeline first).
"""
from __future__ import annotations

import argparse

from ..db import get_db_session
from ..logging_config import setup_logging, logger
from .day2_baselines_risk import run_day2_pipeline


def main() -> None:
    setup_logging()
    parser = argparse.ArgumentParser(description="Day 2: baselines, risk scores, spikes")
    parser.parse_args()
    logger.info("starting day2 pipeline")
    with get_db_session() as session:
        run_day2_pipeline(session)
    logger.info("day2 pipeline completed")


if __name__ == "__main__":
    main()
