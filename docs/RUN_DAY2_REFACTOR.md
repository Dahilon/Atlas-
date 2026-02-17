# Day 2 v2 Refactor: Run Instructions & Reference

## Files changed

| File | Change |
|------|--------|
| `backend/app/pipeline_config.py` | **New.** Env-overridable config: BASELINE_METHOD, BASELINE_MIN_PERIODS, Z_SPIKE_THRESHOLD, SPIKE_MODE, SPIKE_EVIDENCE_N, PIPELINE_VERSION, etc. |
| `backend/app/models.py` | DailyMetric: added rolling_center, rolling_dispersion, baseline_quality, baseline_method, baseline_window_days, computed_at, pipeline_version. Spike: added z_used, rolling_center, rolling_dispersion, baseline_quality, baseline_method, baseline_window_days, computed_at, pipeline_version; UNIQUE(date, country, category, baseline_method, baseline_window_days, pipeline_version). |
| `backend/app/pipeline/day2_baselines_risk.py` | **Rewritten.** Step 4: robust (median+MAD 0.6745) or standard, min_periods=7, baseline_quality, variance floor, bulk_update_mappings. Step 5: z_used (one_sided/two_sided), reasons_json components, bulk update. Step 6: Spike UPSERT (no delete), evidence by \|avg_tone\| desc, all audit fields. |
| `backend/app/schemas.py` | MetricResponse and SpikeResponse extended with new optional fields. |
| `backend/app/routes/metrics.py` | Returns rolling_center, rolling_dispersion, baseline_quality, baseline_method, computed_at, pipeline_version. |
| `backend/app/routes/spikes.py` | Returns z_used, rolling_center, rolling_dispersion, baseline_quality, baseline_method, computed_at, pipeline_version. |
| `migrations/001_day2_v2_add_columns.sql` | **New.** SQL to add new columns to existing SQLite DB. |
| `tests/test_day2_baselines_risk.py` | **New.** Unit tests: robust z (MAD=0), baseline_quality, one_sided z_used, spike upsert no duplicate. |

---

## Migration SQL

For an **existing** database (you already have `daily_metrics` and `spikes`), run the migration to add columns. From project root:

```bash
sqlite3 backend/events.db < migrations/001_day2_v2_add_columns.sql
```

If a column already exists, SQLite will error on that line; you can run the `ALTER TABLE` lines one by one and skip any that fail. For a **new** database, just start the app (or run the pipeline); `Base.metadata.create_all()` will create tables with all columns and the Spike unique constraint.

---

## How to run the pipeline locally

1. **Activate venv and install deps** (if not already):
   ```bash
   cd "/Users/dusitmohammed/Global Events Risk Intelligence Dashboard"
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Ensure Day 1 has run** (so `daily_metrics` is populated):
   ```bash
   python -m backend.app.pipeline.run_day1 --days 14
   ```

3. **Run Day 2** (rolling baseline, risk scores, spikes):
   ```bash
   python -m backend.app.pipeline.run_day2
   ```

4. **Optional env overrides** (before step 3):
   ```bash
   export BASELINE_METHOD=robust    # or standard
   export BASELINE_MIN_PERIODS=7
   export SPIKE_MODE=one_sided      # or two_sided
   export Z_SPIKE_THRESHOLD=2.0
   export PIPELINE_VERSION=v2.0
   python -m backend.app.pipeline.run_day2
   ```

5. **Start API and try endpoints**:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
   Then open `http://127.0.0.1:8000/docs` and call `GET /metrics`, `GET /spikes`, `GET /brief`.

---

## Example queries to inspect spikes and daily_metrics

Using SQLite from the shell:

```bash
sqlite3 backend/events.db
```

**Spikes (last 10) with key fields:**
```sql
SELECT date, country, category, z_score, z_used, delta,
       rolling_center, rolling_dispersion, baseline_quality,
       baseline_method, pipeline_version, computed_at
FROM spikes
ORDER BY date DESC, z_used DESC
LIMIT 10;
```

**Daily metrics with baseline and risk (one country):**
```sql
SELECT date, country, category, event_count,
       rolling_center, rolling_dispersion, baseline_quality, z_score,
       risk_score, pipeline_version
FROM daily_metrics
WHERE country = 'US'
ORDER BY date DESC
LIMIT 20;
```

**Count of spikes by pipeline_version:**
```sql
SELECT pipeline_version, baseline_method, COUNT(*) AS n
FROM spikes
GROUP BY pipeline_version, baseline_method;
```
