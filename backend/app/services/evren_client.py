"""
TÜBİTAK BİLGEM EVREN (OpenAI uyumlu) düşük seviyeli HTTP istemcisi.

Doğrudan kullanılmaz: tüm çağrılar app/services/llm_gateway.py üzerinden geçer
(model seçimi, paket izni, kredi kontrolü ve ölçüm orada yapılır).

Hata durumunda sahte yanıt veya rastgele vektör üretilmez; EvrenError fırlatılır.
Eski istemcideki "mock" geri dönüşleri kesintileri gizliyor ve hafızayı rastgele
vektörlerle kirletiyordu.
"""
import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from app.config import settings

logger = logging.getLogger("evren_client")


class EvrenError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ChatResult:
    content: str
    thought: Optional[str]
    tokens_in: int
    tokens_out: int
    raw: Dict[str, Any] = field(default_factory=dict)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # ADIM 10.2: OpenAI uyumlu araç çağrıları


@dataclass
class EmbeddingResult:
    vector: List[float]
    tokens_in: int


@dataclass
class RerankResult:
    results: List[Dict[str, Any]]
    tokens_in: int


def estimate_tokens(text: str) -> int:
    """Sağlayıcı usage döndürmezse kaba tahmin (Türkçe için ~3,5 karakter/token)."""
    return max(1, int(len(text or "") / 3.5))


# Bağlantı kurulamadıysa (DNS, bağlantı reddi) istek EVREN'e ulaşmamıştır; kısa aralarla yeniden denemek güvenlidir
# (çift işlem/ücret oluşmaz). 26.10.2026: bilgisayarın ağındaki birkaç saniyelik DNS kopmaları işi düşürüyordu.
CONNECT_RETRY_DELAYS = (3, 8)


async def _send(make_request):
    for delay in (*CONNECT_RETRY_DELAYS, None):
        try:
            return await make_request()
        except httpx.ConnectError:
            if delay is None:
                raise
            await asyncio.sleep(delay)


def retry_after_seconds(status_code: int, headers) -> Optional[float]:
    """429 + Retry-After (saniye): beklenecek süre; başlık yok/tarih biçiminde/çok uzunsa None (#666)."""
    if status_code != 429:
        return None
    try:
        wait = float((headers or {}).get("Retry-After"))
    except (TypeError, ValueError):
        return None
    return wait if 0 <= wait <= settings.EVREN_RETRY_AFTER_MAX_SECONDS else None


def thinking_enabled(model_code: str, purpose: Optional[str] = None) -> bool:
    """EVREN'de sohbet modelleri varsayılan olarak düşünür; EVREN_NO_THINKING_MODELS'takilerde kapatılır (#666).
    EVREN_THINKING_PURPOSES'taki amaçlarda (iş adımları) her modelde açık kalır (F85)."""
    keep = {p.strip().upper() for p in (settings.EVREN_THINKING_PURPOSES or "").split(",") if p.strip()}
    if purpose and purpose.upper() in keep:
        return True
    off = {m.strip().lower() for m in (settings.EVREN_NO_THINKING_MODELS or "").split(",") if m.strip()}
    return (model_code or "").lower() not in off


class _RetryLater(Exception):
    def __init__(self, wait: float):
        self.wait = wait


