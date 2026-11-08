"""EVREN istemcisi: bağlantı kurulamadıysa (DNS kopması) kısa aralarla yeniden dener; zaman aşımında yeniden denemez.
#666'dan beri sohbet akışlı (stream); sahte HTTP katmanı httpx.MockTransport."""
import httpx
import pytest

from app.services import evren_client
from app.services.evren_client import EvrenClient, EvrenError

SSE = b'data: {"choices": [{"index": 0, "delta": {"content": "tamam"}, "finish_reason": "stop"}]}\n\ndata: [DONE]\n\n'


def test_connect_error_retried_timeout_not(client, monkeypatch):
    calls = {"n": 0}

    async def no_sleep(_):
        return None

    def handler(request):
        calls["n"] += 1
        if calls["mode"] == "timeout":
            raise httpx.ReadTimeout("yavaş", request=request)
        if calls["n"] < 3:
            raise httpx.ConnectError("[Errno -5] No address associated with hostname", request=request)
        return httpx.Response(200, content=SSE)

    monkeypatch.setattr(evren_client.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(evren_client.settings, "EVREN_API_KEY", "test")
    c = EvrenClient()
    c.transport = httpx.MockTransport(handler)
    calls["mode"] = "dns"
    res = client.portal.call(c.chat, "m", [{"role": "user", "content": "x"}])
    assert res.content == "tamam" and calls["n"] == 3  # iki kopma + başarılı deneme

    calls.update(n=0, mode="timeout")
    with pytest.raises(EvrenError, match="zaman aşımı"):
        client.portal.call(c.chat, "m", [{"role": "user", "content": "x"}])
    assert calls["n"] == 1  # zaman aşımında istek EVREN'e ulaşmış olabilir: yeniden gönderilmez
