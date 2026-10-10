"""
RECOrion Backend API End-to-End Test Suite
Tests FastAPI endpoints:
- Health (PostgreSQL, Qdrant, Redis)
- EVREN Models catalog (13 models)
- Tenants & AI Actors catalog
- Projects & Tasks & Persistent Chat Messages (Gemini Web-like chat persistence)
- 2-Tier Memory (NS_GLOBAL & NS_AGENT)
"""
import sys
import json
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api/v1"

def api_call(method: str, path: str, data: dict = None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content)
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        return e.code, {"error": error_body}
    except Exception as e:
        return 500, {"exception": str(e)}

def run_tests():
    print("=" * 60)
    print("🚀 RECOrion Backend API Doğrulama Testi Başlatılıyor...")
    print("=" * 60)

    # 1. Health check
    print("\n[1/7] Sağlık Kontrolü (/health)...")
    status, res = api_call("GET", "/health")
    print(f"Status: {status} | Yanıt: {json.dumps(res, ensure_ascii=False)}")
    assert status == 200, f"Health check failed: {res}"
    assert res.get("services", {}).get("postgres") == "healthy"
    assert res.get("services", {}).get("qdrant") == "healthy"
    assert res.get("services", {}).get("redis") == "healthy"
    print("  -> PostgreSQL, Qdrant ve Redis BAĞLANTILARI AKTİF VE SAĞLIKLI!")

    # 2. EVREN Models Catalog
    print("\n[2/7] EVREN Model Kataloğu (/models/)...")
    status, models = api_call("GET", "/models/")
    print(f"Status: {status} | Model Sayısı: {len(models)}")
    assert status == 200
    model_codes = [m["model_code"] for m in models]
    print(f"  -> Bulunan Modeller: {', '.join(model_codes[:5])} ... (+{len(model_codes)-5} model)")
    assert len(model_codes) >= 13, f"En az 13 EVREN modeli bulunmalıydı, gelen: {len(model_codes)}"

    # 3. Tenants
    print("\n[3/7] Şirket / Tenant Sorgusu (/tenants/)...")
    status, tenants = api_call("GET", "/tenants/")
    print(f"Status: {status} | Şirket Sayısı: {len(tenants)}")
    assert status == 200 and len(tenants) > 0
    tenant = tenants[0]
    tenant_id = tenant["id"]
    print(f"  -> Aktif Demo Şirket: {tenant['name']} (ID: {tenant_id})")

    # 4. AI Personelleri (Actors)
    print("\n[4/7] AI Personel Aktörleri (/actors/)...")
    status, actors = api_call("GET", f"/actors/?tenant_id={tenant_id}")
    print(f"Status: {status} | Personel Sayısı: {len(actors)}")
    assert status == 200 and len(actors) >= 4
    for a in actors:
        print(f"  - [{a['actor_type']}] {a['display_name']} ({a['role']}) - Otonomi: {a['autonomy_level']}")
    
    # Pick an AI agent and a human
    ai_actors = [a for a in actors if a["actor_type"] == "AI_AGENT"]
    ai_actor = ai_actors[0] if ai_actors else actors[0]

    # 5. Projeler & Görevler (/projects/)
    print("\n[5/7] Proje ve İş Akışı Görevi Oluşturma (/projects/)...")
    status, projects = api_call("GET", f"/projects/?tenant_id={tenant_id}")
    if not projects:
        status, project = api_call("POST", "/projects/", {
            "tenant_id": tenant_id,
            "slug": "akilli-uretim-vaka",
            "name": "Akıllı Üretim & ERP Entegrasyon Projesi",
            "description": "RECOrion AI personelleri ile ilk vaka projesi",
            "field_package": "YAZILIM"
        })
        assert status == 200, f"Project creation failed: {project}"
        project_id = project["id"]
    else:
        project_id = projects[0]["id"]
    print(f"  -> Proje ID: {project_id}")

    # Create a task for Work Area chat
    status, task = api_call("POST", f"/projects/{project_id}/tasks", {
        "title": "Veri Tabanı Şeması ve Kolektif Hafıza Entegrasyonu",
        "description": "PostgreSQL ve Qdrant üzerinde şirket hafızasını bağlayın",
        "acceptance_criteria": "Tüm servisler sağlıklı yanıt vermeli",
        "priority": "HIGH",
        "assignee_actor_id": ai_actor["id"],
        "estimated_effort": 2.5
    })
    task_id = task["id"]
    print(f"  -> Görev Oluşturuldu: {task['title']} (ID: {task_id}, Atanan Ajan: {ai_actor['display_name']})")

    # 6. Persistent Chat Messages (Gemini Web-like chat)
    print("\n[6/7] Gemini Web-Tarzı Kalıcı Sohbet Testi (/chat/send)...")
    chat_payload = {
        "task_id": task_id,
        "content": "Merhaba ekip, bu görevde şirket ve personel hafızasını kullanarak mimari planı oluşturun.",
        "override_model_code": "glm-5.3"
    }
    status, chat_res = api_call("POST", "/chat/send", chat_payload)
    print(f"Status: {status}")
    assert status == 200, f"Chat send failed: {chat_res}"

    user_msg = chat_res["user_message"]
    ai_msg = chat_res["assistant_message"]
    print(f"  -> Kullanıcı Mesajı Kaydedildi: [{user_msg['role']}]: {user_msg['content']}")
    print(f"  -> AI Ajan Cevabı: [{ai_msg['role']}]: {ai_msg['content']}")
    if ai_msg.get("thought_process"):
        print(f"  -> AI Düşünce Akışı (Thoughts): {ai_msg['thought_process']}")

    # Verify history persistence
    print("\n  -> Kalıcı Geçmiş Kontrolü (/chat/history/{task_id})...")
    status, history = api_call("GET", f"/chat/history/{task_id}")
    print(f"  -> Veritabanında Saklanan Mesaj Sayısı: {len(history)}")
    assert len(history) >= 2, "Kalıcı sohbet geçmişi veritabanında saklanmış olmalı!"
    for m in history:
        print(f"     • [{m['role']} - {m['created_at']}]: {m['content'][:60]}...")

    # 7. 2-Tier Memory (NS_GLOBAL & NS_AGENT)
    print("\n[7/7] 2 Kademeli Kolektif Hafıza Testi (/memory)...")
    # Add agent memory
    mem_payload = {
        "tenant_id": tenant_id,
        "scope": "AGENT",
        "agent_id": ai_actor["id"],
        "content": "Asenkron mimaride PostgreSQL + pgvector ve Qdrant kolektif hafıza yapısı standartlaştırılmıştır.",
        "source_reference": "DOC-REF-001",
        "metadata": {"category": "MİMARİ", "project_id": project_id}
    }
    status, mem_res = api_call("POST", "/memory/add", mem_payload)
    print(f"  -> AI Personel Hafızası Eklendi: Status {status}, ID: {mem_res.get('id')}")
    assert status == 200

    # Search in memory (2-tier search)
    status, search_res = api_call("POST", "/memory/search", {
        "tenant_id": tenant_id,
        "query": "kolektif hafıza ve mimari",
        "assigned_agent_id": ai_actor["id"],
        "limit": 3
    })
    results = search_res.get("results", [])
    print(f"  -> Kolektif Hafıza Semantik Arama Sonucu: {len(results)} kayıt bulundu!")
    for r in results:
        print(f"     • Skor: {r['score']:.4f} | Kapsam: {r['scope']} | İçerik: {r['content'][:60]}...")

    # Promote to Corporate Memory (NS_GLOBAL) test
    mem_id = mem_res.get('id')
    status, promote_res = api_call("POST", f"/memory/promote/{mem_id}")
    print(f"  -> Kurumsal Hafızaya (NS_GLOBAL) Terfi Testi: Status {status} | {promote_res.get('message')}")
    assert status == 200

    print("\n" + "=" * 60)
    print("✅ TÜM ADIM 5 BACKEND UÇLARI VE VERİTABANI İŞLEMLERİ %100 BAŞARILI!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
