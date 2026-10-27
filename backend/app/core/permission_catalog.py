"""
İzin kataloğu ve sistem rolleri (tek kaynak).

Müşteri tarafının menü ve işlemlerine göre gruplanır. Veritabanındaki `system_permissions` ve sistem rolleri
(`tenant_roles.tenant_id IS NULL`) 0041 göçüyle bu tabloya eşitlenir; test paketi ikisinin aynı kaldığını doğrular.
Süper Admin "İzin Kataloğu" ve "Yetki Rolleri" ekranından ad/açıklama/rol dağılımı sonradan düzenlenebilir;
yeni izin kodunun bir anlamı olması için kodda denetlenmesi gerekir (ENFORCED dışındaki kodlar uyarıyla gösterilir).
"""

# Modül kodu -> ekranda görünen ad (müşteri menüsüyle aynı sıra)
MODULES = {
    "PLATFORM": "Şirket & Platform",
    "REPORTS": "Genel Bakış & Raporlar",
    "RBAC": "Kullanıcılar & Roller",
    "AGENTS": "AI Personel",
    "ORG": "Organizasyon",
    "INTELLIGENCE": "Kurum Zekâsı",
    "INTEGRATIONS": "Entegrasyon & Otomasyon",
    "BILLING": "Kredi & Kullanım",
    "PROJECTS": "Projeler & İş Akışı",
    "CHAT": "Sohbet & İletişim",
    "MEMORY": "Kurum Hafızası",
    "CONNECTIONS": "Bağlantılarım",
}

