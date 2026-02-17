# How Step 4, 5, and 6 Work (and How Well)

## Step 4: Rolling baseline and z-score

**What we do (in code):**

1. Load **all** rows from `daily_metrics`, ordered by `(country, category, date)`.
2. Turn them into a pandas DataFrame with columns: `id`, `date`, `country`, `category`, `event_count`.
3. **Group by (country, category)** and, within each group, compute a **rolling window** over the **last 14 days** of `event_count`:
   - **rolling_mean** = mean of event_count in that window  
   - **rolling_std** = standard deviation in that window  
   We use `min_periods=1` so the first few days still get a value (with 1 day, std is NaN, so z_score stays null).
4. **Z-score** for each row:  
   `z_score = (event_count - rolling_mean) / rolling_std`  
   Only when `rolling_std > 0` (otherwise we’d divide by zero).
5. Write **rolling_mean**, **rolling_std**, and **z_score** back onto each `daily_metrics` row (matched by `id`).

**In short:** For each (country, category), we compare each day’s event count to the “normal” level over the last 14 days. The z-score says “how many standard deviations above or below normal” that day is.

---

## Step 5: Risk scoring

**What we do (in code):**

1. Load every `daily_metrics` row again (we already have `z_score` from step 4).
2. For **each row** we compute:
   - **base** = fixed weight for that category (e.g. Armed Conflict = 25, Diplomacy = 8). Stored in `CATEGORY_WEIGHTS`.
   - **recency_mult** = 1.5 if the row’s date is in the last 7 days, 1.2 if 8–14 days, 1.0 otherwise.
   - **spike_bonus** = if `|z_score| > 1`, we add `min(25, (|z_score| - 1) * 10)`; otherwise 0.
   - **raw** = base × recency_mult + spike_bonus  
   - **risk_score** = min(100, round(raw, 1))
3. We store **risk_score** and a **reasons_json** object like  
   `{ "base": 25, "recency_mult": 1.5, "spike_bonus": 12, "z_score": 2.3 }`  
   so you can see exactly how the number was built.

**In short:** Risk is “how bad is this category” (base) × “how recent” (recency) + “how unusual is this day” (spike bonus), capped at 100. Everything is explainable via `reasons_json`.

---

## Step 6: Spike detection

**What we do (in code):**

1. **Clear** the `spikes` table (we recompute from current `daily_metrics`).
2. Select all `daily_metrics` rows where **z_score is not null** and **|z_score| > 2.0** (configurable `Z_SPIKE_THRESHOLD`).
3. For each such row we create a **Spike** record with:
   - same **date, country, category**
   - **z_score**, and **delta** = (event_count − rolling_mean)
   - **evidence_event_ids** = JSON array of up to **5 event IDs** from the `events` table for that (date, country, category), so you can link back to real events/URLs.

**In short:** Any (date, country, category) that is more than 2 standard deviations above or below its 14-day norm is written to `spikes`, with a few example event IDs for evidence.

---

## How well does it work?

**What works well:**

- **Simple and interpretable:** Rolling mean/std and z-score are standard; risk is a transparent formula. No black box.
- **Evidence:** Every spike points to specific event IDs; you can resolve them to headlines/URLs via the events table/API.
- **Tunable:** You can change `ROLLING_WINDOW_DAYS`, `Z_SPIKE_THRESHOLD`, and `CATEGORY_WEIGHTS` without changing the structure.

**Limitations:**

- **Only 7–14 days of data:** With few days, rolling stats are noisy; the first days have little history, so z-scores and spikes are less reliable until you have at least ~14 days.
- **Volume only:** We only look at **count** of events. We don’t use tone or Goldstein scale in the baseline or z-score (we could add that later).
- **No seasonality:** Weekdays vs weekends, holidays, etc. are not modelled; a “spike” might sometimes be normal variation.
- **Category noise:** GDELT and our taxonomy mapping can misclassify; that affects both risk and which categories spike.
- **Daily data:** We use daily GDELT batches, so we see at least a one-day delay and no true real-time signal.

**Bottom line:** For a portfolio v1 it’s solid: the pipeline is clear, explainable, and traceable. For production you’d want more history (e.g. 30+ days), optional tone/severity in the baseline, and tests on known events to tune the threshold and weights.
