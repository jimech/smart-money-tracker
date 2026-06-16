import time

import pytest
import requests

from smart_money.client import EdgarClient


class FakeResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.headers = {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


def test_session_sends_user_agent():
    c = EdgarClient()
    assert c._session.headers.get("User-Agent")


def test_throttle_spaces_out_requests(monkeypatch):
    c = EdgarClient(max_requests_per_sec=10)            # 0.1s minimum spacing
    monkeypatch.setattr(c._session, "get", lambda url, **kw: FakeResponse(200))
    start = time.monotonic()
    for _ in range(5):
        c.get("https://data.sec.gov/test")
    elapsed = time.monotonic() - start
    assert elapsed >= 0.35                              # 5 calls -> at least 4 gaps of 0.1s


def test_retries_5xx_then_succeeds(monkeypatch):
    c = EdgarClient(max_retries=3)
    calls = {"n": 0}

    def flaky(url, **kw):
        calls["n"] += 1
        return FakeResponse(503) if calls["n"] < 3 else FakeResponse(200, {"ok": True})

    monkeypatch.setattr(c._session, "get", flaky)
    monkeypatch.setattr(time, "sleep", lambda s: None)  # skip real backoff waits
    resp = c.get("https://data.sec.gov/test")
    assert resp.status_code == 200
    assert calls["n"] == 3


def test_gives_up_after_max_retries(monkeypatch):
    c = EdgarClient(max_retries=2)
    monkeypatch.setattr(c._session, "get", lambda url, **kw: FakeResponse(503))
    monkeypatch.setattr(time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError):
        c.get("https://data.sec.gov/test")