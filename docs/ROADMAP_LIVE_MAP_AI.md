# Roadmap: Live Data, Global Map, Spider Web, AI Search & Better Data Science

This document lists all planned enhancements in order. Tackle them one by one; each section is self-contained with goals, steps, and acceptance criteria.

---

## Overview

| # | Feature | Purpose |
|---|---------|--------|
| 1 | Live data API + history | Ingest from API on a schedule; keep history for monitoring |
| 2 | Global map (high severity) | World map showing high-severity / high-risk areas |
| 3 | Actor network (spider web) | Graph of country–country interactions (edges = links) |
| 4 | AI search / chat | Natural-language search (“regime change”, “protests in X”) → events + summary |
| 5 | Better data science | Longer baselines, trends, percentiles, richer signals |

---

## Step 1: Live Data API + Saving History

### Goal
- Ingest events from a live/updated API (e.g. GDELT) on a schedule instead of only batch ZIPs.
- Keep history so you can monitor trends over time.

### Where it fits
- **New ingest path** alongside existing Day 1: same `events` table, append-only.
- **History:** Keep existing tables; optionally add a snapshot table for “risk by country per day” for long-term monitoring.

### Tasks

1. **Research GDELT API**
   - Identify which GDELT endpoint returns recent events (e.g. last 24h, or since timestamp).
   - Note: GDELT 2.0 has different APIs; daily ZIPs are at `https://data.gdeltproject.org/events/`. Check for any JSON/API feed for incremental pull.
   - If no official “live” API, use “download latest 1–2 days” on a schedule as “live enough.”

2. **Add incremental ingest**
   - New script or function: `ingest_live.py` (or extend `ingest_gdelt.py`) that:
     - Calls GDELT API (or downloads only the most recent day’s ZIP).
     - Normalizes into same Event schema (reuse existing normalizer).
     - **Inserts** into `events` (no full table replace); use upsert on event ID to avoid duplicates.
   - Config: `LIVE_INGEST_INTERVAL_MINUTES` or cron schedule.

3. **Schedule the job**
   - Cron job or systemd timer (e.g. every 6 hours): run incremental ingest, then run aggregation + Day 2 for recent dates only (or full Day 2 if fast enough).
   - Alternatively: a small scheduler inside the app (e.g. APScheduler) that runs “ingest + aggregate + day2” every N hours.

4. **History / monitoring**
   - Option A: Rely on existing `daily_metrics` and `spikes` (retain for 90+ days); ensure DB/backups keep history.
   - Option B: Add table `risk_snapshots(date, country, risk_score, severity_index, ...)` and a job that, after Day 2, appends “today’s” per-country risk for long-term time series and dashboards.

### Acceptance criteria
- [ ] Events are added from an API or latest-day file on a schedule (no manual “run day1 --days 14” for latest).
- [ ] No duplicate events when re-running ingest (upsert on event ID).
- [ ] History is retained (existing tables or new snapshot table) for at least 90 days (configurable).

### Files to create/modify
- New: `backend/app/pipeline/ingest_live.py` (or extend `ingest_gdelt.py`).
- Config: add `LIVE_INGEST_SCHEDULE`, `GDELT_API_URL` (if different).
- Optional: new migration for `risk_snapshots`; new endpoint `GET /history/risk?country=US&days=90`.

### Step 1 implementation (done)

- **Config** (`backend/app/config.py`): `live_ingest_days` (default 2), `live_redownload_latest` (default True).
- **Ingest** (`backend/app/pipeline/ingest_gdelt.py`): `download_daily_exports(days, redownload_latest=...)` — when True, re-downloads the most recent day’s ZIP so scheduled runs get GDELT updates.
- **Live runner** (`backend/app/pipeline/run_live.py`): one command runs download → normalize (upsert) → aggregate → Day 2 → optional risk snapshots.
- **History**: `RiskSnapshot` model and `risk_snapshots` table; `backend/app/pipeline/risk_snapshots.py` appends per-country max risk/severity and event_count for the latest date after each Day 2 run.
- **API**: `GET /history/risk?country=US&days=90` returns risk snapshots for monitoring.
- **Migration**: `python backend/run_migration.py` creates `risk_snapshots` if missing.

