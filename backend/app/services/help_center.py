"""
Yardım (Bilgi Birikimi) — ADIM 15.2.

İçerik: app/help_content/{merkez,sirket,workarea}.md (kullanım kılavuzları v2; kodla birlikte sürümlenir) ve img/*.webp.
Uygulama açılırken dosyalar değiştiyse help_pages tablosu yeniden kurulur (Türkçe tam metin araması için).

Sayfa yapısı: kılavuz › bölüm (#) › sayfa (##). Uzun sayfaların (Work Space › Projeler gibi) ### başlıkları ayrı sayfa olur.
Her sayfa: kitle (RECDX: yalnız RECDx süper yöneticileri; CUSTOMER: şirket kullanıcıları ve RECDx), izinler (biri yeterli;
boş = kitledeki herkes) ve ekran anahtarları (F1 / "Bu ekran": super/<SEKME>, company/<SEKME>, workspace/<MOD>,
workspace/project/<sekme>).
"""
import hashlib
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.models import HelpPage, SystemSetting

CONTENT = Path(__file__).resolve().parent.parent / "help_content"
IMG = CONTENT / "img"
GUIDES = [("merkez", "Merkez Yönetim Kılavuzu", "RECDX"), ("sirket", "Şirket Yönetimi Kılavuzu", "CUSTOMER"),
          ("workarea", "Work Area Kılavuzu", "CUSTOMER")]
STOP = {"nasıl", "nasil", "neden", "nerede", "hangi", "için", "icin", "veya", "gibi", "olan", "bunu", "şunu", "ekranında", "ekranından", "ekranı"}
SPLIT_CHARS = 30000  # bundan uzun ## bölümlerinin ### başlıkları ayrı sayfa olur
HASH_KEY = "help_content_hash"

# (kılavuz, ## başlığı) -> ekran anahtarları. Başlıklar kılavuzdaki gibi (büyük/küçük harf ve noktalama önemsiz).
SCREENS: Dict[Tuple[str, str], List[str]] = {
    ("merkez", "Dashboard (Genel Bakış)"): ["super/DASHBOARD"], ("merkez", "Başvuru Onay Durum"): ["super/LEADS"],
    ("merkez", "Kayıtlı Şirketler"): ["super/TENANTS"], ("merkez", "Sektör Tanımları"): ["super/SECTORS"],
    ("merkez", "Meslek Tanımları"): ["super/PROFESSIONS"], ("merkez", "Departman & Unvan"): ["super/CATALOG"],
    ("merkez", "Proje Şablonları"): ["super/PROJECT_TEMPLATES"], ("merkez", "Mevzuat Paketleri"): ["super/REGULATIONS"],
    ("merkez", "Bağlantı Kataloğu"): ["super/INTEGRATION_CATALOG"], ("merkez", "Uygulama Talepleri"): ["super/APP_REQUESTS"],
    ("merkez", "Kiralama Paketleri"): ["super/PLANS"], ("merkez", "İzin Kataloğu (RBAC)"): ["super/PERMISSIONS"],
    ("merkez", "Yetki Rolleri"): ["super/ROLES"], ("merkez", "E-Posta Şablonları"): ["super/EMAIL_TEMPLATES"],
    ("merkez", "Zamanlayıcılar (Schedules)"): ["super/SCHEDULES"], ("merkez", "Model Yönlendirici"): ["super/MODEL_ROUTER"],
    ("merkez", "Genel AI Modelleri"): ["super/AI_MODEL_SETTINGS"], ("merkez", "Yönetici Asistanı"): ["super/AI_ASSISTANT"],
    ("merkez", "RECAi ve EVREN Modelleri"): ["super/MODELS"], ("merkez", "LLM TL Fiyatları"): ["super/LLM_PRICES"],
    ("merkez", "Sol menü"): ["super/"],
    ("sirket", "Genel Bakış"): ["company/DASHBOARD"], ("sirket", "Şirket Profili"): ["company/COMPANY_PROFILE"],
    ("sirket", "Kullanıcı Yönetimi"): ["company/USERS"], ("sirket", "AI Ajan İşe Alım"): ["company/AI_AGENTS"],
    ("sirket", "Departmanlar"): ["company/DEPARTMENTS"], ("sirket", "Ünvan Tanımları"): ["company/JOB_TITLES"],
    ("sirket", "Sektörel Manifesto"): ["company/MANIFESTO"], ("sirket", "Beyin AI"): ["company/BRAIN"],
    ("sirket", "Entegrasyonlar"): ["company/INTEGRATIONS"], ("sirket", "Otomasyonlar"): ["company/AUTOMATIONS"],
    ("sirket", "Mevzuat Paketleri"): ["company/REGULATIONS"], ("sirket", "Kredi ve Kullanım"): ["company/CREDITS"],
    ("sirket", "Ekran düzeni"): ["company/"],
    ("workarea", "Projeler ve Case'ler ekranı"): ["workspace/HUB"], ("workarea", "Proje ekranı"): ["workspace/project/"],
    ("workarea", "Bilgiler & İsterler sekmesi"): ["workspace/project/info"], ("workarea", "Proje Ekleri sekmesi"): ["workspace/project/docs"],
    ("workarea", "Beyin AI Planlama sekmesi"): ["workspace/project/plan"], ("workarea", "Ekip & Simülasyon sekmesi"): ["workspace/project/team"],
    ("workarea", "Hazırlık & Bildirim sekmesi"): ["workspace/project/ready"], ("workarea", "İş Akışı sekmesi"): ["workspace/project/flow"],
    ("workarea", "Maliyet sekmesi"): ["workspace/project/cost"], ("workarea", "Kod Deposu sekmesi"): ["workspace/project/repo"],
    ("workarea", "RECSlip sekmesi"): ["workspace/project/recslip"], ("workarea", "Kapanış sekmesi"): ["workspace/project/close"],
    ("workarea", "Onaylarım"): ["workspace/INBOX"], ("workarea", "Çalışma Alanı"): ["workspace/WORK"],
    ("workarea", "Bağlantılarım"): ["workspace/LINKS"], ("workarea", "Pano"): ["workspace/PANO"],
    ("workarea", "Üst çubuk ve mod çubuğu"): ["workspace/"],
}
# Şirket Yönetimi menülerinin izinleri (frontend/src/permissions.js MENU_PERMISSIONS ile aynı): sayfa yalnız menüyü görebilene
MENU_PERMS = {
    "DASHBOARD": ["dashboard:view"], "COMPANY_PROFILE": ["tenant:manage"], "USERS": ["user:invite", "user:manage"],
    "AI_AGENTS": ["agent:hire", "agent:configure", "agent:quarantine"], "DEPARTMENTS": ["org:manage"], "JOB_TITLES": ["agent:custom_title"],
    "MANIFESTO": ["manifesto:manage"], "BRAIN": ["brain:manage"], "INTEGRATIONS": ["integration:manage", "mapping:manage", "integration:approve"],
    "AUTOMATIONS": ["automation:manage"], "REGULATIONS": ["regulation:manage"], "CREDITS": ["billing:view"],
}
# Anahtar dışında izne bağlı sayfalar (kılavuz, # bölüm) / (kılavuz, ## sayfa)
EXTRA_PERMS = {
    ("sirket", "RECSlip.App v2 ile aylık masraf süreci"): ["automation:manage", "integration:manage"],
    ("workarea", "Pano"): ["department:dashboard", "dashboard:view"],
    ("workarea", "Maliyet sekmesi"): ["project:manage", "cost:view"],
}


