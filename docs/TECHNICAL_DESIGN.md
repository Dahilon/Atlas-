# Technical Design (Outline)

This document will capture the end-to-end architecture of the Global Events Risk Intelligence Dashboard.

For Day 1, the focus is on:

- Ingestion of GDELT daily events exports
- Normalization into the `events` table
- Aggregation into the `daily_metrics` table
- FastAPI endpoints exposing this data

Further sections will be filled in as we implement spike detection, risk scoring, and the dashboard UI.

