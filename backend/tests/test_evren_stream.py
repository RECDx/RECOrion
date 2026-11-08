"""#666 (EVREN yanıtı 08.11.2026): akışlı sohbet, ilk token süresi, 429 Retry-After, düşünme kapatma.
EVREN'e gidilmez: httpx.MockTransport ile sahte akış."""
import asyncio
import json

import httpx
import pytest

from app.config import settings
from app.services.evren_client import EvrenClient, EvrenError


def _sse(*chunks, keepalive=0):
    lines = [": keep-alive\n\n"] * keepalive
    lines += [f"data: {json.dumps(c)}\n\n" for c in chunks]
    lines.append("data: [DONE]\n\n")
    return "".join(lines).encode()


def _delta(**d):
    return {"id": "c1", "model": "m", "choices": [{"index": 0, "delta": d, "finish_reason": None}]}


def _finish(reason="stop"):
    return {"id": "c1", "choices": [{"index": 0, "delta": {}, "finish_reason": reason}]}


USAGE = {"id": "c1", "choices": [], "usage": {"prompt_tokens": 11, "completion_tokens": 7, "evren": {"cost": 1}}}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "EVREN_API_KEY", "test-key")
    monkeypatch.setattr(settings, "EVREN_NO_THINKING_MODELS", "qwen3.8-flash-next")
    monkeypatch.setattr(settings, "LLM_THINKING_MIN_TOKENS", 4096)
    monkeypatch.setattr(settings, "EVREN_RETRY_AFTER_MAX_SECONDS", 60)
    c = EvrenClient()
    c.sent = []

    def use(handler):
        def wrapped(request):
            c.sent.append(json.loads(request.content or b"{}"))
            return handler(request)
        c.transport = httpx.MockTransport(wrapped)
    c.use = use
    return c


def _run(coro):
    return asyncio.run(coro)


def test_stream_collects_answer_reasoning_usage_and_ignores_keepalive(client):
    body = _sse(_delta(role="assistant"), _delta(reasoning="Düşünü"), _delta(reasoning="yorum."),
                _delta(content="Merha"), _delta(content="ba"), _finish("length"), USAGE, keepalive=3)
    client.use(lambda r: httpx.Response(200, content=body))
    res = _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "selam"}], max_tokens=200))
    assert res.content == "Merhaba" and res.thought == "Düşünüyorum."
    assert (res.tokens_in, res.tokens_out) == (11, 7) and res.raw["usage"]["evren"] == {"cost": 1}
    assert res.raw["choices"][0]["finish_reason"] == "length"  # agent_work devam kararını buna bakar
    sent = client.sent[0]
    assert sent["stream"] is True and sent["stream_options"] == {"include_usage": True}
    assert sent["max_tokens"] == 4096  # düşünen model: bütçe en az 4096
    assert "chat_template_kwargs" not in sent


def test_thinking_disabled_for_listed_model_and_budget_kept(client):
    client.use(lambda r: httpx.Response(200, content=_sse(_delta(content="{\"ok\": true}"), _finish())))
    res = _run(client.chat("qwen3.8-flash-next", [{"role": "user", "content": "json"}], max_tokens=300))
    assert res.content == '{"ok": true}'
    assert client.sent[0]["chat_template_kwargs"] == {"enable_thinking": False} and client.sent[0]["max_tokens"] == 300


def test_thinking_kept_for_agent_work_purpose(client, monkeypatch):
    """F85: düşünmesi kapalı model AI personelin iş adımında (AGENT_CHAT) düşünerek çalışır; diğer amaçlarda kapalı."""
    monkeypatch.setattr(settings, "EVREN_THINKING_PURPOSES", "AGENT_CHAT")
    client.use(lambda r: httpx.Response(200, content=_sse(_delta(content="kod"), _finish())))
    _run(client.chat("qwen3.8-flash-next", [{"role": "user", "content": "x"}], max_tokens=4000, purpose="AGENT_CHAT"))
    _run(client.chat("qwen3.8-flash-next", [{"role": "user", "content": "x"}], max_tokens=4000, purpose="BRAIN"))
    work, brain = client.sent
    assert "chat_template_kwargs" not in work and work["max_tokens"] == 4096
    assert brain["chat_template_kwargs"] == {"enable_thinking": False} and brain["max_tokens"] == 4000


