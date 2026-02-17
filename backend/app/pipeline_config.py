"""
Day 2 pipeline configuration. All values overridable via environment variables.
"""
from __future__ import annotations

import os

# Baseline: "robust" (median + MAD) or "standard" (mean + std)
_def_bm = os.getenv("BASELINE_METHOD", "robust").lower()
BASELINE_METHOD: str = _def_bm if _def_bm in ("robust", "standard") else "robust"

BASELINE_WINDOW_DAYS_SHORT: int = int(os.getenv("BASELINE_WINDOW_DAYS_SHORT", "14"))
BASELINE_WINDOW_DAYS_LONG: int = int(os.getenv("BASELINE_WINDOW_DAYS_LONG", "56"))
BASELINE_MIN_PERIODS: int = int(os.getenv("BASELINE_MIN_PERIODS", "7"))

# Robust z-score: scale so comparable to standard normal (0.6745 is the scaling constant for MAD)
MAD_SCALE_FOR_NORMAL: float = 0.6745

# Spike detection
Z_SPIKE_THRESHOLD: float = float(os.getenv("Z_SPIKE_THRESHOLD", "2.0"))
# "one_sided" => use z_up = max(0, z_score); "two_sided" => use |z_score|
_def_sm = os.getenv("SPIKE_MODE", "one_sided").lower()
SPIKE_MODE: str = _def_sm if _def_sm in ("one_sided", "two_sided") else "one_sided"

SPIKE_EVIDENCE_N: int = int(os.getenv("SPIKE_EVIDENCE_N", "5"))

# Audit
PIPELINE_VERSION: str = os.getenv("PIPELINE_VERSION", "v2.0")
