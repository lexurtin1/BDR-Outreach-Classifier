# UKI Spend & Investment Trends – 5 BDR Insights Engine

Skeleton project for ingesting UK public procurement, research funding, and macroeconomic signals, normalising them into a unified schema, and producing five actionable insights for Business Development Representatives. Built with FastAPI and Postgres, containerised via Docker Compose.

## Quick start
- `docker compose up --build` (after completing subsequent steps)
- API available at `http://localhost:8000`

This repository is intentionally minimal to allow rapid iteration on adapters, pipelines, and insight generation.

## Running locally
- Start services: `docker compose up -d --build`
- Health check: `curl http://localhost:8000/health`
- Trigger ingest: `curl -X POST http://localhost:8000/run/ingest`
- Debug ingest (same pipeline, debug label): `curl -X POST http://localhost:8000/debug/run_adapters`
- Inspect DB counts:
  - `docker compose exec postgres psql -U lead_engine -d lead_engine -c "SELECT count(*) FROM raw_events;" `
  - `docker compose exec postgres psql -U lead_engine -d lead_engine -c "SELECT count(*) FROM signals;" `
