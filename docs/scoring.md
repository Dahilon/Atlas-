# Risk Scoring (Day 2)

## Overview

Risk scores are computed per (date, country, category) and stored in `daily_metrics.risk_score` (0–100). Each row has a `reasons_json` field explaining the components.

## Formula (v1)

- **Base weight** by category (severity):
  - Armed Conflict: 25  
  - Crime / Terror: 20  
  - Civil Unrest, Infrastructure/Energy: 15  
  - Economic Disruption: 12  
  - Diplomacy / Sanctions: 8  
  - Other: 10  

- **Recency multiplier**:  
  - Last 7 days: 1.5×  
  - Last 14 days: 1.2×  
  - Older: 1.0×  

- **Spike bonus**: if |z_score| > 1, add `min(25, (|z| - 1) * 10)`.

- **Final**: `risk_score = min(100, base * recency_mult + spike_bonus)`.

## Rolling baseline and z-score

- For each (country, category), we compute a **14-day rolling mean and std** of `event_count`.
- **z_score** = (event_count − rolling_mean) / rolling_std (when rolling_std > 0).
- **Spikes** are (date, country, category) where |z_score| > 2.0; stored in `spikes` with sample `evidence_event_ids`.

## Evidence

- Every spike links to up to 5 event IDs for that (date, country, category); use `GET /events` with filters to resolve URLs and headlines.
