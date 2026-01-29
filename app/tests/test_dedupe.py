import psycopg

from lead_engine.utils.hashing import signal_fingerprint
from lead_engine.db import signal_exists, init_pool, close_pool, get_connection


def test_signal_dedupe_insertion():
    init_pool()
    sig = {
        "source_id": 999,
        "signal_time": "2026-01-01T00:00:00Z",
        "geo": "UK",
        "theme_hint": None,
        "signal_type": "test",
        "value_num": 123.0,
        "org_name": "Acme",
        "title": "Test Signal",
        "summary": "test",
        "evidence_url": "http://example.com/test",
    }
    fp = signal_fingerprint(sig)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signals
                (source_id, signal_time, geo, theme_hint, signal_type, value_num, org_name, title, summary, evidence_url)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING;
                """,
                (
                    sig["source_id"],
                    sig["signal_time"],
                    sig["geo"],
                    sig["theme_hint"],
                    sig["signal_type"],
                    sig["value_num"],
                    sig["org_name"],
                    sig["title"],
                    sig["summary"],
                    sig["evidence_url"],
                ),
            )
            conn.commit()
        # Second insert should be skipped by existence check
        assert signal_exists(
            conn,
            source_id=sig["source_id"],
            evidence_url=sig["evidence_url"],
            title=sig["title"],
            signal_time=sig["signal_time"],
            org_name=sig["org_name"],
            signal_type=sig["signal_type"],
        )
    close_pool()
