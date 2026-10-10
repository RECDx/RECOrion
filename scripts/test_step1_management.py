import json
import urllib.request
import urllib.parse
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(url_path):
    url = f"{BASE_URL}{url_path}"
    print(f"\n--- Test Ediliyor: {url} ---")
    req = urllib.request.Request(url, headers={"User-Agent": "RECOrion-Test"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            data = json.loads(body)
            print(f"Status: {status} OK")
            return status, data
    except Exception as e:
        print(f"HATA: {e}")
        return None, None

def main():
    print("============================================================")
    print("RECOrion Adım 1 Doğrulama Testi (Yönetim, Paketler, Ünvanlar & NACE)")
    print("============================================================")

    # 1. Plans Test
    status, plans = test_endpoint("/tenants/plans")
    assert status == 200, f"Plans status {status} != 200"
    assert len(plans) == 3, f"Beklenen 3 plan, bulunan: {len(plans)}"
    print(f"Bulunan Paket Sayısı: {len(plans)}")
    for p in plans:
        print(f"  [{p['code']}] {p['name']} - Fiyat: {p['monthly_price']} {p['currency']} | Kredi: {p['monthly_credits']} | Max AI: {p['max_agents']} | Model Sayısı: {len(p['allowed_models'])}")
        assert "allowed_models" in p and len(p["allowed_models"]) > 0
        assert "features" in p

    # 2. Job Titles Test
    status, titles = test_endpoint("/actors/job-titles")
    assert status == 200, f"Job Titles status {status} != 200"
    assert len(titles) == 40, f"Beklenen 40 kurumsal ünvan, bulunan: {len(titles)}"
    print(f"Bulunan Kurumsal Ünvan Sayısı: {len(titles)}")
    categories = set(t["category"] for t in titles)
    print(f"Kategoriler: {categories}")
    sample_title = titles[0]
    print(f"Örnek Ünvan: [{sample_title['code']}] {sample_title['title']} ({sample_title['category']}) - Model: {sample_title['recommended_model_code']}")
    print(f"Prompt Özeti: {sample_title['base_role_prompt'][:100]}...")

    # Kategori Filtre Testi
    status, sw_titles = test_endpoint("/actors/job-titles?category=YAZILIM")
    assert status == 200
    print(f"YAZILIM Kategorisindeki Ünvan Sayısı: {len(sw_titles)}")
    assert all(t["category"] == "YAZILIM" for t in sw_titles)

    # 3. NACE Kataloğu Testi
    status, nace_sample = test_endpoint("/tenants/nace-catalog?limit=5")
    assert status == 200
    assert len(nace_sample) == 5
    print("Örnek NACE Kodları:")
    for n in nace_sample:
        print(f"  [{n['code']}] - {n['title'][:70]}...")

    # NACE Arama Testi: 'yazılım'
    query_url = f"/tenants/nace-catalog?query={urllib.parse.quote('yazılım')}&limit=10"
    status, nace_search = test_endpoint(query_url)
    assert status == 200
    print(f"'yazılım' arama sonuç sayısı: {len(nace_search)}")
    assert len(nace_search) > 0
    for n in nace_search[:3]:
        print(f"  -> {n['code']}: {n['title']}")

    # NACE Arama Testi: Kod ile '62.01'
    status, nace_code = test_endpoint("/tenants/nace-catalog?query=62.01")
    assert status == 200
    print(f"'62.01' arama sonuç sayısı: {len(nace_code)}")
    assert any("62.01" in n["code"] for n in nace_code)
    for n in nace_code:
        print(f"  -> {n['code']}: {n['title']}")

    print("\n============================================================")
    print("TÜM ADIM 1 DOĞRULAMA TESTLERİ BAŞARIYLA GEÇTİ! 100% OK")
    print("============================================================")

if __name__ == "__main__":
    main()