@dataclass
class Page:
    guide: str
    slug: str
    title: str
    parent: Optional[str]
    order: int
    level: int
    body: str
    audience: str
    screens: List[str] = field(default_factory=list)
    perms: List[str] = field(default_factory=list)
    section: str = ""


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").replace("ı", "i").replace("İ", "I")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def slugify(s: str) -> str:
    return norm(s).replace(" ", "-")[:60] or "sayfa"


SCREENS_N = {(g, norm(t)): v for (g, t), v in SCREENS.items()}
EXTRA_N = {(g, norm(t)): v for (g, t), v in EXTRA_PERMS.items()}
SHOT = re.compile(r"^\s*\[\[EKRAN:\s*([^|\]]+?)\s*\|\s*([^|\]]+?)\s*(\|[^\]]*)?\]\]\s*$")


_VER: Dict[str, Tuple[float, int, str]] = {}


def img_version(name: str) -> str:
    """Görselin içerik özeti (8 karakter). Adrese ?v= olarak eklenir: görsel değişince tarayıcı önbelleği eskiyi göstermez."""
    f = IMG / name
    st = f.stat()
    cached = _VER.get(name)
    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
        return cached[2]
    v = hashlib.md5(f.read_bytes()).hexdigest()[:8]
    _VER[name] = (st.st_mtime, st.st_size, v)
    return v


def _body(lines: List[str]) -> str:
    """İşaretleri görsele çevirir: [[EKRAN: ad | açıklama | ...]] -> ![açıklama](ad.webp) (+ devam parçaları); görseli yoksa atlanır."""
    out = []
    for ln in lines:
        m = SHOT.match(ln)
        if not m:
            out.append(ln)
            continue
        name, cap = m.group(1), m.group(2)
        for i, suffix in enumerate(["", "__2", "__3"]):
            if (IMG / f"{name}{suffix}.webp").exists():
                ver = img_version(f"{name}{suffix}.webp")
                out.append(f"![{cap}{' (devamı)' if i else ''}]({name}{suffix}.webp?v={ver})")
    return "\n".join(out).strip()


