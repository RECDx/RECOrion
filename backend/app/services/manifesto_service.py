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
