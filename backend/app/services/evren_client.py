"""
TÜBİTAK BİLGEM EVREN (OpenAI uyumlu) düşük seviyeli HTTP istemcisi.

Doğrudan kullanılmaz: tüm çağrılar app/services/llm_gateway.py üzerinden geçer
(model seçimi, paket izni, kredi kontrolü ve ölçüm orada yapılır).

Hata durumunda sahte yanıt veya rastgele vektör üretilmez; EvrenError fırlatılır.
Eski istemcideki "mock" geri dönüşleri kesintileri gizliyor ve hafızayı rastgele
vektörlerle kirletiyordu.
"""
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


class EvrenClient:
    @property
    def base_url(self) -> str:
        return settings.EVREN_API_BASE_URL.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        if not settings.EVREN_API_KEY:
            raise EvrenError("EVREN API anahtarı tanımlı değil (.env: EVREN_API_KEY).")
        return {"Authorization": f"Bearer {settings.EVREN_API_KEY}", "Content-Type": "application/json"}

    async def _post(self, path: str, payload: Dict[str, Any], timeout: Optional[float] = None) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=timeout or settings.LLM_TIMEOUT_SECONDS) as client:
                resp = await client.post(f"{self.base_url}{path}", headers=self._headers(), json=payload)
        except httpx.TimeoutException as exc:
            raise EvrenError("EVREN yanıt vermedi (zaman aşımı).") from exc
        except httpx.HTTPError as exc:
            raise EvrenError(f"EVREN bağlantı hatası: {exc}") from exc
        if resp.status_code != 200:
            raise EvrenError(f"EVREN hata döndürdü ({resp.status_code}): {resp.text[:300]}", resp.status_code)
        return resp.json()

    async def chat(self, model_code: str, messages: List[Dict[str, str]], temperature: float = 0.7,
                   max_tokens: int = 4096, timeout: Optional[float] = None,
                   tools: Optional[List[Dict[str, Any]]] = None) -> ChatResult:
        body = {"model": model_code, "messages": messages, "temperature": temperature, "max_tokens": max_tokens, "stream": False}
        if tools:  # ADIM 10.2: EVREN OpenAI uyumlu function calling destekler (23.10.2026 denendi)
            body.update(tools=tools, tool_choice="auto")
        data = await self._post("/chat/completions", body, timeout)
        choices = data.get("choices") or []
        if not choices:
            raise EvrenError("EVREN boş yanıt döndürdü.")
        msg = choices[0].get("message") or {}
        reasoning = msg.get("reasoning") or msg.get("reasoning_content")
        content = msg.get("content") or reasoning or ""
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
