from __future__ import annotations

from typing import Dict, Any

from ..db import get_connection
from ..pipeline.ingest import run_ingest


def run_all_adapters() -> Dict[str, Any]:
    """Legacy debug runner wrapping the ingest pipeline."""
    with get_connection() as conn:
        return run_ingest(conn)


if __name__ == "__main__":
    print(run_all_adapters())
