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
