from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Tuple

import psycopg

from ..db import get_connection, signal_exists
from ..utils.hashing import checksum_payload, signal_fingerprint
from ..utils.logging import get_logger
from .contracts_finder import ContractsFinderAdapter
from .ons import ONSDataAdapter
from .ukri_gtr import UKRIGtrAdapter

logger = get_logger("lead_engine.adapters.runner")


ADAPTER_REGISTRY = {
    "contracts_finder": ContractsFinderAdapter,
    "ukri_gtr": UKRIGtrAdapter,
    "ons": ONSDataAdapter,
}


def run_all_adapters() -> Dict[str, Dict[str, int]]:
    """Run all enabled adapters and return a summary."""
    run_id = datetime.utcnow().isoformat()
    summary: Dict[str, Dict[str, int]] = {}
    with get_connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute("SELECT source_id, name, base_url FROM source_registry WHERE enabled = TRUE;")
            sources = cur.fetchall()
        for src in sources:
            name = src["name"]
            adapter_cls = ADAPTER_REGISTRY.get(name)
            if not adapter_cls:
                logger.warning("No adapter registered", extra={"source": name})
                continue
            adapter = adapter_cls(source_id=src["source_id"], base_url=src.get("base_url") or "")
            inserted_raw, inserted_signals, skipped = _process_source(conn, adapter, run_id)
            summary[name] = {
                "raw_events": inserted_raw,
                "signals_inserted": inserted_signals,
                "signals_skipped_duplicates": skipped,
            }
    return summary


def _process_source(conn: psycopg.Connection, adapter, run_id: str) -> Tuple[int, int, int]:
    raw_inserted = 0
    signals_inserted = 0
    signals_skipped = 0
    dedupe_in_run: set[str] = set()
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
                continue  # duplicate raw; skip downstream
            raw_inserted += 1
            signals = adapter.normalise(payload)
            for sig in signals:
                fp = signal_fingerprint(sig | {"source_id": adapter.source_id})
                if fp in dedupe_in_run:
                    signals_skipped += 1
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
                    signals_skipped += 1
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
                signals_inserted += 1
                dedupe_in_run.add(fp)
        conn.commit()
    adapter.log(
        logging.INFO,
        "adapter completed",
        run_id=run_id,
        raw_inserted=raw_inserted,
        signals_inserted=signals_inserted,
        signals_skipped=signals_skipped,
    )
    return raw_inserted, signals_inserted, signals_skipped


if __name__ == "__main__":
    print(run_all_adapters())
