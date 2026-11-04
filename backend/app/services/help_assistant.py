"""
RECAi Yardım Asistanı — ADIM 15.4.

Kullanıcı sorusunu kendi cümlesiyle sorar; RECAi yalnızca kullanıcının yetkisi dahilindeki kılavuz sayfalarından yanıt verir,
dayandığı sayfaları ve (varsa) ilgili ekranı ("Ekrana git") döndürür.

Yetki: aday sayfalar tüm yardım içeriğinde aranır; konu yalnız (veya ağırlıkla) kullanıcının göremediği sayfalardaysa modele
hiç gidilmez ve "yetkiniz dahilinde değil, cevap veremiyorum" denir. Yetkisiz sayfaların içeriği modele verilmez, adı da
yalnız müşteri kılavuzlarına aitse söylenir (Merkez Yönetim içeriği müşteriye hiç anılmaz).
Tüm model çağrıları llm_gateway üzerinden, meşgul modelde yedek modelle (fallback=True).
"""
import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.services import help_center as hc

logger = logging.getLogger("recorion.help")

DENY = ("Bu konu yetkiniz dahilindeki modüllerin dışında kaldığı için cevap veremiyorum. Bu işe ihtiyacınız varsa şirket "
        "yöneticinizden ilgili yetkiyi isteyebilirsiniz.")
NOT_FOUND = ("Kılavuzda bu soruyla ilgili bir bölüm bulamadım. Soruyu ekran veya menü adıyla (ör. \"Otomasyonlar ekranında RECSlip "
             "nasıl kurulur?\") yeniden sorabilirsiniz.")
DEADLINE = 150.0  # sn; EVREN sırada beklettiğinde kullanıcı dakikalarca beklemesin, yardım sayfalarıyla dönülür
DENY_RATIO = 2.0  # en iyi yetkisiz eşleşme, en iyi yetkili eşleşmeden bu kat güçlüyse konu yetki dışı sayılır
MAX_PAGES, MAX_CHARS = 4, 3500

SYSTEM = """Sen RECOrion'un yardım asistanı RECAi'sin. Kullanıcıya RECOrion ekranlarının nasıl kullanılacağını anlatırsın.
Kurallar:
- Yalnızca aşağıda verilen KILAVUZ BÖLÜMLERİNE dayan. Orada olmayan bir şeyi uydurma; bilmiyorsan "kılavuzda bulamadım" de.
- Kullanıcının göremediği modüller hakkında bilgi verme; soru verilen bölümlerin dışındaysa "yetkiniz dahilinde değil" de ve
  "yetki_disi" alanını true yap.
- Türkçe, kısa ve adım adım yaz. Ekrandaki düğme ve menü adlarını **kalın** yaz. En fazla 12 satır.
- Yapay zekanın adı RECAi'dir. Model veya sağlayıcı adı yazma.
Yanıtı yalnızca şu JSON ile ver:
{"cevap": "...", "kaynaklar": ["<kullandığın bölümlerin slug'ları>"], "ekran": "<ilgili ekran anahtarı veya boş>", "yetki_disi": false}"""


def _json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def _src(p) -> Dict[str, Any]:
    return {"slug": p.slug, "title": p.title, "guide_title": hc.guide_title(p.guide), "section": p.section}


def _clip(body: str) -> str:
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body or "")
    return body[:MAX_CHARS] + (" …" if len(body) > MAX_CHARS else "")


async def ask(db: AsyncSession, user: CurrentUser, question: str, history: Optional[List[Dict[str, str]]] = None,
              screen: Optional[str] = None) -> Dict[str, Any]:
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext, LLMError

    question = (question or "").strip()[:1000]
    if len(question) < 3:
        return {"answer": "Lütfen sorunuzu biraz daha açık yazın.", "sources": [], "navigate": None, "denied": False}
    hits = await hc.search(db, user, question, include_hidden=True)
    allowed = [(p, r) for p, r, _ in hits if hc.can_see(user, p)]
    hidden = [(p, r) for p, r, _ in hits if not hc.can_see(user, p)]
    # Bulunulan ekranın sayfası (görebiliyorsa) soruya bağlam olarak eklenir
    ctx_page = None
    if screen:
        c = await hc.context(db, user, screen)
        if c:
            ctx_page = next((p for p in await hc.visible(db, user) if p.slug == c["page"]["slug"]), None)
    if hidden and (not allowed or hidden[0][1] > DENY_RATIO * allowed[0][1]):
        about = next((p for p, _ in hidden if p.audience == "CUSTOMER"), None)
        extra = f" (İlgili bölüm: {hc.guide_title(about.guide)} › {about.title}.)" if about else ""
        return {"answer": DENY + extra, "sources": [], "navigate": None, "denied": True}
    pages = [p for p, _ in allowed[:MAX_PAGES]]
    if ctx_page and ctx_page not in pages:
        pages = [ctx_page] + pages[:MAX_PAGES - 1]
    if not pages:
        return {"answer": NOT_FOUND, "sources": [], "navigate": None, "denied": False}

    by_slug = {p.slug: p for p in pages}
    screens = sorted({k for p in pages for k in (p.screen_keys or []) if not k.endswith("/")})
    blocked = []
    for p, _ in hidden[:6]:
        name = f"{hc.guide_title(p.guide)} › {p.title}" if p.audience == "CUSTOMER" else "RECDx Ana Kontrol Merkezi ekranları"
        if name not in blocked:
            blocked.append(name)
    excerpts = "\n\n".join(f"### [{p.slug}] {hc.guide_title(p.guide)} › {p.section} › {p.title}\n{_clip(p.body)}" for p in pages)
    msgs = [{"role": "system", "content": f"{SYSTEM}\n\nKullanılabilecek ekran anahtarları: {', '.join(screens) or '(yok)'}\n\n"
                                          + (f"Kullanıcının YETKİSİ OLMAYAN konular (soru esas olarak bunlarla ilgiliyse yetki_disi=true; "
                                             f"bunlar hakkında bilgi verme): {'; '.join(blocked)}\n\n" if blocked else "")
                                          + f"KILAVUZ BÖLÜMLERİ:\n{excerpts}"}]
    for h in (history or [])[-6:]:
        if h.get("role") in ("user", "assistant") and h.get("content"):
            msgs.append({"role": h["role"], "content": str(h["content"])[:1500]})
    msgs.append({"role": "user", "content": question})
    try:
        result = await asyncio.wait_for(
            llm_gateway.chat(LLMContext(tenant_id=user.tenant_id, purpose="BRAIN", task_type="WRITING"), msgs,
                             temperature=0.2, max_tokens=1200, timeout=120, fallback=True),
            timeout=DEADLINE)
    except (LLMError, asyncio.TimeoutError) as exc:
        logger.warning("Yardım asistanı yanıt alamadı: %s", exc)
        return {"answer": "RECAi şu anda yanıt veremiyor. Sorunuzla ilgili yardım sayfaları aşağıda.",
                "sources": [_src(p) for p in pages], "navigate": None, "denied": False, "degraded": True}
    data = _json(result.content)
    answer = str(data.get("cevap") or "").strip() or (result.content or "").strip()[:2000]
    if data.get("yetki_disi") is True:
        return {"answer": DENY, "sources": [], "navigate": None, "denied": True}
    used = [by_slug[s] for s in (data.get("kaynaklar") or []) if s in by_slug] or pages[:2]
    nav = data.get("ekran") if data.get("ekran") in screens else None
    return {"answer": answer, "sources": [_src(p) for p in used], "navigate": nav, "denied": False}