**How to run and test**

1. **One-time setup**: Run Day 1 so the DB has enough history for rolling baselines:
   ```bash
   cd "Global Events Risk Intelligence Dashboard"
   source .venv/bin/activate   # or your venv
   python -m backend.app.pipeline.run_day1 --days 14
   python backend/run_migration.py   # if not done yet (adds risk_snapshots)
   ```

2. **Live ingest** (incremental pull + full metrics/risk refresh):
   ```bash
   python -m backend.app.pipeline.run_live
   ```
   Use `--no-snapshot` to skip appending risk snapshots.

3. **Schedule it** (e.g. every 6 hours via cron):
   ```bash
   0 */6 * * * cd /path/to/Global\ Events\ Risk\ Intelligence\ Dashboard && .venv/bin/python -m backend.app.pipeline.run_live
   ```

4. **Test the history API**: With the API running (`uvicorn backend.app.main:app --reload`):
   - `GET http://localhost:8000/history/risk?days=30` — last 30 days of snapshots.
   - `GET http://localhost:8000/history/risk?country=US&days=90` — US only.

---

## Step 2: Global Map (High Severity)

### Goal
- A world map showing high-severity and/or high-risk areas (by country).
- Click country → drill down (existing Drilldown or detail panel).

### Where it fits
- **Backend:** New or extended endpoint that returns map-ready data (country, lat, lon, severity_index, risk_score, event_count).
- **Frontend:** Map tab uses a real map library (e.g. Leaflet, Mapbox, or a globe) and colors/sizes countries (or markers) by severity/risk.

### Tasks

1. **Backend: map endpoint**
   - Add `GET /map?date=YYYY-MM-DD` (or reuse `GET /metrics` with query params).
   - Response: list of `{ country, lat, lon, severity_index, risk_score, event_count }` (one per country; aggregate daily_metrics by country for that date: e.g. max risk_score, max severity_index, sum event_count).
   - Lat/lon: use a static lookup table (country ISO-2 → centroid) if not in DB; or compute from events (e.g. mean lat/lon per country).

2. **Country centroid lookup**
   - Add a small JSON or module: country code → (lat, lon) for map positioning. Many open datasets exist (e.g. natural-earth or a simple CSV).

3. **Frontend: map component**
   - Replace or extend current “Map” tab (country chips) with a real map:
     - Use Leaflet + React-Leaflet, or Mapbox GL, or a 3D globe (e.g. react-globe.gl).
   - Fetch `/map?date=...`; color or size markers/countries by `severity_index` or `risk_score` (e.g. green &lt; 20, yellow &lt; 40, orange &lt; 70, red ≥ 70).
   - On country click: set selected country and switch to Drilldown tab (or open a side panel with that country’s metrics).

4. **Date selector**
   - Allow user to pick date so the map shows that day’s severity/risk.

### Acceptance criteria
- [ ] `GET /map` returns one row per country with at least country, lat, lon, severity_index, risk_score.
- [ ] Frontend map displays countries (or points) colored by severity/risk.
- [ ] Clicking a country opens drill-down (existing Drilldown or equivalent).

### Files to create/modify
- Backend: new route `routes/map.py` or extend `metrics.py`; optional `country_centroids.json` or module.
- Frontend: new Map component (e.g. `MapView.tsx` with Leaflet/Mapbox); update `App.tsx` to use it and pass selected country to Drilldown.

---

## Step 3: Actor Network (Spider Web / Link Connections)

### Goal
- A graph where nodes = countries (or actors) and edges = interactions between them (e.g. event count, conflict ratio).
- “Spider web” style: connections between entities.

### Where it fits
- **Backend:** New table `actors_daily` (date, actor1_country, actor2_country, interaction_count, conflict_ratio, mean_goldstein). New endpoint `GET /actors?country=...&days=30` returning edges (and optionally nodes).
- **Frontend:** New “Network” or “Connections” tab with a graph visualization (D3, vis.js, or React Flow).

