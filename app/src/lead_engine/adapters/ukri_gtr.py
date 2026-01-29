from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Sequence

from .base import BaseAdapter, SignalDict
from .http import HttpClient
from ..utils.logging import get_logger


DEFAULT_KEYWORDS = [
    "infrastructure",
    "cyber",
    "defence",
    "aerospace",
    "renewable",
    "manufacturing",
    "public sector",
    "health",
]


class UKRIGtrAdapter(BaseAdapter):
    """Adapter for UKRI Gateway to Research API."""

    def __init__(self, source_id: int, base_url: str, logger: logging.Logger | None = None):
        super().__init__(source_id, base_url, "ukri_gtr", logger)
        self.client = HttpClient(base_url)

    def fetch(self, run_id: str, keywords: Sequence[str] = DEFAULT_KEYWORDS, page_size: int = 10) -> Sequence[Dict[str, Any]]:
        raw_records: List[Dict[str, Any]] = []
        for kw in keywords:
            params = {"searchTerm": kw, "page": 1, "pageSize": page_size}
            try:
                data = self.client.get_json("/gtr/api/projects", params=params)
                projects = data.get("projects") or data.get("project") or []
                # GtR sometimes nests under "project"
                if isinstance(projects, dict) and "project" in projects:
                    projects = projects.get("project", [])
                if isinstance(projects, list):
                    for proj in projects:
                        proj["_search_keyword"] = kw
                        raw_records.append(proj)
            except Exception as exc:  # noqa: BLE001
                self.log(logging.WARNING, "fetch failed", run_id=run_id, keyword=kw, error=str(exc))
                continue
        self.log(logging.INFO, "fetched records", run_id=run_id, count=len(raw_records))
        return raw_records

    def normalise(self, raw: Dict[str, Any]) -> List[SignalDict]:
        signals: List[SignalDict] = []
        title = raw.get("title") or raw.get("projectTitle") or "UKRI Project"
        abstract = raw.get("abstractText") or raw.get("techAbstract") or raw.get("laySummary") or ""
        summary = (abstract[:397] + "...") if len(abstract) > 400 else abstract
        org = None
        # Common shapes: organisation, leadResearchOrganisation -> organisationName
        if isinstance(raw.get("leadResearchOrganisation"), dict):
            org = raw["leadResearchOrganisation"].get("name") or raw["leadResearchOrganisation"].get("organisationName")
        if not org:
            org = raw.get("organisationName")
        evidence_url = None
        if raw.get("id"):
            evidence_url = f"{self.base_url}/gtr/api/projects/{raw['id']}"
        start_date = raw.get("start") or raw.get("startDate")
        last_updated = raw.get("lastUpdated")
        signal_time = self._choose_date(start_date, last_updated)
        value_num = self._extract_value(raw)
        signals.append(
            SignalDict(
                source_id=self.source_id,
                signal_time=signal_time,
                geo="UK",
                theme_hint=None,
                signal_type="grant",
                value_num=value_num,
                org_name=org,
                title=title,
                summary=summary,
                evidence_url=evidence_url,
            )
        )
        return signals

    @staticmethod
    def _choose_date(start: Any, updated: Any) -> str | None:
        for cand in (start, updated):
            if isinstance(cand, str) and len(cand) >= 4:
                try:
                    return datetime.fromisoformat(cand).isoformat()
                except Exception:
                    continue
        return None

    @staticmethod
    def _extract_value(raw: Dict[str, Any]) -> float | None:
        amount_fields = ["awardPounds", "fund", "amount", "projectCost"]
        for field in amount_fields:
            val = raw.get(field)
            try:
                return float(val) if val is not None else None
            except (TypeError, ValueError):
                continue
        return None
