from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .base import BaseAdapter, SignalDict
from .http import HttpClient


class ONSDataAdapter(BaseAdapter):
    """ONS adapter with live attempt and fixture fallback."""

    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ons_sample.json"

    def __init__(self, source_id: int, base_url: str, logger: logging.Logger | None = None):
        super().__init__(source_id, base_url, "ons", logger)
        self.client = HttpClient(base_url)

    def fetch(self, run_id: str, series_code: str = "ABJR") -> Sequence[Dict[str, Any]]:
        """
        Attempt to fetch a known business investment series; fallback to fixture on any failure.
        API ref: https://api.ons.gov.uk/timeseries/{series}/dataset.
        """
        try:
            data = self.client.get_json(f"/timeseries/{series_code}/dataset")
            observations = data.get("observations") or []
            records = [{"series": data.get("description") or data.get("title") or series_code, "dataset_url": data.get("uri"), "observations": observations}]
            self.log(logging.INFO, "fetched live ons series", run_id=run_id, count=len(records))
            return records
        except Exception as exc:  # noqa: BLE001
            self.log(logging.WARNING, "ons live fetch failed; using fixture", run_id=run_id, error=str(exc))
        with self.FIXTURE_PATH.open("r", encoding="utf-8") as f:
            records = json.load(f)
        self.log(logging.INFO, "loaded fixture ons", run_id=run_id, count=len(records))
        return records

    def normalise(self, raw: Dict[str, Any]) -> List[SignalDict]:
        signals: List[SignalDict] = []
        series_name = raw.get("series", "ONS macro series")
        dataset_url = raw.get("dataset_url")
        observations = raw.get("observations") or []
        for obs in observations:
            date_str = obs.get("date")
            value = obs.get("value")
            signal_time = date_str
            try:
                # attempt to normalise formats like 2025-Q3 to ISO using placeholder day
                if isinstance(date_str, str) and "Q" in date_str:
                    year, quarter = date_str.split("-Q")
                    month = 3 * (int(quarter) - 1) + 1
                    signal_time = datetime(int(year), month, 1).isoformat()
            except Exception:
                pass
            summary = f"{series_name} observation at {date_str}"
            signals.append(
                SignalDict(
                    source_id=self.source_id,
                    signal_time=signal_time,
                    geo="UK",
                    theme_hint=None,
                    signal_type="macro",
                    value_num=float(value) if value is not None else None,
                    org_name=None,
                    title=series_name,
                    summary=summary,
                    evidence_url=dataset_url,
                )
            )
        return signals
