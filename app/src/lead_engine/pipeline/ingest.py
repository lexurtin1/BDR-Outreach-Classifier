from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

import psycopg

from ..adapters.registry import get_adapter_cls
from ..utils.hashing import checksum_payload, signal_fingerprint
from ..db import signal_exists
from ..utils.logging import get_logger

logger = get_logger("lead_engine.pipeline.ingest")


def run_ingest(conn) -> Dict[str, Any]:
    """
    Run ingestion for all enabled sources.
    Returns summary with per-source counts and totals.
    """
    run_id = str(uuid4())
    started = datetime.utcnow()
    summary: Dict[str, Any] = {
        "run_id": run_id,
        "started_at": started.isoformat(),
        "sources": {},
        "totals": {"raw_inserted": 0, "raw_skipped": 0, "signals_inserted": 0, "signals_skipped_duplicates": 0},
    }

    with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
        cur.execute("SELECT source_id, name, base_url FROM source_registry WHERE enabled = TRUE;")
        sources = cur.fetchall()

    in_run_fingerprints: set[str] = set()

    for src in sources:
        name = src["name"]
        adapter_cls = get_adapter_cls(name)
        per = {
            "raw_inserted": 0,
            "raw_skipped": 0,
            "signals_inserted": 0,
            "signals_skipped_duplicates": 0,
            "errors": 0,
        }
        if not adapter_cls:
            per["errors"] = 1
            summary["sources"][name] = per
            logger.warning("No adapter registered", extra={"run_id": run_id, "source": name})
            continue
        adapter = adapter_cls(source_id=src["source_id"], base_url=src.get("base_url") or "")
        try:
            raw_payloads = adapter.fetch(run_id=run_id)
            with conn.cursor() as cur:
                for payload in raw_payloads:
                    checksum = checksum_payload(payload)
                    cur.execute(
                        """
                        INSERT INTO raw_events (source_id, payload_json, checksum)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (source_id, checksum) DO NOTHING
                        RETURNING event_id;
                        """,
                        (adapter.source_id, psycopg.types.json.Jsonb(payload), checksum),
                    )
                    inserted = cur.fetchone()
                    if not inserted:
                        per["raw_skipped"] += 1
                        continue
                    per["raw_inserted"] += 1
                    signals = adapter.normalise(payload)
                    for sig in signals:
                        fingerprint = signal_fingerprint(sig | {"source_id": adapter.source_id})
                        if fingerprint in in_run_fingerprints:
                            per["signals_skipped_duplicates"] += 1
                            continue
                        if signal_exists(
                            conn,
                            source_id=adapter.source_id,
                            evidence_url=sig.get("evidence_url"),
                            title=sig.get("title"),
                            signal_time=sig.get("signal_time"),
                            org_name=sig.get("org_name"),
                            signal_type=sig.get("signal_type"),
                        ):
                            per["signals_skipped_duplicates"] += 1
                            continue
                        cur.execute(
                            """
                            INSERT INTO signals
                            (source_id, signal_time, geo, theme_hint, signal_type, value_num, org_name, title, summary, evidence_url)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """,
                            (
                                adapter.source_id,
                                sig.get("signal_time"),
                                sig.get("geo"),
                                sig.get("theme_hint"),
                                sig.get("signal_type"),
                                sig.get("value_num"),
                                sig.get("org_name"),
                                sig.get("title"),
                                sig.get("summary"),
                                sig.get("evidence_url"),
                            ),
                        )
                        per["signals_inserted"] += 1
                        in_run_fingerprints.add(fingerprint)
                conn.commit()
        except Exception as exc:  # noqa: BLE001
            logger.error("Ingest failed for source", extra={"run_id": run_id, "source": name, "error": str(exc)})
            per["errors"] = 1

        summary["sources"][name] = per
        summary["totals"]["raw_inserted"] += per["raw_inserted"]
        summary["totals"]["raw_skipped"] += per["raw_skipped"]
        summary["totals"]["signals_inserted"] += per["signals_inserted"]
        summary["totals"]["signals_skipped_duplicates"] += per["signals_skipped_duplicates"]
        logger.info(
            "Ingest source complete",
            extra={
                "run_id": run_id,
                "source": name,
                "raw_inserted": per["raw_inserted"],
                "raw_skipped": per["raw_skipped"],
                "signals_inserted": per["signals_inserted"],
                "signals_skipped": per["signals_skipped_duplicates"],
            },
        )

    summary["finished_at"] = datetime.utcnow().isoformat()
    return summary
