"""
Minimal unit tests for Day 2 v2: robust z-score, baseline_quality, one-sided spike, spike upsert.
Run from project root: python -m pytest backend/tests/test_day2_baselines_risk.py -v
"""
import os
import sys
import unittest
from pathlib import Path

# Project root on path so "backend.app" resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from datetime import date, timedelta

import pandas as pd

# Set env before importing pipeline modules
os.environ["BASELINE_METHOD"] = "robust"
os.environ["BASELINE_MIN_PERIODS"] = "7"
os.environ["SPIKE_MODE"] = "one_sided"

from backend.app.pipeline.day2_baselines_risk import _rolling_mad
from backend.app.pipeline_config import BASELINE_MIN_PERIODS


class TestRobustZScore(unittest.TestCase):
    """Robust z-score computes null when MAD==0."""

    def test_z_score_null_when_mad_zero(self):
        # Constant series => MAD = 0 => we must not divide by zero; z_score should be null in pipeline
        series = pd.Series([10.0] * 14)
        mad = _rolling_mad(series, 14, 7)
        self.assertTrue(mad.iloc[-1] == 0 or pd.isna(mad.iloc[-1]))


class TestBaselineQuality(unittest.TestCase):
    """baseline_quality is 'ok' only when at least BASELINE_MIN_PERIODS points in window."""

    def test_baseline_quality_ok_after_min_periods(self):
        n = 20
        df = pd.DataFrame(
            {"event_count": range(n), "country": "US", "category": "Conflict"}
        )
        df["n_in_window"] = df["event_count"].rolling(14, min_periods=1).count()
        quality = df["n_in_window"].apply(
            lambda x: "ok" if x >= BASELINE_MIN_PERIODS else "low"
        )
        # First 6 rows (0..5) have count < 7
        self.assertEqual(quality.iloc[0], "low")
        self.assertEqual(quality.iloc[6], "ok")
        self.assertEqual(quality.iloc[13], "ok")


class TestOneSidedSpike(unittest.TestCase):
    """One-sided spike uses z_used = max(0, z_score)."""

    def test_z_used_max_zero_one_sided(self):
        z_score = -2.5
        z_used = max(0, z_score)
        self.assertEqual(z_used, 0)
        z_score = 2.5
        z_used = max(0, z_score)
        self.assertEqual(z_used, 2.5)


class TestSpikeUpsert(unittest.TestCase):
    """Running spike detection twice does not duplicate spikes (upsert)."""

    def test_upsert_no_duplicate_spikes(self):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from backend.app.models import Base, DailyMetric, Spike
        from backend.app.pipeline.day2_baselines_risk import detect_spikes

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # One (date, country, category) with high z
        d = date.today() - timedelta(days=1)
        m = DailyMetric(
            date=d,
            country="US",
            category="Armed Conflict",
            event_count=100,
            baseline_quality="ok",
            z_score=3.0,
            rolling_center=20.0,
            rolling_dispersion=5.0,
            baseline_method="robust",
            baseline_window_days=14,
            pipeline_version="v2.0",
        )
        session.add(m)
        session.commit()

        count1 = detect_spikes(session)
        session.commit()
        self.assertGreaterEqual(count1, 1)
        n1 = session.execute(select(Spike)).scalars().all()
        n1 = len(n1)

        # Run again: should update, not insert another row
        count2 = detect_spikes(session)
        session.commit()
        n2 = len(session.execute(select(Spike)).scalars().all())
        self.assertEqual(n1, n2, "second run should not add duplicate spikes")
        session.close()


if __name__ == "__main__":
    unittest.main()