### Tasks

1. **Schema: actors_daily**
   - Columns: date, actor1_country, actor2_country, category (optional), interaction_count, conflict_ratio (from quad_class), mean_goldstein.
   - Unique key: (date, actor1_country, actor2_country) or (date, actor1_country, actor2_country, category).
   - Migration + SQLAlchemy model.

2. **Extract actor pairs from events**
   - GDELT has Actor1CountryCode, Actor2CountryCode (or similar). In normalize or a separate step, ensure you have (event_id, date, actor1_country, actor2_country, quad_class, goldstein).
   - If events table doesn’t have actor1/actor2, add them in normalize from GDELT columns (see GDELT 1.0 spec for column indices).

3. **Aggregation**
   - New step: `aggregate_actors_daily.py`. Group by (date, actor1_country, actor2_country): count events, mean(goldstein), conflict_ratio = share of events with quad_class in (3,4). UPSERT into `actors_daily`.
   - Run after normalize (or after daily_metrics aggregation).

4. **API: GET /actors**
   - Query params: country (filter by actor1 or actor2), days (last N days), category (optional).
   - Response: list of edges, e.g. `{ actor1, actor2, interaction_count, conflict_ratio, mean_goldstein }`; optionally list of nodes (unique countries).
   - Format suitable for graph libraries (nodes array, edges array).

5. **Frontend: Network tab**
   - New tab “Network” or “Connections”. Fetch `/actors?days=30`. Render graph: nodes = countries, edges = links, optionally sized by interaction_count and colored by conflict_ratio.
   - Click node: highlight connected edges or filter to that country’s connections.

### Acceptance criteria
- [ ] `actors_daily` populated from events (actor1, actor2 from GDELT).
- [ ] `GET /actors` returns edges (and optionally nodes) for the requested filters.
- [ ] Frontend graph shows country–country links; at least one filter (e.g. country or days) works.

### Files to create/modify
- Backend: model `ActorDaily`; migration; `pipeline/aggregate_actors_daily.py`; normalize (add actor1_country, actor2_country if missing); `routes/actors.py`.
- Frontend: new component `NetworkView.tsx`; add tab and route.

---

## Step 4: AI Search / Chat

### Goal
- User types a natural-language query (e.g. “regime change”, “protests in India”) and gets back relevant events, spikes, and a short summary with evidence links.
- Chat-style UI optional; at minimum: search box + AI-generated answer with links to events/map.

### Where it fits
- **Backend:** Search layer (full-text or semantic) on events; new endpoint `/chat` or `/search` that uses an LLM to interpret the query, runs your existing APIs (events, metrics, spikes) and search, then returns a summary + structured results.
- **Frontend:** Chat panel or “AI Search” box that calls the endpoint and displays the answer and “see these events” / “show on map” links.

### Tasks

1. **Search layer**
   - Option A: Full-text search. Add a searchable text column (e.g. category + country + date as text) or use SQLite FTS / Postgres full-text search on events (and optionally spikes). Endpoint `GET /search?q=...` returning event IDs or event list.
   - Option B: Semantic search. Generate embeddings for event summaries (e.g. category + country + date); store in DB or vector DB; search by embedding similarity. More flexible for “regime change” type queries but requires an embedding model and storage.

2. **AI endpoint**
   - New endpoint: `POST /chat` or `POST /search` with body `{ "query": "regime change" }`.
   - Flow: (1) Send query to LLM with a prompt that asks for structured filters: country (optional), category (optional), date range (optional), keywords. (2) Backend runs: search (if implemented), `GET /events`, `GET /metrics`, `GET /spikes` with those filters. (3) Send results (or top N) back to LLM to summarize in 2–3 sentences and list evidence (event IDs or URLs). (4) Return JSON: `{ "summary": "...", "events": [...], "spikes": [...], "links": [...] }`.
   - Use OpenAI API, Claude API, or a local model (e.g. Ollama); keep API key in env.