def _perms_for(guide: str, section: str, title: str, screens: List[str]) -> List[str]:
    perms: List[str] = []
    for k in screens:
        if k.startswith("company/") and k[8:] in MENU_PERMS:
            perms += MENU_PERMS[k[8:]]
    perms += EXTRA_N.get((guide, norm(title)), []) + EXTRA_N.get((guide, norm(section)), [])
    return sorted(set(perms))


def parse(guide: str, text_: str, audience: str) -> List[Page]:
    lines = text_.splitlines()
    start = next((i for i, l in enumerate(lines) if re.match(r"^# Bu kılavuz hakkında", l)), 0)
    lines = lines[start:]
    pages: List[Page] = []
    order = 0
    sec_slug = sec_title = None
    sec_intro: List[str] = []
    i = 0

    def heads(level: int, i0: int) -> int:
        """level başlığının bittiği satır (bir sonraki aynı/üst seviye başlık)."""
        j = i0 + 1
        while j < len(lines) and not re.match(r"^#{1,%d} " % level, lines[j]):
            j += 1
        return j

    while i < len(lines):
        ln = lines[i]
        h1 = re.match(r"^# (.+)$", ln)
        h2 = re.match(r"^## (.+)$", ln)
        if h1:
            sec_title = h1.group(1).strip()
            sec_slug = f"{guide}/{slugify(sec_title)}"
            j = i + 1
            while j < len(lines) and not re.match(r"^#{1,2} ", lines[j]):
                j += 1
            order += 1
            pages.append(Page(guide, sec_slug, sec_title, None, order, 1, _body(lines[i + 1:j]), audience, section=sec_title))
            i = j
            continue
        if h2:
            title = h2.group(1).strip()
            end = heads(2, i)
            block = lines[i + 1:end]
            slug = f"{sec_slug}/{slugify(title)}"
            screens = SCREENS_N.get((guide, norm(title)), [])
            order += 1
            body = "\n".join(block)
            if len(body) > SPLIT_CHARS and any(l.startswith("### ") for l in block):
                k = next(n for n, l in enumerate(block) if l.startswith("### "))
                pages.append(Page(guide, slug, title, sec_slug, order, 2, _body(block[:k]), audience, screens,
                                  _perms_for(guide, sec_title, title, screens), sec_title))
                n = k
                while n < len(block):
                    t3 = block[n][4:].strip()
                    m = n + 1
                    while m < len(block) and not block[m].startswith("### "):
                        m += 1
                    s3 = SCREENS_N.get((guide, norm(t3)), [])
                    order += 1
                    pages.append(Page(guide, f"{slug}/{slugify(t3)}", t3, slug, order, 3, _body(block[n + 1:m]), audience, s3,
                                      _perms_for(guide, sec_title, t3, s3) or _perms_for(guide, sec_title, title, screens), sec_title))
                    n = m
            else:
                # ### başlıklarının ekran anahtarları da bu sayfaya bağlanır (ör. "Sol menü" › "Menüyü daraltma")
                for l in block:
                    if l.startswith("### "):
                        screens = screens + SCREENS_N.get((guide, norm(l[4:])), [])
                pages.append(Page(guide, slug, title, sec_slug, order, 2, _body(block), audience, screens,
                                  _perms_for(guide, sec_title, title, screens), sec_title))
            i = end
            continue
        i += 1
    # Bölüm izinleri: altındaki her sayfa bir izin istiyorsa bölüm sayfası da (ör. RECSlip bölümü)
    for p in pages:
        if p.level == 1:
            p.perms = sorted(set(EXTRA_N.get((guide, norm(p.title)), [])))
    for p in pages:
        if p.level > 1 and not p.perms:
            p.perms = sorted(set(EXTRA_N.get((guide, norm(p.section)), [])))
    return pages


def load_all() -> Tuple[List[Page], str]:
    pages: List[Page] = []
    h = hashlib.sha256()
    for guide, _title, audience in GUIDES:
        f = CONTENT / f"{guide}.md"
        if not f.exists():
            continue
        t = f.read_text(encoding="utf-8")
        h.update(t.encode())
        pages += parse(guide, t, audience)
    # Görsel adları ve içerik özetleri: aynı adla yenilenen görsel de sayfaları yeniden kurdurur (?v= değişir)
    h.update(",".join(sorted(f"{p.name}:{img_version(p.name)}" for p in IMG.glob("*.webp"))).encode() if IMG.exists() else b"")
    return pages, h.hexdigest()[:16]


