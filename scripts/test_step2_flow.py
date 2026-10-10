import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://localhost:8000/api/v1"

def post_json(path, data):
    url = f"{BASE_URL}{path}"
    print(f"\n--- POST Gönderiliyor: {url} ---")
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "RECOrion-Step2-Test"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        return e.code, json.loads(err_body) if err_body else {}

def get_json(path):
    url = f"{BASE_URL}{path}"
    print(f"\n--- GET Sorgulanıyor: {url} ---")
    req = urllib.request.Request(url, headers={"User-Agent": "RECOrion-Step2-Test"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read().decode("utf-8")
        return resp.status, json.loads(body)

def main():
    print("============================================================")
    print("RECOrion Adım 2 Doğrulama Testi (Satın Alma, Manifesto, E-posta)")
    print("============================================================")

    # 1. Başarılı Satın Alma / Kiralama Başvurusu
    lead_payload = {
        "plan_code": "PRO",
        "company_name": "Nova Bilişim ve Siber Güvenlik Ltd. Şti.",
        "tax_id": "4567891230",
        "address": "ODTÜ Teknokent Bilişim İnovasyon Merkezi, Çankaya / Ankara",
        "phone": "+90 312 444 00 11",
        "website": "https://novabilisim.com.tr",
        "contact_name": "Zeynep Kaya",
        "contact_email": "zeynep.kaya@novabilisim.com.tr",
        "password": "NovaSecurePassword2026!",
        "nace_codes": ["621000", "622000"]
    }

    status, res = post_json("/tenants/purchase-request", lead_payload)
    print(f"HTTP Status: {status}")
    assert status == 200, f"Beklenen 200, gelen: {status}"
    
    lead_id = res.get("lead_id")
    print(f"Oluşturulan Lead ID: {lead_id}")
    assert lead_id is not None
    assert res.get("plan_code") == "PRO"
    assert res.get("company_name") == lead_payload["company_name"]
    assert res.get("admin_notified") is True, "Admin (info@recdx.com) bildirim maili gönderilemedi!"
    assert res.get("customer_notified") is True, "Müşteri onay maili gönderilemedi!"
    
    print("\n[BILDIRIM DURUMU]")
    print(f"  info@recdx.com Yonetici Bildirimi: {'[OK] ILETILDI' if res.get('admin_notified') else '[FAIL] HATA'}")
    print(f"  {lead_payload['contact_email']} Karsilama E-postasi: {'[OK] ILETILDI' if res.get('customer_notified') else '[FAIL] HATA'}")

    # Manifesto ve Sektorel Yetenek Kontrolleri
    manifesto = res.get("generated_manifesto", "")
    print(f"\n[AI MANIFESTO OZETI ({len(manifesto)} karakter)]")
    # ASCII guvenli yazdirma
    print(manifesto[:280].encode('ascii', errors='replace').decode('ascii') + "...\n")
    assert "KURUMSAL YAPAY ZEKA VE" in manifesto or "MANIFESTOSU" in manifesto
    assert "621000" in manifesto or "622000" in manifesto
    
    skills = res.get("assigned_skills", [])
    print(f"Atanan Sektorel Beceriler: {len(skills)} adet")
    assert len(skills) > 0

    # 2. Admin Leads Listesi Doğrulama
    status, leads = get_json("/tenants/leads")
    assert status == 200
    print(f"Sistemdeki Toplam Lead Başvuru Sayısı: {len(leads)}")
    matching_lead = next((l for l in leads if str(l["id"]) == str(lead_id)), None)
    assert matching_lead is not None, "Yeni lead tenant_leads listesinde bulunamadı!"
    print(f"Veritabanı Doğrulaması: Lead ID={matching_lead['id']} Durum={matching_lead['status']}")

    # 3. Hata Yönetimi: Geçersiz Paket Kodu
    invalid_payload = dict(lead_payload)
    invalid_payload["plan_code"] = "NON_EXISTENT_PLAN"
    err_status, err_res = post_json("/tenants/purchase-request", invalid_payload)
    print(f"\nGeçersiz Paket Testi HTTP: {err_status} (Beklenen: 404)")
    assert err_status == 404

    print("\n============================================================")
    print("TÜM ADIM 2 DOĞRULAMA TESTLERİ BAŞARIYLA GEÇTİ! 100% OK")
    print("============================================================")

if __name__ == "__main__":
    main()
