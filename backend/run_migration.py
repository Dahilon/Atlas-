#!/usr/bin/env python3
"""
One-off migration: add Day 2 v2 columns to existing SQLite DB.
Uses the same engine as the app so it targets the correct database.
Run from project root: python backend/run_migration.py
"""
import sqlite3
import sys
from pathlib import Path

# Project root on path so backend.app resolves
_root = Path(__file__).resolve().parents[1]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from backend.app.db import engine

conn = engine.raw_connection()
cur = conn.cursor()

# Events: Phase 1 goldstein
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='events'")
if cur.fetchone():
    try:
        cur.execute("ALTER TABLE events ADD COLUMN goldstein REAL")
        print("Added events.goldstein")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("Column events.goldstein already exists, skipping")
        else:
            raise

# Columns to add to daily_metrics (ignore if already present)
daily_columns = [
    ("rolling_mean", "REAL"),
    ("rolling_std", "REAL"),
    ("z_score", "REAL"),
    ("risk_score", "REAL"),
    ("reasons_json", "TEXT"),
    ("rolling_center", "REAL"),
    ("rolling_dispersion", "REAL"),
    ("baseline_quality", "TEXT"),
    ("baseline_method", "TEXT"),
    ("baseline_window_days", "INTEGER"),
    ("computed_at", "TEXT"),
    ("pipeline_version", "TEXT"),
    # Phase 1 severity layer
    ("mean_goldstein", "REAL"),
    ("min_goldstein", "REAL"),
    ("mean_tone", "REAL"),
    ("pct_negative_tone", "REAL"),
    ("severity_index", "REAL"),
    ("severity_rolling_center", "REAL"),
    ("severity_rolling_dispersion", "REAL"),
    ("z_severity", "REAL"),
    ("percentile_180d", "REAL"),
]

# Check if daily_metrics exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_metrics'")
if not cur.fetchone():
    print("Table daily_metrics does not exist. Run Day 1 pipeline first.")
    conn.close()
    sys.exit(0)

for col_name, col_type in daily_columns:
    try:
        cur.execute(f"ALTER TABLE daily_metrics ADD COLUMN {col_name} {col_type}")
        print(f"Added daily_metrics.{col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"Column daily_metrics.{col_name} already exists, skipping")
        else:
            raise

# Same for spikes if table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spikes'")
if cur.fetchone():
    spike_columns = [
        ("z_used", "REAL"),
        ("rolling_center", "REAL"),
        ("rolling_dispersion", "REAL"),
        ("baseline_quality", "TEXT"),
        ("baseline_method", "TEXT"),
        ("baseline_window_days", "INTEGER"),
        ("computed_at", "TEXT"),
        ("pipeline_version", "TEXT"),
    ]
    for col_name, col_type in spike_columns:
        try:
            cur.execute(f"ALTER TABLE spikes ADD COLUMN {col_name} {col_type}")
            print(f"Added spikes.{col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print(f"Column spikes.{col_name} already exists, skipping")
            else:
                raise

# Step 1: risk_snapshots for history (live ingest)
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS risk_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date DATE NOT NULL,
        country VARCHAR(2) NOT NULL,
        risk_score REAL,
        severity_index REAL,
        event_count INTEGER,
        created_at TEXT,
        UNIQUE (snapshot_date, country)
    )
    """
)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='risk_snapshots'")
if cur.fetchone():
    print("Table risk_snapshots exists or was created.")

conn.commit()
conn.close()
print("Migration done.")
