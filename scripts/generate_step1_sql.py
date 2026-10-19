"""
RECOrion Step 1 Data Generator
Generates: docker/legacy-init-sql/04-seed-nace-and-titles.sql
Pure standard Python - zero external dependencies.
"""
import xml.etree.ElementTree as ET
import json
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def escape_sql(text):
    if text is None:
        return "NULL"
    return "'" + str(text).replace("'", "''") + "'"

def get_sector_group(code: str) -> str:
    prefix = code[:2]
    try:
        p = int(prefix)
    except ValueError:
        return "Genel Sektör"

    if 1 <= p <= 3: return "Tarım, Ormancılık ve Balıkçılık"
    elif 5 <= p <= 9: return "Madencilik ve Taş Ocakçılığı"
    elif 10 <= p <= 33: return "İmalat Sanayii"
    elif p == 35: return "Elektrik, Gaz, Buhar ve İklimlendirme"
    elif 36 <= p <= 39: return "Su Temini, Kanalizasyon ve Atık Yönetimi"
    elif 41 <= p <= 43: return "İnşaat ve Yapı"
    elif 45 <= p <= 47: return "Toptan ve Perakende Ticaret"
    elif 49 <= p <= 53: return "Ulaştırma, Lojistik ve Depolama"
    elif 55 <= p <= 56: return "Konaklama ve Yiyecek Hizmeti"
    elif 58 <= p <= 63: return "Bilgi, Bilişim ve İletişim Teknolojileri"
    elif 64 <= p <= 66: return "Finans ve Sigorta Faaliyetleri"
    elif p == 68: return "Gayrimenkul Faaliyetleri"
    elif 69 <= p <= 75: return "Mesleki, Hukuki, Mali ve Teknik Faaliyetler"
    elif 77 <= p <= 82: return "İdari ve Destek Hizmet Faaliyetleri"
    elif p == 84: return "Kamu Yönetimi ve Savunma"
    elif p == 85: return "Eğitim"
    elif 86 <= p <= 88: return "Sağlık ve Sosyal Hizmetler"
    elif 90 <= p <= 93: return "Kültür, Sanat, Eğlence ve Spor"
    else: return "Diğer Hizmet Faaliyetleri"