# (kod, modül, ad, açıklama)
PERMISSIONS = [
    ("system:admin", "PLATFORM", "Tam Sistem Yönetimi", "Yalnızca RECDx süper yöneticileri. Müşteri şirketlere verilemez."),
    ("tenant:view", "PLATFORM", "Şirket Bilgilerini Görüntüleme",
     "Şirket, departman, ünvan, kullanıcı ve AI personel listelerini görme. Her kullanıcıda bulunur."),
    ("tenant:manage", "PLATFORM", "Şirket Ayarlarını Yönetme",
     "RECDx uygulama tercihleri ve genel şirket ayarları. Şirket yöneticisinin temel izni."),

    ("dashboard:view", "REPORTS", "Şirket Geneli Pano", "Şirket Yönetimi > Genel Bakış: tüm şirketin proje, adım, kredi ve AI personel göstergeleri."),
    ("department:dashboard", "REPORTS", "Departman Panosu", "Yalnızca kendi departmanının panosunu görme (Work Space > Pano)."),
    ("cost:view", "REPORTS", "Maliyet ve Bütçe Bilgilerini Görme",
     "Panolardaki parasal göstergeler: token maliyeti, maliyet dağılımı, tahmini tasarruf, bütçe ve gerçekleşen."),

    ("user:invite", "RBAC", "Kullanıcı Ekleme", "Kullanıcı Yönetimi'nde yeni kullanıcı tanımlama (şifre belirleme e-postası gider)."),
    ("user:manage", "RBAC", "Kullanıcı Düzenleme ve Silme",
     "Kullanıcının departman, ünvan, rol, ek izin ve durumunu değiştirme, silme; kişi günlük maliyetini görme."),
    ("role:create", "RBAC", "Şirkete Özel Rol Tanımlama", "Şirkete özel yetki rolü oluşturma."),
    ("role:edit", "RBAC", "Rol Düzenleme", "Şirkete özel rollerin izinlerini değiştirme."),
    ("role:delete", "RBAC", "Rol Silme", "Şirkete özel rolleri silme."),

    ("agent:hire", "AGENTS", "AI Personel İşe Alma", "AI Personel İşe Al sihirbazı ve RECAi ile ünvan araştırması."),
    ("agent:configure", "AGENTS", "AI Personel Ayarları ve Bilgi Kaynakları",
     "AI personelin bilgilerini, rol promptunu düzenleme; bilgi dokümanı, web ve video kaynağı ekleme, onaylama."),
    ("agent:quarantine", "AGENTS", "AI Personeli İşten Çıkarma", "AI personeli işten çıkarma, yeniden işe alma ve silme."),
    ("agent:custom_title", "AGENTS", "Ünvan Tanımlama", "Şirket ünvanlarını ve rol promptlarını oluşturma, düzenleme, silme."),

    ("org:manage", "ORG", "Departman Yönetimi", "Departman oluşturma, katalogdan ekleme, düzenleme ve silme."),

    ("manifesto:manage", "INTELLIGENCE", "Sektörel Manifesto Yönetimi", "Sektörler, NACE kodları ve kurumsal manifestoyu düzenleme, RECAi'ye yazdırma."),
    ("brain:manage", "INTELLIGENCE", "Beyin AI Ayarları", "Planlamada kullanılacak RECAi kademesini seçme."),
    ("regulation:manage", "INTELLIGENCE", "Mevzuat Paketlerini Açma/Kapatma", "Şirkete mevzuat bilgi paketlerini açma ve kapatma."),

    ("integration:manage", "INTEGRATIONS", "Bağlantı Yönetimi",
     "Dış sistem bağlantısı ekleme, deneme, AI personele araç yetkisi verme, aktarım kurallarını belirleme."),
    ("mapping:manage", "INTEGRATIONS", "Eşleme Stüdyosu", "Ortak kayıtların dış sistem alanlarına eşlemesini hazırlama, deneme ve onaylama."),
    ("automation:manage", "INTEGRATIONS", "Otomasyon Kuralları", "Otomasyon kuralı ve hazır kural kurma, sınama, durdurma, çalışma günlüğü."),
    ("integration:approve", "INTEGRATIONS", "Dış Sisteme Yazma Onayı",
     "Aktarım ve araç çağrısı onayı (ikinci onay dahil), aktarım günlüğü, başarısız aktarımı yeniden deneme."),

    ("billing:view", "BILLING", "Kredi ve Kullanımı Görme", "Kredi ve Kullanım ekranı: aylık hak, kullanılan, ek kredi bakiyesi, kullanım dökümü."),
    ("billing:topup", "BILLING", "Ek Kredi ve Paket Talebi", "RECDx'ten ek kredi veya paket değişikliği talep etme."),

    ("project:create", "PROJECTS", "Proje / Case Açma", "Yeni proje veya Case; şablondan ve toplantıdan proje oluşturma."),
    ("project:manage", "PROJECTS", "Tüm Projeleri Yönetme",
     "Şirketin bütün projelerini görme ve yönetme (yönetici olmadığı projeler dahil): planlama, ekip, başlatma, kapanış."),
    ("template:manage", "PROJECTS", "Şirket Şablonlarını Yönetme", "Projeyi şablon olarak kaydetme ve başkasının şirket şablonunu düzenleme."),
    ("task:create", "PROJECTS", "İş Adımı Ekleme", "Erişebildiği projelere yeni iş akışı görevi ekleme."),
    ("task:approve", "PROJECTS", "İş Adımı Onaylama (Vekâleten)", "Erişebildiği projelerde, onaylayıcısı olmasa da onay bekleyen adımı onaylama."),
    ("task:reject", "PROJECTS", "Revizyon İsteme (Vekâleten)", "Erişebildiği projelerde, onaylayıcısı olmasa da adım için revizyon isteme."),

    ("chat:participate", "CHAT", "Sohbet ve Görev İletişimi", "Görev sohbetine ve Beyin AI sohbetine yazma, dosya ekleme."),
    ("chat:view_a2a", "CHAT", "Ajanlar Arası Konuşmaları İzleme", "AI personelin kendi aralarındaki konuşmaları görme."),
    ("chat:export", "CHAT", "Sohbeti Dışa Aktarma", "Sohbet ve düşünce akışını dışa aktarma."),

    ("memory:search", "MEMORY", "Kurum Hafızasında Arama", "Onaylı kurum hafızasında arama."),
    ("memory:promote", "MEMORY", "Kurum Hafızasına Ekleme ve Onaylama", "Onaylanan çıktı ve proje bilgisini kurum hafızasına aktarma, bekleyenleri onaylama veya reddetme."),
    ("memory:revoke", "MEMORY", "Kurum Hafızasından Geri Alma", "Onaylanmış kurum hafızası bilgisini geri alma."),

    ("token:manage", "CONNECTIONS", "Kişisel Erişim Anahtarı", "Bağlantılarım: Claude, Cursor gibi MCP istemcileri için kişisel erişim anahtarı oluşturma."),
]
CODES = [p[0] for p in PERMISSIONS]
PLATFORM_ONLY = {"*", "system:admin"}
CUSTOMER_CODES = [c for c in CODES if c not in PLATFORM_ONLY]

# Kodda denetlenmeyen izinler (ekranda "henüz bir işleme bağlı değil" uyarısıyla gösterilir)
NOT_ENFORCED = {"role:edit", "role:delete", "billing:topup", "chat:export", "chat:view_a2a"}

STANDARD = ["tenant:view", "task:create", "chat:participate", "memory:search", "token:manage"]
PROJECT_MANAGER = STANDARD + ["department:dashboard", "agent:hire", "project:create", "project:manage", "template:manage",
                              "task:approve", "task:reject", "chat:view_a2a", "memory:promote", "memory:revoke"]

