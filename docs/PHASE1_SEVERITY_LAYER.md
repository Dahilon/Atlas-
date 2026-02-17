# Phase 1 — Severity Layer: Schema & Data Flow

## 1. Schema changes

### 1.1 Event (existing table — extend)

| Column       | Type   | Notes                                      |
|-------------|--------|--------------------------------------------|
| goldstein   | Float  | **NEW.** GDELT Goldstein scale (-10 to +10). |

Needed so we can aggregate severity components in daily_metrics. Normalization already reads `IDX_GOLDSTEIN`; we persist it.

### 1.2 daily_metrics (extend)

| Column             | Type    | Notes |
|--------------------|---------|--------|
| mean_goldstein     | Float   | **NEW.** Mean Goldstein for (date, country, category). |
| min_goldstein      | Float   | **NEW.** Min Goldstein (most negative = most conflict). |
| mean_tone          | Float   | **NEW.** Mean avg_tone (alias/dup of avg_tone for clarity; we keep avg_tone for backward compat). |
| pct_negative_tone  | Float   | **NEW.** Fraction of events with avg_tone < 0 (0–1). |
| severity_index     | Float   | **NEW.** Explainable 0–100 score (see formula below). |
| z_severity         | Float   | **NEW.** Robust z-score of severity_index vs rolling baseline. |
| percentile_180d    | Float   | **NEW, optional.** Percentile of severity_index over last 180 days (null if &lt; 180d). Deferred: column exists, not yet computed. |

Existing columns (event_count, avg_tone, rolling_center, rolling_dispersion, z_score, risk_score, reasons_json, etc.) unchanged.

### 1.3 severity_index formula (explainable)

- **neg_goldstein**: If mean/min goldstein is negative, use magnitude. We use `neg_goldstein_raw = max(0, -min_goldstein) / 10` so 0–1 (min_goldstein = -10 → 1).
- **neg_tone**: `pct_negative_tone` (0–1) or a score from mean_tone when &lt; 0: e.g. `max(0, -mean_tone) / 100`.
- **quad_intensity**: From events: share of events in quad_class 3 or 4, or mean(quad_class/4). We use `mean(quad_class/4)` if we have quad_class in aggregation; else omit or use 0.5.

Define:

```
severity_index = 100 * (0.4 * neg_goldstein_norm + 0.3 * neg_tone_norm + 0.3 * quad_intensity_norm)
```

All components 0–1 so severity_index in 0–100. Stored in daily_metrics; used for z_severity (robust baseline on log1p(severity_index) or raw) and in risk.

### 1.4 risk_score refactor

Current: `risk = base_component * recency_component + anomaly_component`.

New:

```
severity_multiplier = 0.7 + 0.3 * (severity_index / 100)   # 0.7–1.0
risk = base_weight * recency_mult * severity_multiplier + spike_bonus
cap at 100
```

reasons_json extended with:

- `severity_component`, `z_count`, `z_severity`
- `severity_index`, `severity_multiplier`
- existing: `base_component`, `recency_component`, `anomaly_component`, `z_score`, `z_used`, `spike_bonus`, `baseline_method`, `baseline_window_days`

---

## 2. Data flow (Phase 1)

```
Events (with goldstein, quad_class, avg_tone)
    │
    ▼
aggregate_daily_metrics (extended)
    │  event_count, avg_tone, mean_tone, mean_goldstein, min_goldstein,
    │  pct_negative_tone, quad_intensity → severity_index (0–100)
    ▼
daily_metrics (new columns populated)
    │
    ▼
compute_rolling_and_zscore (existing: event_count → z_score)
    │
    ▼
compute_severity_baseline (NEW step)
    │  Rolling median + MAD on severity_index (or log1p); z_severity; baseline_quality same as count
    ▼
compute_risk_scores (refactored)
    │  severity_multiplier from severity_index; risk = base*recency*severity_mult + spike_bonus
    │  reasons_json includes severity_component, z_count, z_severity
    ▼
detect_spikes (unchanged)
```

---

## 3. Pipeline steps (modular)

1. **aggregate_daily_metrics**  
   - Select Event: date, country, category, avg_tone, goldstein, quad_class.  
   - Group by (date, country, category).  
   - Aggregates: event_count, mean(avg_tone)=mean_tone, mean(goldstein)=mean_goldstein, min(goldstein)=min_goldstein, pct_negative_tone = mean(avg_tone &lt; 0), quad_intensity = mean(quad_class/4) with nulls→0.  
   - Compute severity_index (0–100) per group.  
   - Bulk insert/update daily_metrics (clear + repopulate or UPSERT by date, country, category).

2. **compute_rolling_and_zscore**  
   - Unchanged for event_count → rolling_center, rolling_dispersion, z_score.

3. **compute_severity_baseline** (new)  
   - Load daily_metrics (id, country, category, date, severity_index).  
   - Group by (country, category); rolling median + MAD on severity_index (or log1p(severity_index+1)); min_periods=7.  
   - z_severity = 0.6745 * (x - median) / MAD when MAD &gt; 0 and baseline_quality == "ok".  
   - Bulk update daily_metrics (severity_rolling_center, severity_rolling_dispersion, z_severity). We can reuse baseline_quality from count baseline.

4. **compute_risk_scores**  
   - For each row: severity_multiplier = 0.7 + 0.3 * (severity_index/100).  
   - risk = base_weight * recency_mult * severity_multiplier + spike_bonus; cap 100.  
   - reasons_json includes severity_index, severity_multiplier, z_severity, z_count (z_score), plus existing fields.

5. **detect_spikes**  
   - Unchanged.

---

## 4. API & contracts

- **GET /metrics**: Add optional fields mean_goldstein, min_goldstein, mean_tone, pct_negative_tone, severity_index, z_severity, percentile_180d (optional). Existing fields unchanged.
- **GET /brief**: Extend top_movers with severity_index and z_severity when present; summary can mention severity.
- No breaking changes to existing response shapes; only additive fields.

---

## 5. Migration SQL (Phase 1)

- **events**: `ALTER TABLE events ADD COLUMN goldstein REAL;`
- **daily_metrics**: Add columns mean_goldstein, min_goldstein, mean_tone, pct_negative_tone, severity_index, z_severity, percentile_180d (all nullable). Optional: severity_rolling_center, severity_rolling_dispersion if we store them.

Implementing Phase 1 next: Event.goldstein, aggregation extension, daily_metrics new columns, severity baseline step, risk refactor, migration, schemas, brief.