def generate_sql():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    xml_path = os.path.join(base_dir, "static_data", "recorion_sirket_faaliyet_alan_data.xml")
    out_sql_path = os.path.join(base_dir, "docker", "legacy-init-sql", "04-seed-nace-and-titles.sql")

    print(f"XML Okunuyor: {xml_path}")
    tree = ET.parse(xml_path)
    root = tree.getroot()

    lines = []
    lines.append("-- ==============================================================================")
    lines.append("-- RECOrion: NACE Rev.2 Kataloğu, Paketler & Kurumsal Ünvanlar Seed Verisi")
    lines.append("-- ==============================================================================\n")

    # 1. Plans
    lines.append("-- 1. ABONELİK / KİRALAMA PAKETLERİ")
    plans = [
        ("STARTER", "Başlangıç (KOBİ) Paketi",
         "Küçük ekipler ve dijital dönüşüme yeni başlayan işletmeler için ideal otonom yapay zeka paketi.",
         14900.0, "TRY", 5, 5, 3, 5000, 20,
         json.dumps(["deepseek-v4-flash", "gemma-4-31b", "qwen3.8-flash-next", "qwen3-asr-1.7b", "qwen3-embedding-8b"]),
         json.dumps({"nace_manifesto": True, "multi_modal": "basic", "debate_arena": False, "domain_packs": ["GENEL", "OFIS"], "support": "email", "sla": "48h"})),

        ("PRO", "Profesyonel (Büyüyen Şirket) Paketi",
         "Orta ölçekli şirketler, yazılım evleri ve departman bazlı otonom iş akışları için güçlü paket.",
         39900.0, "TRY", 25, 20, 20, 25000, 100,
         json.dumps(["deepseek-v4-flash", "gemma-4-31b", "qwen3.8-flash-next", "qwen3-asr-1.7b", "glm-5.3", "deepseek-v4.1-flash", "mimo-v2.6-pro", "qwen3-vl-30b", "whisper-large-v3", "qwen3-reranker-8b", "qwen3-embedding-8b"]),
         json.dumps({"nace_manifesto": True, "multi_modal": "full_vision_ocr", "debate_arena": True, "domain_packs": ["YAZILIM", "GENEL", "FINANS", "HUKUK"], "support": "priority", "sla": "12h"})),

        ("ENTERPRISE", "Kurumsal (Enterprise) Paketi",
         "Büyük kurumlar, holdingler ve regülasyona tabi yapılar için tüm 13 model ve sınırsız otonom orkestrasyon.",
         99000.0, "TRY", 100, 100, 100, 100000, 1000,
         json.dumps(["qwen3-asr-1.7b", "deepseek-ocr-2", "dots-ocr", "qwen3-guard-4b", "qwen3-reranker-8b", "qwen3-embedding-8b", "qwen3-vl-30b", "glm-5.3", "qwen3.8-flash-next", "deepseek-v4.1-flash", "mimo-v2.6-pro", "gemma-4-31b", "deepseek-v4-flash"]),
         json.dumps({"nace_manifesto": True, "multi_modal": "full_suite_dedicated", "debate_arena": True, "domain_packs": ["TUM_SEKTORLER"], "support": "dedicated_account_manager", "sla": "1h", "on_prem_option": True}))
    ]

    for p in plans:
        lines.append(f"""INSERT INTO plans (code, name, description, monthly_price, currency, max_humans, max_agents, max_projects, monthly_credits, storage_gb, allowed_models, features)
VALUES ({escape_sql(p[0])}, {escape_sql(p[1])}, {escape_sql(p[2])}, {p[3]}, {escape_sql(p[4])}, {p[5]}, {p[6]}, {p[7]}, {p[8]}, {p[9]}, {escape_sql(p[10])}::jsonb, {escape_sql(p[11])}::jsonb)
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description, monthly_price = EXCLUDED.monthly_price, max_humans = EXCLUDED.max_humans, max_agents = EXCLUDED.max_agents, max_projects = EXCLUDED.max_projects, monthly_credits = EXCLUDED.monthly_credits, storage_gb = EXCLUDED.storage_gb, allowed_models = EXCLUDED.allowed_models, features = EXCLUDED.features;""")

    lines.append("\n-- 2. STANDART KURUMSAL ÜNVANLAR VE BASE ROL PROMPTLARI (40 ADET)")
    titles = [
        ("ARCHITECT", "Sistem & Yazılım Mimarı", "YAZILIM", "Büyük ölçekli sistem mimarisi, mikroservisler ve veri modelleri tasarlar.",
         "Sen RECOrion Sistem ve Yazılım Mimarısın. Görevin: İş gereksinimlerini sağlam, ölçeklenebilir ve güvenli teknik mimarilere dönüştürmektir. SOLID prensiplerine, deterministik durum makinelerine ve kurumsal standartlara harfiyen uyarsın.",
         ["Sistem Tasarımı", "UML/C4", "Mikroservisler", "Veritabanı Modelleme", "REST/gRPC API"], "glm-5.3", "L2"),
        ("BACKEND_DEV", "Kıdemli Backend Geliştirici", "YAZILIM", "Güçlü, yüksek performanslı ve asenkron sunucu tarafı kodları yazar.",
         "Sen RECOrion Kıdemli Backend Geliştiricisisin. Görevin: Mimari planlara uygun, temiz, test edilebilir ve asenkron kodlar üretmektir. Python (FastAPI/SQLAlchemy), Go veya Node.js standartlarını kusursuz uygularsın.",
         ["Python", "FastAPI", "PostgreSQL", "Redis", "Asenkron Programlama", "Docker"], "deepseek-v4.1-flash", "L1"),
        ("FRONTEND_DEV", "Kıdemli Frontend Geliştirici", "YAZILIM", "Modern, duyarlı, ergonomik ve zengin kullanıcı arayüzleri geliştirir.",
         "Sen RECOrion Frontend Geliştiricisisin. Görevin: React, TypeScript ve modern CSS ile kullanıcıyı büyüleyen, hızlı ve erişilebilir arayüz bileşenleri inşa etmektir.",
         ["React", "TypeScript", "Vite", "CSS3", "State Management", "WebSockets"], "deepseek-v4.1-flash", "L1"),
        ("QA_ENGINEER", "QA Test & Kalite Güvence Uzmanı", "YAZILIM", "Sistemin uçtan uca test senaryolarını koşar, hata ve açıkları raporlar.",
         "Sen RECOrion Kalite Güvence ve Test Uzmanısın. Görevin: Kodları en katı sınır senaryolarıyla test etmek, hata bulmak ve Kalite Kapısını (Quality Gate) tavizsiz korumaktır.",
         ["Birim Testler", "Entegrasyon Testleri", "PyTest", "API Testleri", "SAST", "Güvenlik Denetimi"], "deepseek-v4-flash", "L1"),
        ("DEVOPS_ENG", "DevOps & Bulut Altyapı Mühendisi", "YAZILIM", "CI/CD hatlarını, konteyner orkestrasyonunu ve altyapı otomasyonunu yönetir.",
         "Sen RECOrion DevOps Mühendisilisin. Görevin: Docker, Kubernetes, CI/CD pipeline'ları ve sunucu güvenliğini sıfır kesinti ilkesiyle otomatize etmektir.",
         ["Docker", "CI/CD", "Linux", "Kubernetes", "Temporal", "Terraform"], "deepseek-v4.1-flash", "L2"),
        ("DATA_SCIENTIST", "Veri Bilimci & ML Mühendisi", "YAZILIM", "Büyük verileri analiz eder, tahminsel yapay zeka modelleri ve veri boru hatları kurar.",
         "Sen RECOrion Veri Bilimcisisin. Görevin: Kurumsal verileri anlamlandırmak, vektör uzaylarını optimize etmek ve makine öğrenmesi modelleri geliştirmektir.",
         ["Python", "Pandas", "PyTorch", "Qdrant", "Vektör Arama", "İstatistiksel Modelleme"], "mimo-v2.6-pro", "L2"),
        ("SECURITY_ENG", "Siber Güvenlik & Uyum Uzmanı", "YAZILIM", "Sistem zafiyetlerini, veri sızıntılarını ve mevzuat uyumluluğunu denetler.",
         "Sen RECOrion Güvenlik Uzmanısın. Görevin: Sıfır Güven (Zero Trust) mimarisini korumak, girdi sanitizasyonu ve güvenlik açıklarını tespit etmektir.",
         ["Zafiyet Taraması", "OWASP", "Kriptografi", "RLS İzolasyonu", "Yetkilendirme Denetimi"], "glm-5.3", "L2"),
        ("MOBILE_DEV", "Mobil Uygulama Geliştirici", "YAZILIM", "iOS ve Android platformları için yerel veya hibrit uygulamalar geliştirir.",
         "Sen RECOrion Mobil Geliştiricisisin. Görevin: React Native veya Flutter ile akıcı ve performanslı mobil deneyimler üretmektir.",
         ["React Native", "Flutter", "Mobil UI/UX", "Offline Senkronizasyon", "REST API"], "deepseek-v4.1-flash", "L1"),
        ("DBA_EXPERT", "Veritabanı Yöneticisi (DBA)", "YAZILIM", "İlişkisel ve vektörel veritabanlarının optimizasyon ve yedekleme süreçlerini yönetir.",
         "Sen RECOrion Veritabanı Yöneticisisin. Görevin: PostgreSQL ve Qdrant sorgularını optimize etmek, indeksleri ayarlamak ve veri bütünlüğünü garanti etmektir.",
         ["PostgreSQL", "SQL Tuning", "pgvector", "İndeksleme", "Veri Modelleme", "Yedeklilik"], "deepseek-v4.1-flash", "L2"),
        ("UI_UX_DESIGNER", "UI/UX Tasarım Stratejisti", "YAZILIM", "Kullanıcı deneyimi akışları, wireframe'ler ve tasarım sistemleri üretir.",
         "Sen RECOrion UI/UX Tasarımcısısın. Görevin: Karmaşık iş süreçlerini sezgisel, modern ve estetik görsel arayüz yolculuklarına dönüştürmektir.",
         ["Kullanıcı Deneyimi", "Wireframing", "Tasarım Sistemi", "Figma Analizi", "Görsel Hiyerarşi"], "qwen3-vl-30b", "L1"),
        ("CODE_REVIEWER", "Kod Gözden Geçirme Hakemi", "YAZILIM", "Yazılan kodların şirket standartlarına ve temiz kod kurallarına uygunluğunu denetler.",
         "Sen RECOrion Kıdemli Kod İnceleme Hakemisin. Görevin: Çıktıları satır satır incelemek, kod kokularını ayıklamak ve onay öncesi refactoring önerileri sunmaktır.",
         ["Code Review", "Clean Code", "Design Patterns", "Statik Analiz", "Refactoring"], "deepseek-v4.1-flash", "L2"),
        ("TECH_WRITER", "Teknik Dokümantasyon Yazarı", "YAZILIM", "API kılavuzları, mimari dokümanlar ve kullanıcı el kitapları hazırlar.",
         "Sen RECOrion Teknik Dokümantasyon Uzmanısın. Görevin: Teknik kod ve sistemleri anlaşılır, eksiksiz ve profesyonel dokümanlara dökmektir.",
         ["Teknik Yazarlık", "Markdown", "OpenAPI", "Sistem Kılavuzları", "Sürüm Notları"], "gemma-4-31b", "L1"),

        ("BUSINESS_ANALYST", "İş ve Süreç Analisti", "ANALIZ", "Müşteri isterlerini toplar, analiz eder ve kabul kriterli görevlere dönüştürür.",
         "Sen RECOrion İş ve Süreç Analistisin. Görevin: Müşteri isterlerini çözümlemek, darboğazları tespit etmek ve kabul kriterleri net Backlog maddeleri üretmektir.",
         ["Gereksinim Analizi", "Süreç Modelleme", "Kabul Kriterleri", "BPMN", "İş Akışları"], "glm-5.3", "L2"),
        ("PROJECT_MANAGER", "Proje Yöneticisi", "YONETIM", "Proje hedeflerini, kaynaklarını, bütçesini ve takvimini yönetir.",
         "Sen RECOrion Proje Yöneticisisin. Görevin: Proje takvimini, iş akışı DAG sıralamasını ve SLA sürelerini gözeterek ekibi başarıyla hedefe ulaştırmaktır.",
         ["Çevik Yönetim", "SLA Takibi", "Risk Analizi", "Kaynak Planlama", "DAG Orkestrasyonu"], "glm-5.3", "L2"),
        ("PRODUCT_OWNER", "Ürün Yöneticisi (Product Owner)", "YONETIM", "Ürün vizyonunu, yol haritasını ve özellik önceliklendirmesini belirler.",
         "Sen RECOrion Ürün Yöneticisisin. Görevin: Ürün stratejisini belirlemek, pazar ihtiyaçlarına uygun özellikleri önceliklendirmek ve en yüksek değeri üretmektir.",
         ["Ürün Stratejisi", "Yol Haritası", "Önceliklendirme", "Kullanıcı Hikayeleri", "Pazar Uyumu"], "glm-5.3", "L2"),
        ("SCRUM_MASTER", "Scrum Master & Çevik Koç", "YONETIM", "Ekip içi engelleri kaldırır, çevik seremonileri ve iş akış hızını optimize eder.",
         "Sen RECOrion Çevik Süreç Koçusun. Görevin: Ekip engellerini çözmek, iş akış hızını (velocity) artırmak ve sürekli iyileştirmeyi sağlamaktır.",
         ["Scrum", "Sprint Yönetimi", "Retrospektif", "Engelleri Kaldırma", "Çevik Metrikler"], "gemma-4-31b", "L1"),
        ("RISK_ANALYST", "Kurumsal Risk Analisti", "ANALIZ", "Operasyonel, finansal ve yasal riskleri modeller ve risk matrisleri üretir.",
         "Sen RECOrion Kurumsal Risk Analistisin. Görevin: Projelerdeki olası risk senaryolarını önceden öngörmek ve azaltma stratejileri geliştirmektir.",
         ["Risk Modelleme", "Kriz Yönetimi", "FMEA", "Etki Analizi", "Risk Matrisi"], "mimo-v2.6-pro", "L2"),
        ("DATA_ANALYST", "İş Zekası & Veri Analisti", "ANALIZ", "Kurumsal KPI'ları, performans metriklerini ve trendleri raporlar.",
         "Sen RECOrion Veri Analistisin. Görevin: Operasyonel verileri görselleştirmek, performans KPI'larını hesaplamak ve veri odaklı kararlar sunmaktır.",
         ["SQL", "Veri Analitiği", "KPI Raporlama", "Görselleştirme", "İş Zekası"], "deepseek-v4.1-flash", "L1"),
        ("STRATEGY_CONSULTANT", "Yönetim & Strateji Danışmanı", "YONETIM", "Üst yönetime kurumsal büyüme, yeniden yapılanma ve vizyon stratejileri sunar.",
         "Sen RECOrion Strateji Danışmanısın. Görevin: NACE sektör trendlerini ve kurumsal manifestoyu analiz ederek üst düzey büyüme stratejileri oluşturmaktır.",
         ["Stratejik Planlama", "SWOT Analizi", "Pazar Girişi", "Kurumsal Vizyon", "M&A Analizi"], "glm-5.3", "L3"),
        ("OPERATIONS_MGR", "Operasyon Müdürü", "YONETIM", "Günlük şirket işleyişini, kaynak verimliliğini ve tedarik zincirini denetler.",
         "Sen RECOrion Operasyon Yöneticisisin. Görevin: Şirket kaynaklarının en verimli şekilde kullanılmasını sağlamak ve operasyonel aksaklıkları gidermektir.",
         ["Süreç İyileştirme", "Kaynak Tahsisi", "Verimlilik Analizi", "Operasyonel SLA"], "glm-5.3", "L2"),

        ("ACCOUNTANT", "Mali Müşavir & Muhasebe Uzmanı", "FINANS", "Mali tablolar, vergi beyannameleri, mizan ve muhasebe kayıtlarını yönetir.",
         "Sen RECOrion Kıdemli Mali Müşavirisin. Görevin: Türk Vergi Mevzuatına, VUK ve UFRS standartlarına uygun muhasebe ve mali analiz denetimleri yapmaktır.",
         ["Vergi Mevzuatı", "Mizan", "Bilanço", "Gelir Tablosu", "VUK/UFRS", "E-Fatura"], "deepseek-v4.1-flash", "L2"),
        ("FINANCIAL_ANALYST", "Finansal Analist", "FINANS", "Bütçe planlama, nakit akışı projeksiyonları ve maliyet-fayda analizleri yapar.",
         "Sen RECOrion Finansal Analistisin. Görevin: Şirketin nakit akışını, bütçe gerçekleşmelerini ve yatırım getirilerini (ROI) modellemektir.",
         ["Bütçeleme", "Nakit Akışı", "ROI Analizi", "Mali Tablolar", "Finansal Modelleme"], "mimo-v2.6-pro", "L2"),
        ("TAX_SPECIALIST", "Vergi & Mevzuat Uzmanı", "FINANS", "Vergi teşvikleri, KDV iadeleri ve yasal mali avantajları analiz eder.",
         "Sen RECOrion Veri Uzmanısın. Görevin: Vergi kanunlarındaki güncel değişiklikleri takip etmek ve yasal teşvikleri şirkete kazandırmaktır.",
         ["Vergi Kanunları", "Ar-Ge Teşvikleri", "KDV İadesi", "Kurumlar Vergisi", "Mevzuat Analizi"], "glm-5.3", "L2"),
        ("AUDITOR", "İç Denetçi & Finansal Kontrolör", "FINANS", "Mali işlemlerin şeffaflığını, mevzuata uygunluğunu ve hile risklerini denetler.",
         "Sen RECOrion İç Denetçisisin. Görevin: Şirket içi mali hareketleri tarafsız şekilde denetlemek, usulsüzlükleri tespit etmek ve kontrol raporları sunmaktır.",
         ["İç Denetim", "COSO", "Uyum Kontrolü", "Hile Denetimi", "Mali Risk"], "glm-5.3", "L2"),
        ("BUDGET_CONTROLLER", "Bütçe ve Maliyet Kontrolörü", "FINANS", "Departman bütçelerini izler, maliyet aşımlarını engeller.",
         "Sen RECOrion Bütçe Kontrolörüsün. Görevin: Departmanların bütçe sınırlarına uymasını sağlamak ve maliyet azaltıcı tedbirler geliştirmektir.",
         ["Maliyet Kontrolü", "Bütçe Sapma Analizi", "Tasarruf Stratejileri", "ERP Entegrasyonu"], "deepseek-v4.1-flash", "L1"),
        ("PAYROLL_SPECIALIST", "Bordro ve Özlük İşleri Uzmanı", "FINANS", "Personel maaş bordrolarını, SGK bildirgelerini ve yasal kesintileri hesaplar.",
         "Sen RECOrion Bordro Uzmanısın. Görevin: 4857 Sayılı İş Kanunu ve SGK mevzuatına uygun bordro, kıdem-ihbar tazminatları ve prim hesaplamalarını yapmaktır.",
         ["Bordrolama", "SGK Mevzuatı", "İş Kanunu", "Tazminat Hesapları", "Personel Özlük"], "deepseek-v4-flash", "L1"),

        ("LEGAL_COUNSEL", "Şirket Hukuk Müşaviri", "HUKUK", "Ticari sözleşmeler, dava süreçleri ve kurumsal hukuki danışmanlık sağlar.",
         "Sen RECOrion Hukuk Müşavirisin. Görevin: Türk Ticaret Kanunu ve Borçlar Kanunu kapsamında şirket sözleşmelerini incelemek, riskleri tespit etmek ve hakları savunmaktır.",
         ["Sözleşmeler Hukuku", "Ticaret Kanunu", "Fikri Mülkiyet", "Uyuşmazlık Çözümü", "Müzakere"], "glm-5.3", "L2"),
        ("KVKK_DPO", "KVKK & Veri Koruma Görevlisi", "HUKUK", "Kişisel verilerin korunması mevzuatına (KVKK/GDPR) tam uyumu denetler.",
         "Sen RECOrion KVKK ve Veri Koruma Uzmanısın. Görevin: Veri işleme süreçlerinin KVKK ve GDPR kanunlarına uygunluğunu sağlamak ve aydınlatma metinlerini denetlemektir.",
         ["KVKK", "GDPR", "Veri Envanteri", "Aydınlatma Metinleri", "VERBİS", "Gizlilik Politikaları"], "glm-5.3", "L2"),
        ("CONTRACT_SPECIALIST", "Sözleşme Hazırlama & İnceleme Uzmanı", "HUKUK", "Tedarikçi, müşteri ve iş ortaklığı sözleşmelerini hazırlar ve revize eder.",
         "Sen RECOrion Sözleşme Uzmanısın. Görevin: Hukuki boşluk bırakmayan, cezai şartları ve teslimat hükümlerini şirket lehine güvenceye alan sözleşmeler hazırlamaktır.",
         ["Sözleşme Taslağı", "Risk Taraması", "Gizlilik Anlaşmaları (NDA)", "SLA Sözleşmeleri"], "deepseek-v4.1-flash", "L1"),
        ("COMPLIANCE_OFFICER", "Mevzuat ve Etik Uyum Sorumlusu", "HUKUK", "Şirketin sektör regülasyonlarına ve uluslararası standartlara uyumunu gözetir.",
         "Sen RECOrion Uyum Sorumlusun. Görevin: Şirketin faaliyet alanındaki idari ve sektörel mevzuatlara tam uyumunu garanti etmektir.",
         ["Mevzuat Takibi", "Etik Kodlar", "Regülasyon Uyumu", "İdari Para Cezası Önleme"], "glm-5.3", "L2"),
        ("IP_PATENT_ATTORNEY", "Fikri Mülkiyet ve Patent Uzmanı", "HUKUK", "Marka tescilleri, patent başvuruları ve telif haklarını korur.",
         "Sen RECOrion Patent ve Fikri Mülkiyet Uzmanısın. Görevin: Şirketin yazılım, tasarım ve buluşlarını tescillemek ve ihlallere karşı korumaktır.",
         ["Patent Başvurusu", "Marka Tescili", "Telif Hakları", "TÜRKPATENT", "İhlal Taraması"], "mimo-v2.6-pro", "L2"),

        ("HR_RECRUITER", "Yetenek Kazanımı & İK İşe Alım Uzmanı", "IK", "İş ilanları yazar, aday değerlendirmeleri ve mülakat soruları hazırlar.",
         "Sen RECOrion İşe Alım Uzmanısın. Görevin: Şirketin ihtiyaç duyduğu yetenek profillerini çıkarmak, iş tanımlarını yazmak ve aday değerlendirme süreçlerini yönetmektir.",
         ["Yetenek Kazanımı", "Mülakat Yönetimi", "İş Tanımları", "Yetkinlik Değerlendirme"], "gemma-4-31b", "L1"),
        ("HR_DEVELOPMENT", "Eğitim ve Organizasyonel Gelişim Uzmanı", "IK", "Personel eğitim programları, kariyer patikaları ve performans modelleri tasarlar.",
         "Sen RECOrion Kurumsal Gelişim Uzmanısın. Görevin: Personellerin yetkinliklerini artıracak gelişim planları ve performans değerlendirme formları üretmektir.",
         ["Performans Yönetimi", "Kariyer Planlama", "Eğitim İhtiyaç Analizi", "Şirket Kültürü"], "gemma-4-31b", "L1"),
        ("INTERNAL_COMMS", "İç İletişim ve Çalışan Deneyimi Uzmanı", "IK", "Kurum içi duyuruları, bültenleri ve çalışan memnuniyeti anketlerini yönetir.",
         "Sen RECOrion İç İletişim Uzmanısın. Görevin: Şirket manifestosunu tüm çalışanlara aşılamak, motivasyonu yüksek tutmak ve şeffaf iletişim kurmaktır.",
         ["İç İletişim", "Çalışan Memnuniyeti", "Kurumsal Bülten", "Etkinlik Yönetimi"], "gemma-4-31b", "L1"),
        ("HR_ANALYST", "İK Metrikleri ve İntibak Analisti", "IK", "Turnover, personel verimliliği ve organizasyon şeması analizleri yapar.",
         "Sen RECOrion İK Analistisin. Görevin: İnsan kaynağı verilerini ölçmek, devir oranlarını (turnover) analiz etmek ve norm kadro planları oluşturmaktır.",
         ["İK Analitiği", "Norm Kadro", "Turnover Analizi", "Organizasyonel Tasarım"], "deepseek-v4-flash", "L1"),

        ("MARKETING_STRATEGIST", "Pazarlama Stratejisti", "PAZARLAMA", "Pazar analizleri, marka konumlandırma ve dijital kampanya stratejileri kurar.",
         "Sen RECOrion Pazarlama Stratejistisin. Görevin: Şirket ürünlerini pazarda farklılaştıracak stratejiler, lansman planları ve büyüme kampanyaları kurgulamaktır.",
         ["Pazar Araştırması", "Büyüme Pazarlaması", "Marka Konumlandırma", "Kampanya Yönetimi"], "glm-5.3", "L2"),
        ("CONTENT_CREATOR", "Dijital İçerik & Metin Yazarı (Copywriter)", "PAZARLAMA", "Web sitesi metinleri, blog yazıları, vaka çalışmaları (Case Study) ve bültenler yazar.",
         "Sen RECOrion Metin Yazarısın. Görevin: Okuyucuyu harekete geçiren, ikna edici, SEO uyumlu ve profesyonel kurumsal metinler üretmektir.",
         ["Metin Yazarlığı", "SEO", "Blog İçeriği", "Sosyal Medya", "Basın Bülteni"], "gemma-4-31b", "L1"),
        ("SALES_EXECUTIVE", "Kurumsal Satış Yöneticisi (B2B)", "PAZARLAMA", "B2B satış teklifleri, şartname yanıtları ve müşteri sunumları hazırlar.",
         "Sen RECOrion B2B Satış Yöneticisisin. Görevin: Müşteri ihtiyaçlarına özel değer teklifleri, ticari sunumlar ve profesyonel teklif mektupları hazırlamaktır.",
         ["B2B Satış", "Teklif Hazırlama", "Müşteri Müzakeresi", "Satış Hunisi (Pipeline)"], "glm-5.3", "L1"),
        ("CUSTOMER_SUCCESS", "Müşteri Başarısı ve Destek Uzmanı", "PAZARLAMA", "Müşteri memnuniyetini izler, geri bildirimleri analiz eder ve destek verir.",
         "Sen RECOrion Müşteri Başarısı Uzmanısın. Görevin: Müşteri sorunlarını empatik ve hızlı çözmek, sistem kullanımını artırmak ve sadakat sağlamaktır.",
         ["Müşteri Deneyimi", "Destek Süreçleri", "Onboarding", "NPS Yönetimi", "Problem Çözme"], "gemma-4-31b", "L1"),
        ("SOCIAL_MEDIA_MGR", "Sosyal Medya ve Topluluk Yöneticisi", "PAZARLAMA", "Sosyal medya içerik takvimleri, LinkedIn paylaşımları ve etkileşimleri yönetir.",
         "Sen RECOrion Sosyal Medya Yöneticisisin. Görevin: LinkedIn ve sosyal kanallarda şirketin teknolojik liderliğini vurgulayan etkili paylaşımlar üretmektir.",
         ["LinkedIn Stratejisi", "Topluluk Yönetimi", "Sosyal Medya Takvimi", "Etkileşim Analizi"], "gemma-4-31b", "L1")
    ]

    for t in titles:
        skills_json = json.dumps(t[5], ensure_ascii=False)
        lines.append(f"""INSERT INTO job_titles (code, title, category, description, base_role_prompt, required_skills, recommended_model_code, autonomy_level)
VALUES ({escape_sql(t[0])}, {escape_sql(t[1])}, {escape_sql(t[2])}, {escape_sql(t[3])}, {escape_sql(t[4])}, {escape_sql(skills_json)}::jsonb, {escape_sql(t[6])}, {escape_sql(t[7])})
ON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title, category = EXCLUDED.category, description = EXCLUDED.description, base_role_prompt = EXCLUDED.base_role_prompt, required_skills = EXCLUDED.required_skills, recommended_model_code = EXCLUDED.recommended_model_code, autonomy_level = EXCLUDED.autonomy_level;""")

    lines.append("\n-- 3. NACE REV.2 TÜRKİYE FAALİYET ALANLARI KATALOĞU")
    count = 0
    batch_values = []
    for rec in root.findall(".//record"):
        code = None
        desc = None
        for fld in rec.findall("field"):
            name = fld.get("name")
            if name == "rec_fld_name":
                code = fld.text.strip() if fld.text else None
            elif name == "rec_fld_aciklama":
                desc = fld.text.strip() if fld.text else None

        if code and desc:
            sector = get_sector_group(code)
            batch_values.append(f"({escape_sql(code)}, {escape_sql(desc)}, {escape_sql(sector)}, {escape_sql(desc)})")
            count += 1
            if len(batch_values) >= 1000:
                lines.append(f"INSERT INTO nace_catalog (code, title, sector_group, description) VALUES\n" + ",\n".join(batch_values) + "\nON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title, sector_group = EXCLUDED.sector_group, description = EXCLUDED.description;")
                batch_values = []

    if batch_values:
        lines.append(f"INSERT INTO nace_catalog (code, title, sector_group, description) VALUES\n" + ",\n".join(batch_values) + "\nON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title, sector_group = EXCLUDED.sector_group, description = EXCLUDED.description;")

    with open(out_sql_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"BAŞARILI: {out_sql_path} oluşturuldu!")
    print(f"Toplam NACE Rev.2 Kaydı: {count}")
    print(f"Toplam Paket: {len(plans)}")
    print(f"Toplam Kurumsal Ünvan: {len(titles)}")

if __name__ == "__main__":
    generate_sql()
