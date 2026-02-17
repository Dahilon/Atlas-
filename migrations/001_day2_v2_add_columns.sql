-- Migration: Add Day 2 v2 columns for robust baseline, risk, and spike audit.
-- Run against your SQLite DB (e.g. backend/events.db) when upgrading from pre-v2 schema.
-- New installs: Base.metadata.create_all() will create tables with all columns; this file is for existing DBs.

-- daily_metrics: add new columns (ignore if already present)
ALTER TABLE daily_metrics ADD COLUMN rolling_center REAL;
ALTER TABLE daily_metrics ADD COLUMN rolling_dispersion REAL;
ALTER TABLE daily_metrics ADD COLUMN baseline_quality TEXT;
ALTER TABLE daily_metrics ADD COLUMN baseline_method TEXT;
ALTER TABLE daily_metrics ADD COLUMN baseline_window_days INTEGER;
ALTER TABLE daily_metrics ADD COLUMN computed_at TEXT;
ALTER TABLE daily_metrics ADD COLUMN pipeline_version TEXT;

-- spikes: add new columns (if table already exists without them)
ALTER TABLE spikes ADD COLUMN z_used REAL;
ALTER TABLE spikes ADD COLUMN rolling_center REAL;
ALTER TABLE spikes ADD COLUMN rolling_dispersion REAL;
ALTER TABLE spikes ADD COLUMN baseline_quality TEXT;
ALTER TABLE spikes ADD COLUMN baseline_method TEXT;
ALTER TABLE spikes ADD COLUMN baseline_window_days INTEGER;
ALTER TABLE spikes ADD COLUMN computed_at TEXT;
ALTER TABLE spikes ADD COLUMN pipeline_version TEXT;

-- Note: SQLite does not support adding a UNIQUE constraint via ALTER TABLE.
-- For new databases, create_all() will create spikes with UNIQUE(date, country, category, baseline_method, baseline_window_days, pipeline_version).
-- For existing DBs, upsert is enforced in application code only.