def test_repetition_penalty_only_for_agent_work(client, monkeypatch):
    """F85: iş adımlarında (AGENT_CHAT) tekrar cezası gönderilir, düşünme kapalı kalır; diğer amaçlarda gönderilmez."""
    monkeypatch.setattr(settings, "EVREN_THINKING_PURPOSES", "")
    monkeypatch.setattr(settings, "EVREN_REPETITION_PENALTY", 1.05)
    monkeypatch.setattr(settings, "EVREN_REPETITION_PURPOSES", "AGENT_CHAT")
    client.use(lambda r: httpx.Response(200, content=_sse(_delta(content="kod"), _finish())))
    _run(client.chat("qwen3.8-flash-next", [{"role": "user", "content": "x"}], max_tokens=4000, purpose="AGENT_CHAT"))
    _run(client.chat("qwen3.8-flash-next", [{"role": "user", "content": "x"}], max_tokens=4000, purpose="BRAIN"))
    work, brain = client.sent
    assert work["repetition_penalty"] == 1.05 and work["chat_template_kwargs"] == {"enable_thinking": False}
    assert "repetition_penalty" not in brain


def test_reasoning_never_becomes_answer(client):
    """F60: bütçe düşünmede biterse düşünme metni yanıt sayılmaz (gateway boş yanıtı yedek modele devreder)."""
    client.use(lambda r: httpx.Response(200, content=_sse(_delta(reasoning="Let me think..."), _finish("length"))))
    res = _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "plan"}]))
    assert res.content == "" and res.thought == "Let me think..."


def test_first_token_timeout_cuts_busy_model(client):
    async def slow():
        for _ in range(20):  # kuyrukta bekleyen model: yalnız keep-alive
            yield b": keep-alive\n\n"
            await asyncio.sleep(0.1)
        yield _sse(_delta(content="geç"))

    client.use(lambda r: httpx.Response(200, content=slow()))
    with pytest.raises(EvrenError) as e:
        _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}], timeout=30, first_token_timeout=0.5))
    assert "yanıt vermeye başlamadı" in str(e.value)


def test_slow_generation_after_first_token_is_not_cut(client):
    async def gen():
        yield _sse(_delta(reasoning="a"))[:-len(b"data: [DONE]\n\n")]
        for _ in range(4):
            await asyncio.sleep(0.2)
            yield f"data: {json.dumps(_delta(content='x'))}\n\n".encode()
        yield b"data: [DONE]\n\n"

    client.use(lambda r: httpx.Response(200, content=gen()))
    res = _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}], timeout=30, first_token_timeout=0.3))
    assert res.content == "xxxx"


def test_429_retry_after_waits_and_retries_once(client):
    calls = {"n": 0}

    def handler(r):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, content=b"too many")
        return httpx.Response(200, content=_sse(_delta(content="tamam"), _finish()))

    client.use(handler)
    assert _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}])).content == "tamam"
    assert calls["n"] == 2


def test_429_with_long_retry_after_fails_fast(client):
    client.use(lambda r: httpx.Response(429, headers={"Retry-After": "900"}, content=b"too many"))
    with pytest.raises(EvrenError) as e:
        _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}]))
    assert e.value.status_code == 429 and len(client.sent) == 1


def test_429_on_embedding_post_is_retried(client):
    calls = {"n": 0}

    def handler(r):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}], "usage": {"prompt_tokens": 3}})

    client.use(handler)
    assert _run(client.embed("metin", "qwen3-embedding-8b")).vector == [0.1, 0.2] and calls["n"] == 2


def test_streamed_tool_calls_are_merged(client):
    body = _sse(
        _delta(tool_calls=[{"index": 0, "id": "call_1", "type": "function", "function": {"name": "odoo_search", "arguments": ""}}]),
        _delta(tool_calls=[{"index": 0, "function": {"arguments": "{\"model\": "}}]),
        _delta(tool_calls=[{"index": 0, "function": {"arguments": "\"res.partner\"}"}}]),
        _finish("tool_calls"))
    client.use(lambda r: httpx.Response(200, content=body))
    res = _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}], tools=[{"type": "function", "function": {"name": "odoo_search"}}]))
    assert res.tool_calls == [{"id": "call_1", "type": "function", "function": {"name": "odoo_search", "arguments": "{\"model\": \"res.partner\"}"}}]
    assert client.sent[0]["tool_choice"] == "auto"


def test_http_error_and_empty_stream(client):
    client.use(lambda r: httpx.Response(503, content=b"model busy"))
    with pytest.raises(EvrenError) as e:
        _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}]))
    assert e.value.status_code == 503
    client.use(lambda r: httpx.Response(200, content=b"data: [DONE]\n\n"))
    with pytest.raises(EvrenError):
        _run(client.chat("deepseek-v4-flash", [{"role": "user", "content": "x"}]))
