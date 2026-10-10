import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("recorion_manifesto")

class ManifestoService:
    """
    Şirketin seçtiği NACE Rev.2 faaliyet kodları ve kurumsal profili üzerinden
    Yapay Zeka Operasyon, Güvenlik ve İş Manifestosu üreten servis.
    """

    @classmethod
    def generate_manifesto(
        cls,
        company_name: str,
        nace_items: List[Dict[str, str]],
        website: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        NACE kodları ve şirket bilgilerini harmanlayarak kurumsal AI manifestosu ve 
        önerilen yetenek havuzunu (assigned_skills) üretir.
        """
        nace_titles = [item.get("title", "") for item in nace_items if item.get("title")]
        nace_codes = [item.get("code", "") for item in nace_items if item.get("code")]
        
        # Sektörel anahtar kelimeleri çıkar
        combined_text = " ".join(nace_titles).upper()
        
        skills = set()
        skills.add("Kurumsal İletişim")
        skills.add("Görev Yönetimi")
        
        sector_focus = "Genel Ticaret ve Kurumsal Hizmetler"
        regulatory_clauses = [
            "KVKK ve 6698 Sayılı Kişisel Verilerin Korunması Kanunu tam uyumu",
            "Müşteri ve şirket sırrı niteliğindeki verilerin Dark DB sınırları dışına çıkarılmaması",
            "İnsan Denetimli (Human-in-the-Loop) nihai onay mekanizması"
        ]

        if any(w in combined_text for w in ["YAZILIM", "BİLGİSAYAR", "PROGRAMLAMA", "BİLİŞİM", "VERİ"]):
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

        if any(w in combined_text for w in ["SAĞLIK", "TIBBİ", "ECZA", "HASTANE"]):
            sector_focus = "Sağlık ve Biyoteknoloji"
            skills.update(["Tıbbi Dokümantasyon", "Klinik Veri Güvenliği", "Etik Kurul Standartları"])
            regulatory_clauses.append("Hasta mahremiyeti ve özel nitelikli kişisel sağlık verilerinin mutlak izolasyonu")

        if any(w in combined_text for w in ["İMALAT", "ÜRETİM", "SANAYİ", "FABRİKA", "OTOMOTİV"]):
            sector_focus = "Endüstriyel Üretim ve İmalat Sanayii"
            skills.update(["Tedarik Zinciri Optimizasyonu", "Kalite Kontrol Standartları", "ERP Entegrasyonu", "Verimlilik Analizi"])
            regulatory_clauses.append("İş sağlığı ve güvenliği standartları ile sıfır hata toleransı")

        manifesto_text = f"""# {company_name.upper()} - KURUMSAL YAPAY ZEKA VE İŞ OPERASYONU MANİFESTOSU

## 1. MİSYON VE SEKTÖREL ODAK
{company_name}, RECOrion Otonom Yapay Zeka Ekosistemi bünyesinde faaliyet göstermektedir.
Şirketin ana sektörel odağı: **{sector_focus}**
Faaliyet Alanı NACE Referansları: {', '.join(nace_codes) if nace_codes else 'Genel Kurumsal'}

## 2. TEMEL YAPAY ZEKA ETİK VE OPERASYON İLKELERİ
- **Deterministik Karar Alma:** Şirket bünyesindeki tüm AI personelleri (Ajanlar), tanımlı iş akışlarına ve durum makinelerine bağlı kalarak çalışır; halüsinasyondan arındırılmış veri üretir.
- **Kolektif Kurum Hafızası:** Üretilen her doküman, mimari karar ve analiz, {company_name} şirketinin güvenli Dark DB ve Qdrant vektör hafızasında kurumsal değer olarak birikir.
- **Rol ve Yetki Sınırları:** Her AI ajan personeli, kendisine atanan kurumsal ünvanın ve otonomi seviyesinin (L1/L2/L3) sınırlarını asla aşamaz.

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
