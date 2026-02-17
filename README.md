# Global Events Risk Intelligence Dashboard

OSINT dashboard: GDELT event data → normalized schema → daily metrics → API + React dashboard (map, movers, drilldown, brief, evidence).

## Structure

- **backend/** – Python 3.11+, FastAPI, SQLAlchemy, SQLite. API, pipeline (ingest, normalize, aggregate, risk/spikes). Tests and deps live here.
- **frontend/** – React, TypeScript, Parcel, Tailwind. Map, event feed, movers table, country drilldown, brief, evidence panel.
- **docs/** – Design, schema, taxonomy, roadmaps (local only; not pushed).

## Run locally

**Backend**

```bash
# From repo root
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r backend/requirements.txt
python -m backend.app.pipeline.run_day1 --days 14   # optional: load data
python -m backend.app.pipeline.run_day2             # optional: baselines + spikes
uvicorn backend.app.main:app --reload
```

API: http://localhost:8000 — Docs: http://localhost:8000/docs

**Frontend**

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env   # set API_URL=http://localhost:8000, optional MAPBOX_TOKEN
npm run dev
```

App: http://localhost:1234 (Parcel default). It uses `API_URL` from `.env` to talk to the API.

## Tests

From repo root:

```bash
python -m pytest backend/tests/ -v
```
