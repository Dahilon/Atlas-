"""
Phase 1 Severity Layer: severity_index, z_severity, risk formula and reasons_json.
Run from project root: python -m pytest backend/tests/test_phase1_severity.py -v
"""
import json
import os
import sys
import unittest
from pathlib import Path

# Project root on path so "backend.app" resolves
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

os.environ.setdefault("BASELINE_METHOD", "robust")
os.environ.setdefault("SPIKE_MODE", "one_sided")

from backend.app.pipeline.aggregate_daily import _severity_index_row


class TestSeverityIndex(unittest.TestCase):
    """severity_index is 0-100 and explainable from components."""

    def test_severity_index_high_when_negative_goldstein_and_tone(self):
        # min_goldstein -8 => neg_g=0.8, mean_tone -50 => neg_t=0.5, quad=0.5
        si = _severity_index_row(min_goldstein=-8, mean_tone=-50, pct_negative_tone=0.6, quad_intensity=0.5)
        self.assertIsNotNone(si)
        self.assertGreaterEqual(si, 0)
        self.assertLessEqual(si, 100)
        self.assertGreater(si, 50)

    def test_severity_index_low_when_positive_goldstein(self):
        si = _severity_index_row(min_goldstein=5, mean_tone=10, pct_negative_tone=0, quad_intensity=0)
        self.assertIsNotNone(si)
        self.assertLess(si, 30)


class TestReasonsJsonSeverityFields(unittest.TestCase):
    """reasons_json from risk scoring includes severity_component, z_severity, severity_index."""

    def test_reasons_contain_severity_fields(self):
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from backend.app.models import Base, DailyMetric
        from backend.app.pipeline.day2_baselines_risk import compute_risk_scores, compute_rolling_and_zscore, compute_severity_baseline

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        # One row with enough history (baseline_quality will be ok after rolling) and severity_index
        from datetime import date, timedelta
        base_d = date.today() - timedelta(days=30)
        for i in range(14):
            d = base_d + timedelta(days=i)
            session.add(
                DailyMetric(
                    date=d,
                    country="US",
                    category="Armed Conflict",
                    event_count=20 + i,
                    avg_tone=-5.0,
                    mean_tone=-5.0,
                    severity_index=60.0,
                )
            )
        session.commit()

        compute_rolling_and_zscore(session)
        compute_severity_baseline(session)
        compute_risk_scores(session)
        session.commit()

        m = session.execute(
            select(DailyMetric).where(DailyMetric.country == "US", DailyMetric.baseline_quality == "ok").limit(1)
        ).scalars().first()
        self.assertIsNotNone(m, "at least one row should have baseline_quality ok after 14 days")
        self.assertIsNotNone(m.reasons_json)
        reasons = json.loads(m.reasons_json)
        self.assertIn("severity_component", reasons)
        self.assertIn("severity_multiplier", reasons)
        self.assertIn("severity_index", reasons)
        self.assertIn("z_severity", reasons)
        self.assertIn("z_count", reasons)
        session.close()
