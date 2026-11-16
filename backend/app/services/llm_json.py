"""
JSON bekleyen Beyin AI çağrıları için ortak yardımcı (canlı test 16.11.2026: EVREN yoğunken keşif turu bozuk/yarım JSON döndü → 502).

Yanıt ayrıştırılamazsa model bir kez daha, kendi yanıtıyla birlikte "yalnız geçerli ve kısa JSON" talimatıyla çağrılır.
Tüm çağrılar llm_gateway üzerinden (fallback=True) yapılır; iki çağrının kredisi de sonuçta toplanır.
"""
import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.services import llm_gateway
from app.services.llm_gateway import GatewayChatResult, LLMContext

REPAIR = ("Önceki yanıtın geçerli bir JSON değildi (yarım kalmış ya da JSON dışında metin içeriyor olabilir). "
          "Aynı içeriği YALNIZ istenen şemada, geçerli ve daha kısa bir JSON olarak yeniden döndür; açıklama ya da kod bloğu ekleme.")


def parse(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if "```" in text:
        text = text.split("```")[1].removeprefix("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("JSON bulunamadı")
    return json.loads(text[start: end + 1])


async def chat_json(ctx: LLMContext, messages: List[Dict[str, str]], validate: Optional[Callable[[Dict[str, Any]], Any]] = None,
                    **kw) -> Tuple[Any, GatewayChatResult]:
    """(ayrıştırılmış/doğrulanmış sonuç, son model yanıtı). İki denemede de olmazsa ValueError."""
    kw.setdefault("fallback", True)
    result = await llm_gateway.chat(ctx, messages, **kw)
    try:
        data = parse(result.content)
        return (validate(data) if validate else data), result
    except (ValueError, KeyError, TypeError):
        pass
    retry = await llm_gateway.chat(ctx, messages + [{"role": "assistant", "content": (result.content or "")[:6000]},
                                                    {"role": "user", "content": REPAIR}], **kw)
    retry.credits = float(retry.credits or 0) + float(result.credits or 0)
    data = parse(retry.content)
    return (validate(data) if validate else data), retry
