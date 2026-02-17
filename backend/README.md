# Backend – Global Events Risk Intelligence Dashboard

FastAPI app: GDELT ingestion, normalization, daily aggregation, risk/spike detection, REST API.

## Setup

From **repo root** (so `backend.app` resolves):

```bash
pip install -r backend/requirements.txt
```

Optional: copy `.env` to root with any overrides (e.g. database path).

## Run API

From repo root:

```bash
uvicorn backend.app.main:app --reload
```

API: http://localhost:8000 — Swagger: http://localhost:8000/docs

## Pipelines

From repo root:

- Day 1 (ingest + normalize + aggregate):  
  `python -m backend.app.pipeline.run_day1 --days 14`
- Day 2 (baselines + risk + spikes):  
  `python -m backend.app.pipeline.run_day2`

## Tests

From repo root:

```bash
python -m pytest backend/tests/ -v
```
