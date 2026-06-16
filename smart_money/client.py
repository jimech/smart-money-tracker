"""A polite, compliant HTTP client for SEC EDGAR.

Every request to the SEC must (1) identify you with a real User-Agent and
(2) stay under 10 requests/second. This module guarantees both so the rest of
the codebase can't forget. It also retries transient failures (HTTP 429 and
5xx) with exponential backoff.

Smoke test:  python -m smart_money.client
"""
from __future__ import annotations

import time

import requests

from . import config


class EdgarClient:
    """One entry point for every SEC request."""

    def __init__(
        self,
        max_requests_per_sec: int = config.MAX_REQUESTS_PER_SEC,
        max_retries: int = 4,
    ) -> None:
        self._min_interval = 1.0 / max_requests_per_sec
        self._max_retries = max_retries
        self._last_request = 0.0
        self._session = requests.Session()
        self._session.headers.update(config.headers())

    def get(self, url: str, **kwargs) -> requests.Response:
        """GET a URL with rate limiting, SEC headers, and retry-on-transient-error."""
        timeout = kwargs.pop("timeout", 30)
        last_error: Exception | None = None

        for attempt in range(self._max_retries + 1):
            self._throttle()
            try:
                response = self._session.get(url, timeout=timeout, **kwargs)
            except requests.RequestException as exc:
                last_error = exc                        # network hiccup -> retry
            else:
                if response.status_code < 400:
                    return response
                if response.status_code == 429 or response.status_code >= 500:
                    last_error = requests.HTTPError(     # rate-limited / server error -> retry
                        f"HTTP {response.status_code} for {url}", response=response
                    )
                else:
                    response.raise_for_status()         # 403/404/... -> fail fast

            if attempt < self._max_retries:
                self._backoff(attempt)

        raise RuntimeError(
            f"EDGAR request failed after {self._max_retries + 1} attempts: {url}"
        ) from last_error

    def get_json(self, url: str, **kwargs):
        """GET a URL and return the parsed JSON body."""
        return self.get(url, **kwargs).json()

    def _throttle(self) -> None:
        """Sleep just long enough to stay under the rate limit."""
        elapsed = time.monotonic() - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()

    def _backoff(self, attempt: int) -> None:
        """Wait before a retry: 1s, 2s, 4s, 8s..."""
        time.sleep(2 ** attempt)


default_client = EdgarClient()


def get(url: str, **kwargs) -> requests.Response:
    return default_client.get(url, **kwargs)


def get_json(url: str, **kwargs):
    return default_client.get_json(url, **kwargs)


if __name__ == "__main__":
    if not config.user_agent_is_configured():
        raise SystemExit(
            'Set SEC_USER_AGENT first:\n'
            '  export SEC_USER_AGENT="Your Name your-email@gmail.com"'
        )
    data = get_json(config.COMPANY_TICKERS_URL)
    print(f"OK - fetched {len(data):,} companies from EDGAR.")
    example = next(iter(data.values()))
    print(f"Example: {example['ticker']} -> CIK {example['cik_str']} ({example['title']})")