from __future__ import annotations

import abc
import logging
from typing import Any, Dict, List, Optional, Sequence, TypedDict

from ..utils.hashing import checksum_payload
from ..utils.logging import get_logger


class SignalDict(TypedDict, total=False):
    source_id: int
    signal_time: Optional[str]
    geo: str
    theme_hint: Optional[str]
    signal_type: str
    value_num: Optional[float]
    org_name: Optional[str]
    title: str
    summary: Optional[str]
    evidence_url: Optional[str]


class BaseAdapter(abc.ABC):
    """Base class for all adapters."""

    def __init__(self, source_id: int, base_url: str, name: str, logger: Optional[logging.Logger] = None):
        self.source_id = source_id
        self.base_url = base_url.rstrip("/")
        self.name = name
        self.logger = logger or get_logger(f"lead_engine.adapters.{name}")

    @abc.abstractmethod
    def fetch(self, run_id: str) -> Sequence[Dict[str, Any]]:
        """Return iterable of raw payload objects."""

    @abc.abstractmethod
    def normalise(self, raw: Dict[str, Any]) -> List[SignalDict]:
        """Convert raw payload into one or more signals."""

    def checksum(self, payload: Dict[str, Any]) -> str:
        return checksum_payload(payload)

    def log(self, level: int, message: str, **extra: Any) -> None:
        context = {"source": self.name, **extra}
        self.logger.log(level, message, extra=context)