# Sistem rolleri. base_role: kullanıcıya atanınca actors.role bu kod olur (şirket yöneticisi denetimleri buna bakar).
# platform=True: yalnızca RECDx personeline görünür ve atanabilir.
SYSTEM_ROLES = [
    {"name": "Süper Yönetici (Platform Admin)", "base_role": "SUPER_ADMIN", "platform": True, "permissions": ["*"],
     "description": "RECDx süper yöneticisi. Yalnızca RECDx ana şirketinde kullanılır."},
    {"name": "Şirket Yöneticisi", "base_role": "COMPANY_ADMIN", "permissions": CUSTOMER_CODES,
     "description": "Şirketin tüm yönetim ve çalışma yetkileri. Şirkette en az bir aktif şirket yöneticisi bulunmalıdır."},
    {"name": "Proje Yöneticisi", "base_role": "PROJECT_MANAGER", "permissions": PROJECT_MANAGER,
     "description": "Proje ve Case açar, RECAi ile planlar, ekip kurar, AI personel işe alır, adımları onaylar, kurum hafızasına aktarır."},
    {"name": "Uzman Kullanıcı", "base_role": "USER", "permissions": STANDARD,
     "description": "Ekibinde olduğu projelerde çalışır: atanan adımlar, sohbet, hafızada arama, kişisel erişim anahtarı."},
    {"name": "Personel ve Organizasyon Yöneticisi", "permissions": STANDARD + [
        "department:dashboard", "user:invite", "user:manage", "agent:hire", "agent:configure", "agent:quarantine",
        "agent:custom_title", "org:manage"],
     "description": "İnsan kullanıcıları, AI personeli, departman ve ünvanları yönetir."},
    {"name": "Yapay Zeka ve Ajan Lideri", "permissions": STANDARD + [
        "agent:hire", "agent:configure", "agent:quarantine", "agent:custom_title", "manifesto:manage", "brain:manage",
        "regulation:manage", "project:manage", "chat:view_a2a", "memory:promote", "memory:revoke"],
     "description": "AI personelin işe alımı, eğitimi ve kalitesinden; manifesto, Beyin AI ve mevzuat ayarlarından sorumludur."},
    {"name": "Entegrasyon Yöneticisi", "permissions": STANDARD + [
        "integration:manage", "mapping:manage", "automation:manage", "integration:approve"],
     "description": "Dış sistem bağlantıları, eşlemeler, otomasyon kuralları ve dış sisteme yazma onaylarından sorumludur (BT)."},
    {"name": "Finans ve Raporlama Sorumlusu", "permissions": STANDARD + [
        "dashboard:view", "department:dashboard", "cost:view", "billing:view", "billing:topup", "integration:approve"],
     "description": "Şirket panosu, maliyet ve bütçe, kredi kullanımı; tutar eşiğini aşan aktarımların onayı."},
    {"name": "Kalite ve Onay Sorumlusu", "permissions": STANDARD + [
        "task:approve", "task:reject", "chat:view_a2a", "memory:promote", "memory:revoke"],
     "description": "Erişebildiği projelerde adım çıktılarını onaylar veya revizyon ister; kurum hafızasını denetler."},
    {"name": "Operasyon Yöneticisi", "permissions": STANDARD + [
        "tenant:manage", "dashboard:view", "department:dashboard", "cost:view", "billing:view", "manifesto:manage",
        "regulation:manage", "org:manage", "project:create", "project:manage"],
     "description": "Şirket ayarları, pano, kredi ve operasyonel projelerin genel yönetimi."},
    {"name": "Güvenlik ve Uyum Denetçisi", "permissions": [
        "tenant:view", "memory:search", "dashboard:view", "department:dashboard", "cost:view", "billing:view",
        "chat:view_a2a", "chat:export"],
     "description": "Salt okunur denetim: panolar, maliyet ve kredi, ajanlar arası konuşmalar, sohbet dışa aktarma."},
]

# Eski rol adları (0041 öncesi) -> yeni ad; bu rollere bağlı kullanıcılar korunur
RENAMED_ROLES = {
    "Standart Kurumsal Kullanıcı": "Uzman Kullanıcı",
    "Yapay Zeka Mimarisi & Ajan Lideri": "Yapay Zeka ve Ajan Lideri",
    "Kurumsal Operasyon & Müşteri Yöneticisi": "Operasyon Yöneticisi",
    "Güvenlik & Uyum Denetçisi (SecOps & Compliance)": "Güvenlik ve Uyum Denetçisi",
}

ROLE_BASE_PERMISSIONS = {r["base_role"]: set(r["permissions"]) for r in SYSTEM_ROLES if r.get("base_role") not in (None, "SUPER_ADMIN", "USER")}
DEFAULT_PERMISSIONS = set(STANDARD)

# Şirket Yönetimi konsolunu açan izinler (biri yeterli); menüler ayrıca izne göre süzülür
CONSOLE_PERMISSIONS = {
    "tenant:manage", "dashboard:view", "user:invite", "user:manage", "agent:hire", "agent:configure", "agent:quarantine",
    "agent:custom_title", "org:manage", "manifesto:manage", "brain:manage", "regulation:manage", "integration:manage",
    "mapping:manage", "automation:manage", "integration:approve", "billing:view",
}

BASE_ROLE_LABELS = {"SUPER_ADMIN": "Süper Yönetici", "COMPANY_ADMIN": "Şirket Yöneticisi", "PROJECT_MANAGER": "Proje Yöneticisi",
                    "USER": "Uzman Kullanıcı", "MEMBER": "Uzman Kullanıcı"}


def role_label(role: str) -> str:
    return BASE_ROLE_LABELS.get(role or "", role or "")


def default_for_roles(code: str) -> list:
    """Bir izni varsayılan olarak içeren sistem rollerinin adları (İzin Kataloğu ekranında gösterilir)."""
    return [r["name"] for r in SYSTEM_ROLES if code in r["permissions"] or r["permissions"] == ["*"]]
