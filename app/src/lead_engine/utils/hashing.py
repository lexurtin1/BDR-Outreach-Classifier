import hashlib
import json
from typing import Any, Dict


def stable_json_dumps(payload: Any) -> str:
    """Return deterministic JSON string for hashing and storage."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def checksum_payload(payload: Any) -> str:
    """Compute a stable SHA256 checksum for arbitrary JSON-serialisable payloads."""
    normalized = stable_json_dumps(payload)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def checksum_record(record: Dict[str, Any]) -> str:
    """Alias for clarity when hashing dict-like records."""
    return checksum_payload(record)


def normalize_text(s: str) -> str:
    """Lowercase, strip, and collapse whitespace for stable comparisons."""
    return " ".join(s.strip().lower().split())


def signal_fingerprint(signal: Dict[str, Any]) -> str:
    """
    Compute a deterministic fingerprint for a normalised signal.
    Uses key fields to avoid duplicates across runs without schema changes.
    """
    def safe(val: Any) -> str:
        if val is None:
            return ""
        return normalize_text(str(val))

    parts = [
        str(signal.get("source_id", "")),
        safe(signal.get("evidence_url", "")),
        safe(signal.get("title", "")),
        safe(signal.get("signal_time", "")),
        safe(signal.get("org_name", "")),
        safe(signal.get("signal_type", "")),
    ]
    joined = "|".join(parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