3. **Frontend: chat / search UI**
   - New tab or panel “AI Search” or “Chat”. Input box for natural-language query. On submit, call `POST /chat`. Display: summary text + list of events (with links to source URLs) + optional “Show on map” / “Show in Evidence” buttons that filter or navigate to the right view.

4. **Safety and cost**
   - Limit query length and rate-limit `/chat` to avoid abuse and cost. Optional: only allow for authenticated users later.

### Acceptance criteria
- [ ] User can type a query (e.g. “regime change” or “protests India”) and receive a short summary plus relevant events/spikes (or links).
- [ ] At least one search path works (full-text or semantic or “filter by LLM-extracted country/category”).
- [ ] Response includes at least one link to evidence (event source URL or spike detail).

### Files to create/modify
- Backend: `routes/chat.py` or `routes/search.py`; optional `services/search.py` (full-text or embedding); optional `services/llm.py` (call OpenAI/Claude). Env: `OPENAI_API_KEY` or similar.
- Frontend: `ChatView.tsx` or `SearchView.tsx`; add tab.

---

## Step 5: Better Data Science

### Goal
- Longer baselines for stability.
- Simple trends (e.g. “risk rising last 7 days”).
- Percentiles (e.g. severity in top 10% over 180 days).
- Richer signals for the map and brief.

### Where it fits
- Inside existing **aggregate_daily** and **Day 2** pipeline (config + formulas).
- Optional new columns or tables for trends/percentiles.

### Tasks

1. **Longer baselines**
   - In `pipeline_config`: add or use `BASELINE_WINDOW_DAYS_LONG = 56`. In `compute_rolling_and_zscore` and `compute_severity_baseline`, optionally compute a second set of stats with 56-day window (e.g. `z_score_56d`, `z_severity_56d`) for comparison or to use in risk. Document in HOW_DAY2_WORKS.md.

2. **Trend: risk over last 7 days**
   - For each (country, category) and latest date, compute slope or simple “avg risk last 7 days” vs “avg risk previous 7 days”. Add column `risk_trend` (e.g. "up", "down", "stable") or numeric slope. Expose in `GET /metrics` and in brief/map.

3. **Percentile 180d**
   - Implement `percentile_180d` for severity_index: for each (country, category, date), compute percentile of that day’s severity_index within the last 180 days. Store in `daily_metrics.percentile_180d`. Expose in API and optionally in Brief (“worst in 6 months”).

4. **Actor metrics for network**
   - If Step 3 is done: from `actors_daily`, compute “top conflict partners” or a simple centrality (e.g. degree) per country. Expose in `GET /actors` or a small `GET /actors/stats` for use in map tooltips or AI answers.

5. **Geo hotspots (optional)**
   - If you add Phase 3 geo_daily_bins (H3 or grid), you get sub-country severity; map can show both country-level and bin-level hotspots. Document in a separate “Phase 3 geo” doc if you implement it.

### Acceptance criteria
- [ ] At least one of: longer baseline (e.g. 56d), risk_trend, or percentile_180d is implemented and exposed in the API.
- [ ] Brief or map can show the new signal (e.g. “severity in top 10%” or “risk trending up”).

### Files to create/modify
- `pipeline_config.py`; `day2_baselines_risk.py` (rolling window, trend, percentile logic); `docs/HOW_DAY2_WORKS.md`; schemas and routes for new fields.

---

## Summary checklist

Use this to track progress:

- [ ] **Step 1:** Live data API + history (incremental ingest, schedule, optional snapshots).
- [ ] **Step 2:** Global map (backend map endpoint, country centroids, frontend map component).
- [ ] **Step 3:** Actor network (actors_daily, GET /actors, frontend graph).
- [ ] **Step 4:** AI search / chat (search layer, LLM endpoint, chat UI).
- [ ] **Step 5:** Better data science (longer baselines, trends, percentiles).

Do them in this order for the best payoff; Steps 2 and 3 can be swapped if you prefer the spider web before the map.
