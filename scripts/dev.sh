#!/usr/bin/env bash
set -euo pipefail

cmd="${1:-}"

case "$cmd" in
  start)
    docker compose up -d --build
    ;;
  stop)
    docker compose down
    ;;
  reset-db)
    docker compose exec postgres psql -U lead_engine -d lead_engine -c "TRUNCATE signals RESTART IDENTITY CASCADE; TRUNCATE raw_events RESTART IDENTITY CASCADE;"
    ;;
  run-ingest)
    curl -s -X POST http://localhost:8000/run/ingest | jq .
    ;;
  show-counts)
    docker compose exec postgres psql -U lead_engine -d lead_engine -c "SELECT count(*) AS raw_events FROM raw_events; SELECT count(*) AS signals FROM signals; SELECT source_id, count(*) FROM signals GROUP BY 1 ORDER BY 1;"
    ;;
  *)
    echo "Usage: $0 {start|stop|reset-db|run-ingest|show-counts}"
    exit 1
    ;;
esac
