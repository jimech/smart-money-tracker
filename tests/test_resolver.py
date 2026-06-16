import os
import time

import pytest

from smart_money import resolver as resolver_mod
from smart_money.resolver import TickerResolver

FAKE = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
}


@pytest.fixture
def patched_download(monkeypatch):
    calls = {"n": 0}

    def fake_get_json(url, **kw):
        calls["n"] += 1
        return FAKE

    monkeypatch.setattr(resolver_mod.client, "get_json", fake_get_json)
    return calls


def test_resolves_ticker_to_cik(tmp_path, patched_download):
    r = TickerResolver(cache_path=tmp_path / "ct.json")
    assert r.cik_for("AAPL") == 320193
    assert r.cik10_for("AAPL") == "0000320193"


def test_is_case_insensitive(tmp_path, patched_download):
    r = TickerResolver(cache_path=tmp_path / "ct.json")
    assert r.cik_for("aapl") == 320193


def test_reverse_lookup(tmp_path, patched_download):
    r = TickerResolver(cache_path=tmp_path / "ct.json")
    assert r.ticker_for(789019) == "MSFT"


def test_unknown_ticker_raises(tmp_path, patched_download):
    r = TickerResolver(cache_path=tmp_path / "ct.json")
    with pytest.raises(KeyError):
        r.cik_for("NOPE")


def test_cache_avoids_second_download(tmp_path, patched_download):
    cache = tmp_path / "ct.json"
    TickerResolver(cache_path=cache)   # downloads once
    TickerResolver(cache_path=cache)   # should read cache
    assert patched_download["n"] == 1


def test_stale_cache_redownloads(tmp_path, patched_download):
    cache = tmp_path / "ct.json"
    TickerResolver(cache_path=cache)
    old = time.time() - (8 * 24 * 60 * 60)   # backdate cache by 8 days
    os.utime(cache, (old, old))
    TickerResolver(cache_path=cache)
    assert patched_download["n"] == 2