"""Resolve between tickers and SEC CIK numbers.

EDGAR keys filings by CIK; humans use tickers. This downloads the SEC's
company_tickers.json (at most once a week), caches it locally, and builds
fast in-memory lookups in both directions.

Smoke test:  python -m smart_money.resolver
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import client, config

CACHE_PATH: Path = config.DATA_DIR / "company_tickers.json"
CACHE_MAX_AGE_SECONDS: int = 7 * 24 * 60 * 60  # one week


class TickerResolver:
    """Bidirectional ticker <-> CIK lookup, backed by a weekly disk cache."""

    def __init__(
        self,
        cache_path: Path = CACHE_PATH,
        max_age: int = CACHE_MAX_AGE_SECONDS,
    ) -> None:
        self._cache_path = cache_path
        self._max_age = max_age
        self._ticker_to_cik: dict[str, int] = {}
        self._cik_to_ticker: dict[int, str] = {}
        self._titles: dict[int, str] = {}
        self._load()

    def cik_for(self, ticker: str) -> int:
        """'AAPL' -> 320193. Raises KeyError if unknown."""
        try:
            return self._ticker_to_cik[ticker.upper()]
        except KeyError:
            raise KeyError(f"Unknown ticker: {ticker!r}") from None

    def cik10_for(self, ticker: str) -> str:
        """'AAPL' -> '0000320193' (the form EDGAR's submissions API wants)."""
        return config.cik10(self.cik_for(ticker))

    def ticker_for(self, cik: int | str) -> str:
        """320193 -> 'AAPL'. Raises KeyError if unknown."""
        try:
            return self._cik_to_ticker[int(cik)]
        except KeyError:
            raise KeyError(f"Unknown CIK: {cik!r}") from None

    def title_for(self, ticker: str) -> str:
        return self._titles[self.cik_for(ticker)]

    def __len__(self) -> int:
        return len(self._ticker_to_cik)

    def _load(self) -> None:
        data = self._read_cache() or self._download_and_cache()
        for row in data.values():
            ticker = str(row["ticker"]).upper()
            cik = int(row["cik_str"])
            self._ticker_to_cik[ticker] = cik
            # Note: a few CIKs have multiple tickers (e.g. GOOG/GOOGL); last wins.
            self._cik_to_ticker[cik] = ticker
            self._titles[cik] = row["title"]

    def _read_cache(self) -> dict | None:
        if not self._cache_path.exists():
            return None
        if time.time() - self._cache_path.stat().st_mtime > self._max_age:
            return None  # stale
        try:
            return json.loads(self._cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _download_and_cache(self) -> dict:
        data = client.get_json(config.COMPANY_TICKERS_URL)
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(json.dumps(data))
        return data


_default: TickerResolver | None = None


def get_resolver() -> TickerResolver:
    global _default
    if _default is None:
        _default = TickerResolver()
    return _default


def cik_for(ticker: str) -> int:
    return get_resolver().cik_for(ticker)


def ticker_for(cik: int | str) -> str:
    return get_resolver().ticker_for(cik)


if __name__ == "__main__":
    if not config.user_agent_is_configured():
        raise SystemExit("Set SEC_USER_AGENT first (see README).")
    r = TickerResolver()
    print(f"Loaded {len(r):,} ticker -> CIK mappings.")
    for t in ("AAPL", "MSFT", "NVDA"):
        print(f"  {t:6} -> CIK {r.cik_for(t):>10}  ({r.title_for(t)})")
    print(f"Reverse: CIK 320193 -> {r.ticker_for(320193)}")