class StreamAccumulator:
    """OpenAI uyumlu SSE akışını tek yanıta toplar. İlk token = içerik, düşünme veya araç çağrısı parçası;
    kuyruktaki keep-alive satırları ve yalnız rol taşıyan parça sayılmaz."""

    def __init__(self):
        self.content: List[str] = []
        self.reasoning: List[str] = []
        self.calls: Dict[int, Dict[str, Any]] = {}
        self.finish_reason: Optional[str] = None
        self.usage: Dict[str, Any] = {}
        self.meta: Dict[str, Any] = {}
        self.got_first = False
        self.chunks = 0
        self.done = False

    def feed(self, line: str) -> None:
        line = (line or "").strip()
        if not line.startswith("data:"):
            return  # ": keep-alive", boş satır, event: ...
        payload = line[5:].strip()
        if payload == "[DONE]":
            self.done = True
            return
        try:
            chunk = json.loads(payload)
        except ValueError:
            return
        if chunk.get("error"):
            raise EvrenError(f"EVREN akış hatası: {str(chunk['error'])[:300]}")
        self.chunks += 1
        for key in ("id", "model", "created"):
            if chunk.get(key) is not None:
                self.meta.setdefault(key, chunk[key])
        if chunk.get("usage"):
            self.usage = chunk["usage"]
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            text = delta.get("content")
            thought = delta.get("reasoning") or delta.get("reasoning_content")
            if text:
                self.content.append(text)
                self.got_first = True
            if thought:
                self.reasoning.append(thought)
                self.got_first = True
            for tc in delta.get("tool_calls") or []:
                self.got_first = True
                cur = self.calls.setdefault(int(tc.get("index") or 0),
                                            {"id": None, "type": "function", "function": {"name": "", "arguments": ""}})
                if tc.get("id"):
                    cur["id"] = tc["id"]
                if tc.get("type"):
                    cur["type"] = tc["type"]
                fn = tc.get("function") or {}
                if fn.get("name"):
                    cur["function"]["name"] += fn["name"]
                if fn.get("arguments"):
                    cur["function"]["arguments"] += fn["arguments"]
            if choice.get("finish_reason"):
                self.finish_reason = choice["finish_reason"]

    def raw(self) -> Dict[str, Any]:
        """Akışsız yanıtla aynı biçim (finish_reason ve usage.evren kullananlar için)."""
        message = {"role": "assistant", "content": "".join(self.content), "reasoning": "".join(self.reasoning) or None}
        if self.calls:
            message["tool_calls"] = [self.calls[i] for i in sorted(self.calls)]
        return {**self.meta, "object": "chat.completion", "usage": self.usage,
                "choices": [{"index": 0, "message": message, "finish_reason": self.finish_reason}]}


