import logging
from typing import Any, Dict, Optional


def get_logger(name: str = "lead_engine") -> logging.Logger:
    """Get a configured logger; basicConfig is set in main entrypoints."""
    return logging.getLogger(name)


def log_struct(
    logger: logging.Logger,
    level: int,
    message: str,
    *,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Structured log helper to attach contextual fields."""
    logger.log(level, message, extra=extra or {})