async def sync(db: AsyncSession, force: bool = False) -> int:
    """Dosyalar değiştiyse yardım sayfalarını yeniden kurar. Döner: sayfa sayısı (değişmediyse 0)."""
    pages, digest = load_all()
    row = await db.get(SystemSetting, HASH_KEY)
    if row and row.value == digest and not force:
        return 0
    await db.execute(delete(HelpPage))
    for p in pages:
        db.add(HelpPage(slug=p.slug, guide=p.guide, title=p.title, parent_slug=p.parent, sort=p.order, level=p.level,
                        section=p.section, body=p.body, audience=p.audience, screen_keys=p.screens, permissions=p.perms))
    if row:
        row.value = digest
    else:
        db.add(SystemSetting(key=HASH_KEY, value=digest))
    await db.commit()
    return len(pages)


# ---------------------------------------------------------------- yetki
def can_see(user: CurrentUser, page: HelpPage) -> bool:
    if user.is_super_admin:
        return True
    if page.audience != "CUSTOMER":
        return False
    perms = page.permissions or []
    return not perms or any(user.has(p) for p in perms)


async def visible(db: AsyncSession, user: CurrentUser) -> List[HelpPage]:
    rows = (await db.execute(select(HelpPage).order_by(HelpPage.sort))).scalars().all()
    return [p for p in rows if can_see(user, p)]


def guide_title(guide: str) -> str:
    return next((t for g, t, _ in GUIDES if g == guide), guide)


def page_out(p: HelpPage, body: bool = False) -> Dict:
    out = {"slug": p.slug, "guide": p.guide, "guide_title": guide_title(p.guide), "title": p.title, "parent": p.parent_slug,
           "level": p.level, "section": p.section, "screens": p.screen_keys or []}
    if body:
        out["body"] = p.body
    return out


async def context(db: AsyncSession, user: CurrentUser, screen: str, title: Optional[str] = None) -> Optional[Dict]:
    """F1: ekran anahtarına (ve açık pencerenin başlığına) en uygun, kullanıcının görebildiği sayfa + sayfa içi başlık."""
    pages = await visible(db, user)
    screen = (screen or "").strip()
    cands = [p for p in pages if screen and screen in (p.screen_keys or [])]
    if not cands and "/" in screen:  # ör. company/AUTOMATIONS yoksa company/ (genel düzen)
        root = screen.rsplit("/", 1)[0] + "/"
        cands = [p for p in pages if root in (p.screen_keys or [])]
    if not cands:
        return None
    page = cands[0]
    anchor = None
    if title:
        want = norm(title)
        for p in [page] + [x for x in pages if x.parent_slug == page.slug]:
            for ln in (p.body or "").splitlines():
                m = re.match(r"^#{3,4} (.+)$", ln)
                if m and want and (want in norm(m.group(1)) or norm(m.group(1)) in want):
                    return {"page": page_out(p), "anchor": slugify(m.group(1))}
    return {"page": page_out(page), "anchor": anchor}


async def search(db: AsyncSession, user: CurrentUser, q: str, limit: int = 8, include_hidden: bool = False) -> List[Tuple[HelpPage, float, str]]:
    """Türkçe tam metin araması (başlık ağırlıklı). include_hidden: yetki kontrolü çağıranda (RECAi asistanı)."""
    q = (q or "").strip()[:300]
    if not q:
        return []
    def sql(query_fn: str):
        return text(f"""
        SELECT id, ts_rank(search, query) * CASE WHEN level = 1 THEN 0.5 ELSE 1 END AS rank,
               ts_headline('turkish', body, query, 'MaxFragments=2, MaxWords=28, MinWords=10, StartSel=**, StopSel=**') AS snip
        FROM help_pages, {query_fn} query
        WHERE search @@ query ORDER BY rank DESC LIMIT 40""")
    rows = list((await db.execute(sql("websearch_to_tsquery('turkish', :q)"), {"q": q})).all())
    # Kök öneki (VEYA): her kelimenin ilk harfleri; çekimli soruların ("nasıl oluştururum") sayfayı bulması için
    words = [w.lower() for w in re.findall(r"\w+", q) if len(w) > 3 and w.lower() not in STOP][:10]
    if words:
        pref = " | ".join(f"{re.sub(r'[^0-9a-zçğıöşü]', '', w[:max(4, len(w) - 3)])}:*" for w in words)
        seen = {r[0] for r in rows}
        for r in (await db.execute(sql("to_tsquery('simple', :q)"), {"q": pref})).all():
            if r[0] not in seen:
                rows.append((r[0], r[1] * 0.6, r[2]))  # tam eşleşmeler önde
        rows.sort(key=lambda r: -r[1])
    by_id = {p.id: p for p in (await db.execute(select(HelpPage).where(HelpPage.id.in_([r[0] for r in rows] or [0])))).scalars()}
    out = []
    for rid, rank, snip in rows:
        p = by_id.get(rid)
        if p and (include_hidden or can_see(user, p)):
            out.append((p, float(rank), snip or ""))
    return out[:limit] if not include_hidden else out
