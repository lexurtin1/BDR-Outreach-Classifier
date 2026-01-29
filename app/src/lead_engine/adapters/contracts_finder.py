from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Sequence

from .base import BaseAdapter, SignalDict
from .http import HttpClient


class ContractsFinderAdapter(BaseAdapter):
    """Adapter for UK Contracts Finder / Open Contracting feed with fixture fallback."""

    FIXTURE_PATH = Path(__file__).parent / "fixtures" / "contracts_finder_sample.json"

    def __init__(self, source_id: int, base_url: str, logger: logging.Logger | None = None):
        super().__init__(source_id, base_url, "contracts_finder", logger)
        self.client = HttpClient(base_url)

    def fetch(self, run_id: str, days: int = 7) -> Sequence[Dict[str, Any]]:
        """Fetch recent notices; fallback to fixture if live call fails."""
        since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        params = {"publishedFrom": since, "page": 1}
        try:
            # NOTE: Endpoint best-effort; TODO replace with documented OCDS endpoint if available.
            data = self.client.get_json("/Published/Notices/OCDS/Notices.json", params=params)
            records = data.get("records") or data.get("results") or data.get("releases") or []
            if isinstance(records, list) and records:
                self.log(logging.INFO, "fetched live contracts", run_id=run_id, count=len(records))
                return records
        except Exception as exc:  # noqa: BLE001
            self.log(logging.WARNING, "live fetch failed; using fixture", run_id=run_id, error=str(exc))
        # fixture fallback
        with self.FIXTURE_PATH.open("r", encoding="utf-8") as f:
            records = json.load(f)
        self.log(logging.INFO, "loaded fixture contracts", run_id=run_id, count=len(records))
        return records

    def normalise(self, raw: Dict[str, Any]) -> List[SignalDict]:
        signals: List[SignalDict] = []
        release = raw.get("compiledRelease") or raw
        title = release.get("title") or release.get("tender", {}).get("title") or "Contract notice"
        description = release.get("description") or release.get("tender", {}).get("description") or ""
        summary = (description[:397] + "...") if len(description) > 400 else description
        supplier = None
        if release.get("awards"):
            awards = release["awards"]
            if isinstance(awards, list) and awards:
                parties = awards[0].get("suppliers")
                if parties and isinstance(parties, list):
                    supplier = parties[0].get("name")
        buyer = None
        if release.get("buyer"):
            buyer = release["buyer"].get("name")
        org = supplier or buyer
        evidence_url = release.get("uri") or release.get("notice_url") or release.get("id")
        if evidence_url and not evidence_url.startswith("http"):
            evidence_url = f"{self.base_url}/{evidence_url.lstrip('/')}"
        signal_time = (
            release.get("date") or release.get("published_date") or release.get("awards", [{}])[0].get("date")
        )
        value_num = None
        if release.get("value"):
            try:
                value_num = float(release["value"].get("amount"))
            except Exception:
                value_num = None
        if not value_num and release.get("contracts"):
            try:
                value_num = float(release["contracts"][0].get("value", 0))
            except Exception:
                value_num = None
        signals.append(
            SignalDict(
                source_id=self.source_id,
                signal_time=signal_time,
                geo="UK",
                theme_hint=None,
                signal_type="contract",
                value_num=value_num,
                org_name=org,
                title=title,
                summary=summary,
                evidence_url=evidence_url,
            )
        )
        return signals
