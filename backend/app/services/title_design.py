"""
İSTEK #739 — Ünvan tanımlama sohbeti (Merkez katalog ve Şirket Yönetimi).

Kullanıcı ünvanın özelliklerini serbest metinle anlatır; RECAi eksik bilgiyi kısa sorularla tamamlar ve her turda ünvan
taslağını (iş tanımı, sorumluluklar, yetkinlikler, başarı ölçütleri, rol promptu) günceller. Kullanıcı taslağı forma alır
ve kaydeder; sohbet hiçbir şeyi kendiliğinden kaydetmez.

Sektörden bağımsızdır: diş kliniği, turizm, üretim, muhasebe, yazılım… Rol promptuna platformun iş disiplini (adım çıktısının
kabul ölçütüne göre teslimi, belirsizlikte soru sorma, bilmediğini uydurmama, onay gerektiren işte onaya bırakma) yazılır.
Tüm model çağrıları llm_gateway üzerinden, meşgul modelde yedek modelle (fallback=True).
"""
import json
import re
import uuid
from typing import Any, Dict, List, Optional

MAX_TURNS, MAX_MSG = 16, 2000
FIELDS = ("title", "description", "responsibilities", "required_skills", "kpis", "base_role_prompt")

SYSTEM = """Sen RECOrion'un ünvan tasarım asistanı RECAi'sin. Kullanıcıyla sohbet ederek bir AI personel ünvanını tanımlarsın.
Ünvan her sektörden olabilir (sağlık, turizm, üretim, finans, hukuk, eğitim, yazılım…); sektörü kullanıcının anlatımından çıkar,
yazılım varsayma.

Çalışma biçimin:
- Kullanıcının anlattıklarından taslağı HER TURDA doldur/güncelle; eksik kalan en önemli 1–3 noktayı kısa sorularla sor
  (ör. hangi çıktıları üretecek, kime teslim edecek, hangi sistemleri kullanacak, neyi asla yapmamalı, başarı nasıl ölçülür).
- Yeterli bilgi olduğunda soru sormayı bırak, "hazir": true yap ve kullanıcıya taslağı forma alabileceğini söyle.
- Kullanıcı bir alanı düzeltirse yalnız onu değiştir, gerisini koru.
- Uydurma kurum bilgisi (kişi adı, tutar, sistem adı) ekleme; bilinmeyen yerde genel ifade kullan.

Rol promptu (base_role_prompt) kuralları — AI personelin sistem talimatıdır, Türkçe, ikinci tekil şahıs ("Sen …sın"):
1. Rol ve kimlik, şirketteki misyonu ({{company_name}} ve {{department_name}} yer tutucularını kullan).
2. Temel sorumluluklar ve çalışma ilkeleri.
3. Kalite kapıları: çıktıyı adımın kabul ölçütüne göre kendin denetle; ölçüt yoksa varsayımını açıkça yaz; bilmediğini
   uydurma; belirsizlikte soru sor; onay gerektiren işi (dış gönderim, ödeme, silme) onaya bırak.
4. Gizlilik: kişisel veriyi yalnız işin gerektirdiği kadar kullan (KVKK); şirket bilgisini dışarı verme.
5. Çıktı biçimi ve tonu.
Model veya sağlayıcı adı yazma; yapay zekanın adı RECAi'dir.

Yanıtı YALNIZCA şu JSON ile ver:
{"cevap": "<kullanıcıya kısa yanıt ve sorular, en fazla 8 satır>",
 "taslak": {"title": "...", "description": "...", "responsibilities": ["..."], "required_skills": ["..."], "kpis": ["..."],
            "base_role_prompt": "..."},
 "hazir": false}"""


def _json(text: str) -> Dict[str, Any]:
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def _list(v: Any) -> List[str]:
    if isinstance(v, str):
        v = [x.strip(" -•\t") for x in v.splitlines()]
    return [str(x).strip()[:300] for x in (v or []) if str(x).strip()][:20]


def clean_draft(d: Any, prev: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Model taslağını güvenli alanlara indirger; modelin boş bıraktığı alan önceki taslaktan korunur."""
    prev = prev or {}
    d = d if isinstance(d, dict) else {}
    out: Dict[str, Any] = {}
    for k in FIELDS:
        v = d.get(k)
        if k in ("responsibilities", "required_skills", "kpis"):
            v = _list(v) or _list(prev.get(k))
        else:
            v = (str(v).strip() if v else "") or (str(prev.get(k) or "").strip())
            v = v[:12000] if k == "base_role_prompt" else v[:2000] if k == "description" else v[:128]
        out[k] = v
    return out


def _context_text(ctx: Dict[str, Any]) -> str:
    parts = []
    for key, label in (("company", "Şirket"), ("sector", "Sektör"), ("department", "Departman"), ("seniority", "Kıdem"),
                       ("autonomy_level", "Otonomi")):
        if ctx.get(key):
            parts.append(f"{label}: {ctx[key]}")
    return "\n".join(parts) or "(belirtilmedi)"


async def chat(tenant_id: Optional[uuid.UUID], messages: List[Dict[str, str]], draft: Optional[Dict[str, Any]],
               context: Optional[Dict[str, Any]] = None, actor_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
    """Bir sohbet turu. tenant_id None: Merkez (RECDx platform maliyeti); dolu: şirketin kredisi."""
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    hist = [{"role": m.get("role"), "content": str(m.get("content") or "")[:MAX_MSG]}
            for m in (messages or []) if m.get("role") in ("user", "assistant") and str(m.get("content") or "").strip()][-MAX_TURNS:]
    if not hist or hist[-1]["role"] != "user":
        raise ValueError("Sohbetin son mesajı kullanıcıdan olmalı.")
    prev = clean_draft(draft or {})
    state = (f"BAĞLAM:\n{_context_text(context or {})}\n\nŞU ANKİ TASLAK (JSON):\n"
             f"{json.dumps(prev, ensure_ascii=False)}")
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "system", "content": state}, *hist]
    res = await llm_gateway.chat(LLMContext(tenant_id=tenant_id, purpose="ROLE_PROMPT", actor_id=actor_id), msgs,
                                 temperature=0.4, max_tokens=6144, timeout=150, fallback=True)
    data = _json(res.content)
    if not data:  # JSON gelmediyse metni yanıt olarak göster, taslak korunur
        return {"reply": (res.content or "").strip()[:3000] or "Yanıt okunamadı; lütfen tekrar deneyin.", "draft": prev,
                "ready": False, "credits": res.credits}
    return {"reply": str(data.get("cevap") or "").strip()[:3000] or "Taslağı güncelledim.",
            "draft": clean_draft(data.get("taslak"), prev), "ready": bool(data.get("hazir")), "credits": res.credits}
