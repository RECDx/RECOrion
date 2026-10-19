import os
import requests
import json
import uuid
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    print("\n" + "=" * 60)
    print(f">> {title}")
    print("=" * 60)

def test_all():
    # -------------------------------------------------------------
    # E. Giriş & Kimlik Doğrulama Testi
    # -------------------------------------------------------------
    print_section("E. RECDx Süper Admin Giriş Testi (auth/login)")
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "cuneyterdil@recdx.com",
        "password": os.getenv("RECORION_TEST_SUPERADMIN_PASSWORD", "")
    })
    print(f"Login Status: {login_resp.status_code}")
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    login_data = login_resp.json()
    print("Giriş Başarılı!")
    print(f"Kullanıcı: {login_data['display_name']} | Rol: {login_data['role']}")
    print(f"Yetkiler: {login_data['permissions']}")

    # -------------------------------------------------------------
    # C. Sistem İzin Kataloğu Testi
    # -------------------------------------------------------------
    print_section("C. Sistem İzin Kataloğu (system/permissions)")
    perms_resp = requests.get(f"{BASE_URL}/system/permissions")
    print(f"Permissions Status: {perms_resp.status_code}")
    assert perms_resp.status_code == 200
    perms = perms_resp.json()
    print(f"Toplam Tanımlı İzin Sayısı: {len(perms)}")
    modules = set(p['module'] for p in perms)
    print(f"İzin Modülleri: {list(modules)}")
    for p in perms[:5]:
        print(f"  - [{p['module']}] {p['code']}: {p['name']}")

    # -------------------------------------------------------------
    # A. Odoo 19 Entegrasyonu & Paket Satın Alma (A.1 - A.8)
    # -------------------------------------------------------------
    print_section("A. Odoo 19 Satın Alma Başvurusu (tenants/purchase-request)")
    test_tax = f"998877{str(uuid.uuid4())[:4]}"
    req_body = {
        "company_name": "Antigravity Odoo Test A.Ş.",
        "contact_name": "Cüneyt Erdil Test",
        "contact_email": f"test_{str(uuid.uuid4())[:6]}@antigravity-corp.com",
        "phone": "+90 532 555 44 33",
        "website": "https://antigravity-corp.com",
        "address": "Maslak Mah. Büyükdere Cad. No:123 Sarıyer / İstanbul",
        "tax_id": "1234567890",
        "plan_code": "ENTERPRISE",
        "password": "CustomerSecure_2026!",
        "nace_codes": ["62.01.01", "70.22.02"]
    }
    
    pur_resp = requests.post(f"{BASE_URL}/tenants/purchase-request", json=req_body)
    print(f"Purchase Status: {pur_resp.status_code}")
    assert pur_resp.status_code == 200, f"Purchase failed: {pur_resp.text}"
    pur_data = pur_resp.json()
    lead_id = pur_data["lead_id"]
    print(f"Lead ID: {lead_id}")
    print(f"Odoo Sipariş Referansı: {pur_data['odoo_order_name']}")
    print(f"Durum: {pur_data['status']}")
    assert pur_data["odoo_order_name"] is not None, "Odoo order name should be populated!"

    # -------------------------------------------------------------
    # A.9 RECDx Yetkilisinin Ödemeyi Doğrulayıp Onaylaması
    # -------------------------------------------------------------
    print_section("A.9. Satış ve Üyelik Onayı (leads/{lead_id}/approve)")
    app_resp = requests.post(f"{BASE_URL}/tenants/leads/{lead_id}/approve")
    print(f"Approve Status: {app_resp.status_code}")
    assert app_resp.status_code == 200, f"Approve failed: {app_resp.text}"
    app_data = app_resp.json()
    new_tenant_id = app_data["tenant_id"]
    print(f"Tenant ID: {new_tenant_id}")
    print(f"Tenant Slug: {app_data['tenant_slug']}")
    print(f"Admin E-posta: {app_data['admin_email']}")
    print(f"Aktivasyon E-postası İletildi mi: {app_data.get('activation_email_sent')}")
    assert app_data.get("activation_email_sent") is True, "Aktivasyon e-postası başarıyla gönderilmiş olmalı!"
    print(f"Mesaj: {app_data['message']}")

    # -------------------------------------------------------------
    # B. AI Personel Ünvanı Tanımlama Yetkisi Kontrolü
    # -------------------------------------------------------------
    print_section("B. AI Personel Ünvanı Tanımlama Yetkisi")
    # Kurumsal Müşteri (new_tenant_id) için özel ünvan oluşturma (Başarılı Olmalı)
    title_payload = {
        "tenant_id": new_tenant_id,
        "code": "AI_STRATEGY_DIRECTOR",
        "title": "Stratejik İnovasyon ve Ar-Ge Direktörü AI",
        "category": "STRATEJİ",
        "description": "Kurumsal dönüşüm ve yapay zeka stratejilerini koordine eden üst düzey yönetici AI ajanı.",
        "base_role_prompt": "Sen şirketin Stratejik İnovasyon Direktörüsün. Gelecek vizyonunu ve Ar-Ge yol haritasını yönetirsin.",
        "required_skills": ["stratejik_planlama", "finansal_fizibilite"],
        "recommended_model_code": "glm-5.3",
        "autonomy_level": "L3"
    }
    title_resp = requests.post(f"{BASE_URL}/actors/job-titles", json=title_payload)
    print(f"Kurumsal Müşteri Ünvan Ekleme Status: {title_resp.status_code}")
    assert title_resp.status_code == 200, f"Enterprise title creation failed: {title_resp.text}"
    created_title = title_resp.json()
    print(f"Oluşturulan Özel Ünvan: {created_title['title']} (Kod: {created_title['code']})")

    # Ünvanları Listeleme (Standart + Şirkete Özel)
    list_titles_resp = requests.get(f"{BASE_URL}/actors/job-titles?tenant_id={new_tenant_id}")
    assert list_titles_resp.status_code == 200
    all_titles = list_titles_resp.json()
    custom_titles = [t for t in all_titles if t.get("tenant_id") == new_tenant_id]
    print(f"Toplam Ünvan: {len(all_titles)} | Şirkete Özel Ünvan: {len(custom_titles)}")
    assert len(custom_titles) >= 1

    # Standart Paket (STARTER) abonesi bir tenant için 403 engeli testi:
    # recdx_hq starter değildir ama starter bir tenant id ile deneyelim:
    # Bir starter lead oluşturalım:
    starter_lead_req = {
        "company_name": "Starter KOBİ Ltd.",
        "contact_name": "Ahmet Başlangıç",
        "contact_email": f"starter_{str(uuid.uuid4())[:6]}@starterkobi.com",
        "phone": "+90 532 111 22 33",
        "plan_code": "STARTER",
        "password": "Password123!"
    }
    st_pur_resp = requests.post(f"{BASE_URL}/tenants/purchase-request", json=starter_lead_req)
    st_lead_id = st_pur_resp.json()["lead_id"]
    st_app_resp = requests.post(f"{BASE_URL}/tenants/leads/{st_lead_id}/approve")
    st_tenant_id = st_app_resp.json()["tenant_id"]

    # Şimdi STARTER tenant özel ünvan eklemeye çalışsın:
    forbidden_resp = requests.post(f"{BASE_URL}/actors/job-titles", json={
        "tenant_id": st_tenant_id,
        "code": "FORBIDDEN_TITLE",
        "title": "İzinsiz Ünvan",
        "base_role_prompt": "Test prompt"
    })
    print(f"Starter Paket Ünvan Ekleme Status (Beklenen 403): {forbidden_resp.status_code}")
    assert forbidden_resp.status_code == 403, f"Expected 403 for STARTER plan, got {forbidden_resp.status_code}"
    print(f"403 Engelleme Mesajı: {forbidden_resp.json()['detail']}")

    # -------------------------------------------------------------
    # D. Müşteri Yetkilisinin Özel Rol Tanımlaması (İzin Kataloğu ile)
    # -------------------------------------------------------------
    print_section("D. Şirket İçi Özel Rol Tanımlama (tenants/{id}/roles)")
    role_payload = {
        "name": "Kıdemli Proje ve AI Operasyon Lideri",
        "description": "Projeleri yöneten, ajanları görevlendiren ve hafızayı sorgulayan yetkili rolü.",
        "permissions": [
            "agent:hire",
            "agent:configure",
            "project:create",
            "task:create",
            "task:approve",
            "chat:participate",
            "chat:view_a2a",
            "memory:search"
        ]
    }
    role_resp = requests.post(f"{BASE_URL}/tenants/{new_tenant_id}/roles", json=role_payload)
    print(f"Role Create Status: {role_resp.status_code}")
    assert role_resp.status_code == 200, f"Role creation failed: {role_resp.text}"
    created_role = role_resp.json()
    print(f"Oluşturulan Rol: {created_role['name']} (ID: {created_role['id']})")
    print(f"Atanan Yetkiler: {created_role['permissions']}")

    # Rolleri listele
    roles_list_resp = requests.get(f"{BASE_URL}/tenants/{new_tenant_id}/roles")
    assert roles_list_resp.status_code == 200
    roles = roles_list_resp.json()
    print(f"Şirketin Toplam Rol Sayısı: {len(roles)}")

    print("\n" + "=" * 60)
    print("SUCCESS: TUM MADDELER (A, B, C, D, E) EKSIKSIZ VE BASARIYLA DOGRULANDI!")
    print("=" * 60)

if __name__ == "__main__":
    test_all()
