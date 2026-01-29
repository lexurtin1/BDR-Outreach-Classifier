import time
from typing import Any, Dict, Optional

import requests

DEFAULT_TIMEOUT = 10
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
USER_AGENT = "BDR-Outreach-Classifier/0.1 (+github)"


class HttpClient:
    """Lightweight HTTP helper with retry/backoff."""

    def __init__(self, base_url: str, timeout: int = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = timeout
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})

    def _request(self, method: str, path: str, *, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = self.session.request(method, url, params=params, timeout=self.timeout)
                if resp.status_code in (429, 500, 502, 503, 504):
                    raise TransientHttpError(f"Transient status {resp.status_code}")
                resp.raise_for_status()
                return resp
            except (requests.RequestException, TransientHttpError):
                if attempt >= MAX_RETRIES:
                    raise
                sleep_for = BACKOFF_FACTOR ** attempt
                time.sleep(sleep_for)
        # should not reach
        raise RuntimeError("Unhandled request retry logic")

    def get_json(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
        resp = self._request("GET", path, params=params)
        return resp.json()


class TransientHttpError(Exception):
    """Errors considered retryable."""

    pass
