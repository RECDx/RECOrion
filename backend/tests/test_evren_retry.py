"""EVREN istemcisi: bağlantı kurulamadıysa (DNS kopması) kısa aralarla yeniden dener; zaman aşımında yeniden denemez."""
import httpx
import pytest

from app.services import evren_client
from app.services.evren_client import EvrenClient, EvrenError


def test_connect_error_retried_timeout_not(client, monkeypatch):
    calls = {"n": 0}

    async def no_sleep(_):
        return None

    class Flaky:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **k):
            calls["n"] += 1
            if calls["mode"] == "timeout":
                raise httpx.ReadTimeout("yavaş")
            if calls["n"] < 3:
                raise httpx.ConnectError("[Errno -5] No address associated with hostname")
            return httpx.Response(200, json={"choices": [{"message": {"content": "tamam"}}], "usage": {}})

    monkeypatch.setattr(evren_client.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(evren_client.httpx, "AsyncClient", Flaky)
    monkeypatch.setattr(evren_client.settings, "EVREN_API_KEY", "test")
    calls["mode"] = "dns"
    res = client.portal.call(EvrenClient().chat, "m", [{"role": "user", "content": "x"}])
    assert res.content == "tamam" and calls["n"] == 3  # iki kopma + başarılı deneme

    calls.update(n=0, mode="timeout")
    with pytest.raises(EvrenError, match="zaman aşımı"):
        client.portal.call(EvrenClient().chat, "m", [{"role": "user", "content": "x"}])
    assert calls["n"] == 1  # zaman aşımında istek EVREN'e ulaşmış olabilir: yeniden gönderilmez