class EvrenClient:
    transport: Optional[httpx.AsyncBaseTransport] = None  # testlerde httpx.MockTransport

    @property
    def base_url(self) -> str:
        return settings.EVREN_API_BASE_URL.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        if not settings.EVREN_API_KEY:
            raise EvrenError("EVREN API anahtarı tanımlı değil (.env: EVREN_API_KEY).")
        return {"Authorization": f"Bearer {settings.EVREN_API_KEY}", "Content-Type": "application/json"}

    def _client(self, timeout) -> httpx.AsyncClient:
        if self.transport is not None:
            return httpx.AsyncClient(timeout=timeout, transport=self.transport)
        return httpx.AsyncClient(timeout=timeout)

    async def _post(self, path: str, payload: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        async def go():
            async with self._client(timeout or settings.LLM_TIMEOUT_SECONDS) as client:
                return await client.post(f"{self.base_url}{path}", headers=self._headers(), json=payload)

        for attempt in (0, 1):
            try:
                resp = await _send(go)
            except httpx.TimeoutException as exc:
                raise EvrenError("EVREN yanıt vermedi (zaman aşımı).") from exc
            except httpx.HTTPError as exc:
                raise EvrenError(f"EVREN bağlantı hatası: {exc}") from exc
            wait = retry_after_seconds(resp.status_code, resp.headers) if attempt == 0 else None
            if wait is None:
                break
            logger.warning("EVREN 429 (%s); Retry-After %.0f sn beklenip yeniden deneniyor.", path, wait)
            await asyncio.sleep(wait)
        if resp.status_code != 200:
            raise EvrenError(f"EVREN hata döndürdü ({resp.status_code}): {resp.text[:300]}", resp.status_code)
        return resp.json()

    async def chat(self, model_code: str, messages: List[Dict[str, str]], temperature: float = 0.7,
                   max_tokens: int = 4096, timeout: Optional[float] = None,
                   tools: Optional[List[Dict[str, Any]]] = None, first_token_timeout: Optional[float] = None,
                   purpose: Optional[str] = None) -> ChatResult:
        """Akışlı çağrı (#666, EVREN önerisi): ilk token first_token_timeout içinde gelmezse model meşgul sayılır ve
        EvrenError fırlatılır (gateway yedek modele geçer); timeout tüm çağrının üst sınırıdır."""
        thinking = thinking_enabled(model_code, purpose)
        if thinking:  # düşünme de bütçeden yer; EVREN: en az 2048, önerilen 4096
            max_tokens = max(max_tokens, settings.LLM_THINKING_MIN_TOKENS)
        body = {"model": model_code, "messages": messages, "temperature": temperature, "max_tokens": max_tokens,
                "stream": True, "stream_options": {"include_usage": True}}
        if not thinking:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        penalized = {p.strip().upper() for p in (settings.EVREN_REPETITION_PURPOSES or "").split(",") if p.strip()}
        if purpose and purpose.upper() in penalized and settings.EVREN_REPETITION_PENALTY > 1:
            body["repetition_penalty"] = settings.EVREN_REPETITION_PENALTY  # F85: uzun kodda tekrar döngüsü
        if tools:  # ADIM 10.2: EVREN OpenAI uyumlu function calling destekler (23.10.2026 denendi)
            body.update(tools=tools, tool_choice="auto")
        total = float(timeout or settings.LLM_TIMEOUT_SECONDS)
        ttft = min(float(first_token_timeout or settings.LLM_FIRST_TOKEN_TIMEOUT_SECONDS), total)

        acc = None
        for attempt in (0, 1):
            try:
                acc = await asyncio.wait_for(_send(lambda: self._stream_chat(body, total, ttft)), total)
                break
            except _RetryLater as later:
                if attempt == 1:
                    raise EvrenError("EVREN istek sınırına ulaşıldı (429).", 429)
                logger.warning("EVREN 429 (%s); Retry-After %.0f sn beklenip yeniden deneniyor.", model_code, later.wait)
                await asyncio.sleep(later.wait)
            except asyncio.TimeoutError as exc:
                raise EvrenError(f"EVREN yanıt vermedi (zaman aşımı, {total:.0f} sn).") from exc
            except httpx.TimeoutException as exc:
                raise EvrenError("EVREN yanıt vermedi (zaman aşımı).") from exc
            except httpx.HTTPError as exc:
                raise EvrenError(f"EVREN bağlantı hatası: {exc}") from exc
        if acc is None or not acc.chunks:
            raise EvrenError("EVREN boş yanıt döndürdü.")
        data = acc.raw()
        msg = data["choices"][0]["message"]
        reasoning = msg.get("reasoning")
        content = msg.get("content") or ""  # düşünme metni asla yanıt yerine kullanılmaz (F60)
        usage = data.get("usage") or {}
        prompt_text = " ".join(str(m.get("content", "")) for m in messages)
        return ChatResult(
            content=content,
            thought=reasoning,
            tokens_in=int(usage.get("prompt_tokens") or estimate_tokens(prompt_text)),
            tokens_out=int(usage.get("completion_tokens") or estimate_tokens(content)),
            raw=data,
            tool_calls=list(msg.get("tool_calls") or []),
        )

    async def _stream_chat(self, body: Dict[str, Any], total: float, ttft: float) -> StreamAccumulator:
        loop = asyncio.get_running_loop()
        first_deadline = loop.time() + ttft
        acc = StreamAccumulator()
        async with self._client(httpx.Timeout(total, connect=15.0)) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", headers=self._headers(), json=body) as resp:
                if resp.status_code != 200:
                    text = (await resp.aread()).decode("utf-8", errors="replace")[:300]
                    wait = retry_after_seconds(resp.status_code, resp.headers)
                    if wait is not None:
                        raise _RetryLater(wait)
                    raise EvrenError(f"EVREN hata döndürdü ({resp.status_code}): {text}", resp.status_code)
                lines = resp.aiter_lines()
                while not acc.done:
                    try:
                        if acc.got_first:
                            line = await lines.__anext__()
                        else:
                            remaining = first_deadline - loop.time()
                            if remaining <= 0:
                                raise asyncio.TimeoutError
                            line = await asyncio.wait_for(lines.__anext__(), remaining)
                    except StopAsyncIteration:
                        break
                    except asyncio.TimeoutError:
                        raise EvrenError(f"EVREN {ttft:.0f} sn içinde yanıt vermeye başlamadı (model meşgul).") from None
                    acc.feed(line)
        return acc

    async def embed(self, text: str, model_code: str) -> EmbeddingResult:
        data = await self._post("/embeddings", {"model": model_code, "input": text})
        try:
            vector = data["data"][0]["embedding"]
        except (KeyError, IndexError) as exc:
            raise EvrenError("EVREN embedding yanıtı beklenen biçimde değil.") from exc
        usage = data.get("usage") or {}
        return EmbeddingResult(vector=vector, tokens_in=int(usage.get("prompt_tokens") or usage.get("total_tokens") or estimate_tokens(text)))

    async def ocr(self, png_bytes: bytes, model_code: str) -> str:
        """EVREN /ocr ucu: gömülü (data URL) görselden metin okur. Usage döndürmez."""
        import base64

        data = await self._post("/ocr", {
            "model": model_code, "image": "data:image/png;base64," + base64.b64encode(png_bytes).decode(),
        }, timeout=120)
        return str(data.get("text") or "")

    async def transcribe(self, audio: bytes, filename: str, mime: str, model_code: str, language: str = "tr", timeout: float = 300) -> str:
        """EVREN /audio/transcriptions (OpenAI uyumlu, çok parçalı form). Dosya boyutu sınırı ~25 MB (24.10.2026 ölçüldü)."""
        if not settings.EVREN_API_KEY:
            raise EvrenError("EVREN API anahtarı tanımlı değil (.env: EVREN_API_KEY).")
        async def go():
            async with httpx.AsyncClient(timeout=timeout) as client:
                return await client.post(f"{self.base_url}/audio/transcriptions", headers={"Authorization": f"Bearer {settings.EVREN_API_KEY}"},
                                         files={"file": (filename, audio, mime)}, data={"model": model_code, "language": language})

        try:
            resp = await _send(go)
        except httpx.TimeoutException as exc:
            raise EvrenError("EVREN yanıt vermedi (zaman aşımı).") from exc
        except httpx.HTTPError as exc:
            raise EvrenError(f"EVREN bağlantı hatası: {exc.__class__.__name__}") from exc
        if resp.status_code != 200:
            raise EvrenError(f"EVREN hata döndürdü ({resp.status_code}): {resp.text[:300]}", resp.status_code)
        return str(resp.json().get("text") or "")

    async def rerank(self, query: str, documents: List[str], model_code: str, top_n: int = 5) -> RerankResult:
        data = await self._post("/rerank", {"model": model_code, "query": query, "documents": documents, "top_n": top_n})
        usage = data.get("usage") or {}
        tokens = int(usage.get("prompt_tokens") or usage.get("total_tokens") or estimate_tokens(query + " ".join(documents)))
        return RerankResult(results=data.get("results") or [], tokens_in=tokens)

    async def list_models(self) -> List[Dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(f"{self.base_url}/models", headers=self._headers())
        except httpx.HTTPError as exc:
            raise EvrenError(f"EVREN bağlantı hatası: {exc}") from exc
        if resp.status_code != 200:
            raise EvrenError(f"EVREN model listesi alınamadı ({resp.status_code}).", resp.status_code)
        return resp.json().get("data") or []


evren_client = EvrenClient()
