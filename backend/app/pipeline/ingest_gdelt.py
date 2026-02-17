from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import List

import urllib3
import requests

from ..config import config

# Suppress warning when skipping SSL verify for GDELT (public data, known cert quirk)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("events-risk-dashboard.ingest")


def _build_export_url(day: date) -> str:
    datestr = day.strftime("%Y%m%d")
    return f"{config.gdelt_events_base_url}/{datestr}.export.CSV.zip"


def download_daily_exports(
    days: int,
    *,
    redownload_latest: bool = False,
) -> List[Path]:
    """
    Download the last N days of GDELT daily events exports.

    Args:
        days: Number of days to fetch (today - 1, today - 2, ...).
        redownload_latest: If True, always re-download the most recent day's file
            (offset 0), so you get GDELT's latest updates. Use for live/scheduled ingest.

    Returns a list of paths to the downloaded ZIP files.
    """
    config.raw_data_dir.mkdir(parents=True, exist_ok=True)

    today = date.today()
    paths: List[Path] = []

    for offset in range(days):
        target_day = today - timedelta(days=offset + 1)
        datestr = target_day.strftime("%Y%m%d")
        url = _build_export_url(target_day)
        dest = config.raw_data_dir / f"{datestr}.export.CSV.zip"

        skip_existing = dest.exists() and not (redownload_latest and offset == 0)
        if skip_existing:
            logger.info("raw file already exists; skipping download", extra={"path": str(dest)})
            paths.append(dest)
            continue

        logger.info("downloading gdelt export", extra={"url": url, "path": str(dest)})
        # GDELT data server can trigger hostname mismatch on SSL verify; skip for this public data only
        resp = requests.get(url, timeout=60, verify=False)
        if resp.status_code != 200:
            logger.warning(
                "failed to download gdelt export",
                extra={"url": url, "status_code": resp.status_code},
            )
            continue

        dest.write_bytes(resp.content)
        logger.info(
            "downloaded gdelt export",
            extra={"url": url, "path": str(dest), "bytes": len(resp.content)},
        )
        paths.append(dest)

    return paths

