-- Phase 1 Severity Layer: events.goldstein + daily_metrics severity columns.
-- Run once against existing DB. New DBs get these from create_all().

-- Events: GDELT Goldstein scale (-10 to +10)
ALTER TABLE events ADD COLUMN goldstein REAL;

-- daily_metrics: severity layer
ALTER TABLE daily_metrics ADD COLUMN mean_goldstein REAL;
ALTER TABLE daily_metrics ADD COLUMN min_goldstein REAL;
ALTER TABLE daily_metrics ADD COLUMN mean_tone REAL;
ALTER TABLE daily_metrics ADD COLUMN pct_negative_tone REAL;
ALTER TABLE daily_metrics ADD COLUMN severity_index REAL;
ALTER TABLE daily_metrics ADD COLUMN severity_rolling_center REAL;
ALTER TABLE daily_metrics ADD COLUMN severity_rolling_dispersion REAL;
ALTER TABLE daily_metrics ADD COLUMN z_severity REAL;
ALTER TABLE daily_metrics ADD COLUMN percentile_180d REAL;
