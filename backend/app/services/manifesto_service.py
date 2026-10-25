import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("recorion_manifesto")

class ManifestoService:
    """
    Şirketin seçtiği Sektör ve Meslek Tanımları üzerinden
    Yapay Zeka Operasyon, Güvenlik ve İş Manifestosu üreten servis (Madde 1).
    """

    @classmethod
    def generate_manifesto(
        cls,
        company_name: str,
        sectors: Optional[List[str]] = None,
        professions: Optional[List[str]] = None,
        nace_items: Optional[List[Dict[str, str]]] = None,
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sektör ve Meslek Tanımları ile şirket bilgilerini harmanlayarak kurumsal AI manifestosu ve 
        önerilen yetenek havuzunu (assigned_skills) üretir.
        """
        all_desc_terms = []
        if sectors:
            all_desc_terms.extend([str(s) for s in sectors if s])
        if professions:
            all_desc_terms.extend([str(p) for p in professions if p])
        if nace_items:
            for item in nace_items:
                if isinstance(item, dict):
                    t = item.get("title") or item.get("name") or item.get("code")
                    if t:
                        all_desc_terms.append(t)
                elif isinstance(item, str):
                    all_desc_terms.append(item)

        combined_text = " ".join(all_desc_terms).upper()

        skills = set()
        skills.add("Kurumsal İletişim")
        skills.add("Görev Yönetimi")

        sector_focus = "Genel Ticaret ve Kurumsal Hizmetler"
        regulatory_clauses = [
            "KVKK ve 6698 Sayılı Kişisel Verilerin Korunması Kanunu tam uyumu",
            "Müşteri ve şirket sırrı niteliğindeki verilerin Dark DB sınırları dışına çıkarılmaması",
            "İnsan Denetimli (Human-in-the-Loop) nihai onay mekanizması"
        ]

        if any(w in combined_text for w in ["YAZILIM", "BİLGİSAYAR", "PROGRAMLAMA", "BİLİŞİM", "VERİ", "ELEKTRONİK"]):
            sector_focus = "Bilişim Teknolojileri, Yazılım ve Dijital Çözümler"
            skills.update(["Yazılım Mimarisi", "Temiz Kod & Test Otomasyonu", "Siber Güvenlik", "API Tasarımı", "CI/CD & DevOps"])
            regulatory_clauses.append("Açık kaynak lisans uyumluluğu ve statik kod güvenlik analizi (SAST)")

        if any(w in combined_text for w in ["FİNANS", "BANKA", "SİGORTA", "MUHASEBE", "MALİ", "DANIŞMANLIK"]):
            sector_focus = "Finans, Denetim ve Stratejik Danışmanlık"
            skills.update(["Mali Analiz", "Bütçe ve Nakit Akışı Modelleme", "Vergi Mevzuatı Denetimi", "Kurumsal Risk Yönetimi"])
            regulatory_clauses.append("Mali denetim standartları, şeffaf defter tutma ve hesap verebilirlik ilkesi")

        if any(w in combined_text for w in ["HUKUK", "DAVA", "MEVZUAT", "PATENT", "TELİF"]):
            sector_focus = "Hukuki Uyum ve Mevzuat Yönetimi"
            skills.update(["Sözleşme İnceleme", "Mevzuat Taraması", "KVKK/GDPR Uyumluluk", "Hukuki Risk Analizi"])
            regulatory_clauses.append("Avukatlık sırrı ve müvekkil mahremiyeti prensiplerinin mutlak korunması")

        if any(w in combined_text for w in ["SAĞLIK", "TIBBİ", "ECZA", "HASTANE", "KOZMETİK"]):
            sector_focus = "Sağlık, Kozmetik ve Biyoteknoloji"
            skills.update(["Tıbbi Dokümantasyon", "Klinik Veri Güvenliği", "Etik Kurul Standartları"])
            regulatory_clauses.append("Hasta mahremiyeti ve özel nitelikli kişisel sağlık verilerinin mutlak izolasyonu")

        if any(w in combined_text for w in ["İMALAT", "ÜRETİM", "SANAYİ", "FABRİKA", "OTOMOTİV", "METAL", "MAKİNE", "KERESTE", "AĞAÇ"]):
            sector_focus = "Endüstriyel Üretim, Metal ve İmalat Sanayii"
            skills.update(["Tedarik Zinciri Optimizasyonu", "Kalite Kontrol Standartları", "ERP Entegrasyonu", "Verimlilik Analizi"])
            regulatory_clauses.append("İş sağlığı ve güvenliği standartları ile sıfır hata toleransı")

        if any(w in combined_text for w in ["ULAŞTIRMA", "LOJİSTİK", "NAKLİYE", "KARGO", "TAŞIMA"]):
            sector_focus = "Lojistik, Taşımacılık ve Ulaştırma Hizmetleri"
            skills.update(["Filo & Rota Optimizasyonu", "Depo Yönetimi", "Gümrük & Mevzuat Denetimi"])
            regulatory_clauses.append("Uluslararası taşımacılık ve yük güvenliği standartlarına tam uyum")

        manifesto_text = f"""# {company_name.upper()} - KURUMSAL YAPAY ZEKA VE İŞ OPERASYONU MANİFESTOSU

## 1. MİSYON VE SEKTÖREL ODAK
{company_name}, RECOrion Otonom Yapay Zeka Ekosistemi bünyesinde faaliyet göstermektedir.
Şirketin ana sektörel odağı: **{sector_focus}**
Faaliyet Sektör ve Meslek Referansları: {', '.join(all_desc_terms) if all_desc_terms else 'Genel Kurumsal Faaliyet'}

## 2. TEMEL YAPAY ZEKA ETİK VE OPERASYON İLKELERİ
- **Deterministik Karar Alma:** Şirket bünyesindeki tüm AI personelleri (Ajanlar), tanımlı iş akışlarına ve durum makinelerine bağlı kalarak çalışır; halüsinasyondan arındırılmış veri üretir.
- **Kolektif Kurum Hafızası:** Üretilen her doküman, mimari karar ve analiz, {company_name} şirketinin güvenli Dark DB ve Qdrant vektör hafızasında kurumsal değer olarak birikir.
- **Rol ve Yetki Sınırları:** Her AI ajan personeli, kendisine atanan kurumsal rolün ve otonomi seviyesinin (L1/L2/L3) sınırlarını asla aşamaz.

## 3. REGÜLASYON VE VERİ GÜVENLİĞİ TAAHHÜTLERİ
{chr(10).join([f'- {c}' for c in regulatory_clauses])}

## 4. HEDEF ÇIKTI VE MÜKEMMELLİK STANDARDI
Bu manifesto, {company_name} şirketinin tüm dijital personelleri için bağlayıcı üst anayasa niteliğindedir. Tüm görev teslimleri 'Doğrulanmış Çıktı' ve 'Kalite Kapısı' ilkelerine tabidir.
"""
        return {
            "manifesto": manifesto_text.strip(),
            "sector_focus": sector_focus,
            "assigned_skills": sorted(list(skills))
        }


# ---------------------------------------------------------------------------
# Detaylı, LLM ile üretilen manifesto (Odoo #228)
# ---------------------------------------------------------------------------
MANIFESTO_SECTIONS = """1. Kimliğimiz ve Misyonumuz (şirketin ne yaptığı, kime değer ürettiği)
2. Vizyonumuz (3-5 yıllık hedef tablo)
3. Temel Değerlerimiz (her değer için davranışa dökülmüş 2-3 somut ilke)
4. Faaliyet Alanımıza Özgü İş İlkeleri (seçili sektör ve meslek gruplarının gerçek iş süreçleri, riskleri ve iyi uygulamaları)
5. Müşteri ve Paydaş Taahhütlerimiz (hizmet kalitesi, iletişim, şikâyet yönetimi)
6. Kalite, Mevzuat ve Uyum (sektörün tabi olduğu Türk mevzuatı, KVKK, iş güvenliği, sektörel standartlar ve belgeler)
7. AI Personellerimizin Çalışma İlkeleri (insan onayı, gizlilik, doğruluk, emin olmadığında sorma, kurum hafızasını kullanma)
8. Karar Alma, Onay ve Eskalasyon (hangi kararları AI'ın, hangilerini insan yöneticinin verdiği)
9. Kurumsal İletişim Dili ve Üslubumuz (müşteriye ve ekibe hitap şekli, kaçınılacak ifadeler)
10. Ölçülebilir Hedeflerimiz (her biri sayısal ölçütlü 4-6 hedef)"""


async def describe_activity(db, sector_codes, profession_codes) -> str:
    """Sektör ve meslek kodlarını Ticaret Bakanlığı tanım adlarına çevirir."""
    from sqlalchemy import select
    from app.db.models import Profession, Sector

    lines = []
    if sector_codes:
        rows = (await db.execute(select(Sector).where(Sector.code.in_([str(c) for c in sector_codes])))).scalars().all()
        lines += [f"Sektör {s.code}: {s.name}" for s in rows] or [str(c) for c in sector_codes]
    if profession_codes:
        rows = (await db.execute(select(Profession).where(Profession.code.in_([str(c) for c in profession_codes])))).scalars().all()
        lines += [f"Meslek grubu {p.code}: {p.name}" for p in rows] or [str(c) for c in profession_codes]
    return "\n".join(lines) or "Belirtilmedi (genel ticari faaliyet)"


async def generate_detailed_manifesto(db, *, tenant_id, company_name: str, sector_codes=None, profession_codes=None,
                                      website: str = None, instructions: str = None, current: str = None,
                                      departments=None, titles=None, model_code: str = None) -> dict:
    """
    LLM Gateway ile şirkete özgü, 10 bölümlü detaylı manifesto üretir. Hata durumunda şablona
    düşülmez (önceden sessizce genel şablon dönüyor ve kullanıcı bunu AI çıktısı sanıyordu).
    """
    from app.services import llm_gateway
    from app.services.llm_gateway import LLMContext

    activity = await describe_activity(db, sector_codes, profession_codes)
    org = ""
    if departments:
        org += "Departmanlar: " + ", ".join(departments[:30]) + "\n"
    if titles:
        org += "Tanımlı ünvanlar: " + ", ".join(titles[:40]) + "\n"
    prompt = f"""'{company_name}' için kurumsal manifesto yaz{' (mevcut metni geliştirerek)' if current else ''}.

ŞİRKET BİLGİLERİ
Ünvan: {company_name}
Web sitesi: {website or 'belirtilmedi'}
Faaliyet alanı (T.C. Ticaret Bakanlığı sınıflandırması):
{activity}
{org}
{('Yöneticinin özel talimatı: ' + instructions) if instructions else ''}
{('MEVCUT MANİFESTO (koru, geliştir, tutarsızlıkları düzelt):' + chr(10) + current[:6000]) if current else ''}

BÖLÜMLER (her bölüm başlıklı ve dolu olmalı):
{MANIFESTO_SECTIONS}

KURALLAR
- Genel geçer slogan yerine bu faaliyet alanına özgü, somut ve uygulanabilir ifadeler kullan.
- Bu metin şirketin AI personellerinin sistem talimatlarına eklenecek; açık, yönlendirici ve tutarlı yaz.
- Doğrulanamayan rakam, ödül, müşteri adı veya sertifika uydurma; mevzuat adlarını genel düzeyde an.
- Markdown kullan (## başlıklar, madde işaretleri). Giriş/kapanış cümlesi ekleme. Türkçe yaz."""
    result = await llm_gateway.chat(
        LLMContext(tenant_id=tenant_id, purpose="MANIFESTO"),
        [
            {"role": "system", "content": "Sen Türk iş dünyasını, sektör mevzuatını ve kurumsal kültür tasarımını iyi bilen kıdemli bir strateji danışmanısın."},
            {"role": "user", "content": prompt},
        ],
        model_code=model_code, temperature=0.6, max_tokens=8192, timeout=180,
    )
    return {"manifesto": result.content.strip(), "model_code": result.public_model, "credits": result.credits}
