"""
ADIM 5.5: 4 katmanlı bilgi + proje ekleri. Qdrant, filtreleri gerçekten uygulayan sahte bir depoyla değiştirilir;
böylece katman ve şirket ayrımı (KVKK) uçtan uca doğrulanır.
"""
import json
import uuid

import pytest

from app.core.security import hash_password
from app.services import storage
from app.services.collective_memory import collective_memory
from app.services.evren_client import ChatResult, EmbeddingResult, RerankResult, evren_client

PASSWORD = "Bilgi-Katmani-Testi-2026"
CARD = {"summary": "Özet.", "key_points": ["Bilgi."], "quiz": []}


def _exec(db, sql, *params):
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if cur.description else None


def _matches(flt, payload) -> bool:
    """qdrant Filter (must / should, MatchValue) değerlendirici."""
    if flt is None:
        return True
    for cond in flt.must or []:
        if hasattr(cond, "key"):
            if str(payload.get(cond.key)) != str(cond.match.value):
                return False
        elif not _matches(cond, payload):
            return False
    if flt.should:
        return any(_matches(c, payload) if not hasattr(c, "key") else str(payload.get(c.key)) == str(c.match.value)
                   for c in flt.should)
    return True


class FakeQdrant:
    def __init__(self):
        self.points = {}

    async def upsert(self, collection_name, points):
        for p in points:
            self.points[str(p.id)] = dict(p.payload)

    async def delete(self, collection_name, points_selector):
        for pid in points_selector.points:
            self.points.pop(str(pid), None)

    async def set_payload(self, collection_name, payload, points):
        for pid in points:
            self.points[str(pid)].update(payload)

    async def query_points(self, collection_name, query, query_filter=None, limit=10):
        class P:
            def __init__(self, pid, payload):
                self.id, self.payload, self.score = pid, payload, 0.9

        class R:
            pass
        r = R()
        r.points = [P(k, v) for k, v in self.points.items() if _matches(query_filter, v)][:limit]
        return r


@pytest.fixture
def env(monkeypatch):
    objects, prompts, q = {}, [], FakeQdrant()
    monkeypatch.setattr(storage, "_put", lambda key, data, ct: objects.__setitem__(key, data))
    monkeypatch.setattr(storage, "_get", lambda key: objects[key])
    monkeypatch.setattr(storage, "_delete", lambda key: objects.pop(key, None))

    async def chat(model_code, messages, **kw):
        content = messages[-1]["content"] if isinstance(messages[-1]["content"], str) else ""
        if model_code == "qwen3-guard-4b":
            return ChatResult("Safety: Safe\nCategories: None", None, 10, 5, {})
        if "öğrenme kartı" in content:
            return ChatResult(json.dumps(CARD), None, 100, 50, {})
        if "Diyalogdan Bilgi" in messages[0]["content"]:  # sohbetten öğrenme
            return ChatResult(json.dumps({"learnings": [
                {"fact": "SOHBET-GLOBAL: tüm teklifler 15 gün geçerlidir.", "scope": "GLOBAL", "category": "IS_PROSESI", "confidence": 0.9},
                {"fact": "SOHBET-AGENT: bu personel raporları tablo halinde verir.", "scope": "AGENT", "category": "TERCIH", "confidence": 0.9},
            ]}), None, 100, 50, {})
        prompts.append(messages[0]["content"])
        return ChatResult("Bilgilere göre cevap.", None, 300, 20, {})

    async def embed(text, model_code):
        return EmbeddingResult([0.1] * 8, 10)

    async def rerank(query, documents, model_code, top_n=5):
        return RerankResult([{"index": i, "relevance_score": 1 - i / 100} for i in range(min(top_n, len(documents)))], 10)

    monkeypatch.setattr(evren_client, "chat", chat)
    monkeypatch.setattr(evren_client, "embed", embed)
    monkeypatch.setattr(evren_client, "rerank", rerank)
    monkeypatch.setattr(collective_memory, "client", q)
    return {"q": q, "prompts": prompts}


@pytest.fixture(scope="module")
def world(client, db):
    tag = uuid.uuid4().hex[:6]
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    sa_email = f"kn_super_{tag}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, sa_email, hash_password(PASSWORD))
    dept = _exec(db, "INSERT INTO catalog_departments (code, name, scope) VALUES (%s, 'Bilgi Test', 'GENERAL') RETURNING id", f"GEN_KN{tag.upper()}")[0]
    platform_title = _exec(db, "INSERT INTO job_titles (id, tenant_id, code, title, category, base_role_prompt, catalog_department_id, scope, source) "
                               "VALUES (gen_random_uuid(), NULL, %s, 'Bilgi Uzmanı', 'Bilgi Test', 'Sen bir bilgi uzmanısın.', %s, 'GENERAL', 'CATALOG') RETURNING id",
                           f"GEN_KN{tag.upper()}_U", dept)[0]
    out = {"super": None, "platform_title": str(platform_title)}

    def company(suffix):
        tid = _exec(db, "INSERT INTO tenants (id, slug, name, plan_id, is_active) VALUES (gen_random_uuid(), %s, %s, "
                        "(SELECT id FROM plans WHERE code = 'ENTERPRISE'), TRUE) RETURNING id", f"kn_{suffix}_{tag}", f"Bilgi {suffix}")[0]
        email = f"kn_{suffix}_{tag}@kn-test.com.tr"
        _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
                  "VALUES (%s, 'HUMAN', 'Yönetici', %s, 'COMPANY_ADMIN', %s, 'IDLE') RETURNING id", tid, email, hash_password(PASSWORD))
        title = _exec(db, "INSERT INTO job_titles (id, tenant_id, code, title, category, base_role_prompt, source_title_id, scope, source) "
                          "VALUES (gen_random_uuid(), %s, 'KN', 'Bilgi Uzmanı', 'Bilgi', 'Sen bir bilgi uzmanısın.', %s, 'COMPANY', 'CATALOG') RETURNING id",
                      tid, platform_title)[0]
        agent = _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status, job_title_id) "
                          "VALUES (%s, 'AI_AGENT', 'Orion', 'KN', 'IDLE', %s) RETURNING id", tid, title)[0]
        other = _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, role, status) "
                          "VALUES (%s, 'AI_AGENT', 'Diğer', 'KN', 'IDLE') RETURNING id", tid)[0]
        project = _exec(db, "INSERT INTO projects (id, tenant_id, slug, name, status) VALUES (gen_random_uuid(), %s, 'kn', 'Bilgi Projesi', 'ACTIVE') RETURNING id", tid)[0]
        task = _exec(db, "INSERT INTO tasks (id, project_id, title, assignee_actor_id) VALUES (gen_random_uuid(), %s, 'Görev', %s) RETURNING id", project, agent)[0]
        r = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD})
        return {"id": str(tid), "title": str(title), "agent": str(agent), "other": str(other), "project": str(project),
                "task": str(task), "h": {"Authorization": f"Bearer {r.json()['access_token']}"}}

    out["a"], out["b"] = company("a"), company("b")
    r = client.post("/api/v1/auth/login", json={"email": sa_email, "password": PASSWORD})
    out["super"] = {"Authorization": f"Bearer {r.json()['access_token']}"}
    return out


def _upload_and_approve(client, url, headers, name, text):
    r = client.post(url, headers=headers, files={"file": (name, text.encode())})
    assert r.status_code == 201, r.text
    doc_id = r.json()["id"]
    r = client.post(f"/api/v1/documents/{doc_id}/approve", headers=headers, json={})
    assert r.status_code == 200, r.text
    return doc_id


def test_layers_isolation_promotion_and_chat(client, world, env):
    a, b = world["a"], world["b"]
    base = "/api/v1/company/{t}"
    _upload_and_approve(client, f"/api/v1/catalog/titles/{world['platform_title']}/documents", world["super"],
                        "platform.txt", "PLATFORM-BILGISI genel mesleki kural metni. " * 5)
    _upload_and_approve(client, f"{base.format(t=a['id'])}/job-titles/{a['title']}/documents", a["h"], "unvan.txt", "SIRKET-UNVAN-A bilgisi metni. " * 5)
    _upload_and_approve(client, f"{base.format(t=a['id'])}/ai-agents/{a['agent']}/documents", a["h"], "kisisel.txt", "PERSONEL-A bilgisi metni. " * 5)
    proj_doc = _upload_and_approve(client, f"/api/v1/projects/{a['project']}/documents", a["h"], "proje.txt", "PROJE-A eki metni. " * 5)
    _upload_and_approve(client, f"{base.format(t=b['id'])}/ai-agents/{b['agent']}/documents", b["h"], "b.txt", "SIRKET-B gizli bilgisi. " * 5)

    def search(c, agent, project=None):
        r = client.post(f"{base.format(t=c['id'])}/ai-agents/{agent}/knowledge/search", headers=c["h"],
                        json={"query": "bilgi", "project_id": project})
        assert r.status_code == 200, r.text
        return r.json()

    res = search(a, a["agent"], a["project"])
    text = " ".join(h["content"] for h in res["results"])
    assert set(res["counts"]) == {"PLATFORM_TITLE", "TITLE", "AGENT", "PROJECT"}
    assert "SIRKET-B" not in text  # KVKK: başka şirketin bilgisi asla gelmez
    assert "PROJE-A" not in " ".join(h["content"] for h in search(a, a["agent"])["results"])  # proje dışında görünmez
    # B şirketinin aynı katalog unvanı yoksa platform bilgisi de gelmez; A'nın hiçbir bilgisi B'ye gitmez
    assert all("-A" not in h["content"] for h in search(b, b["agent"])["results"])

    # Proje kapanışı: proje eki Kurum Hafızasına aktarılır, şirketin diğer AI personeli de görür
    assert "PROJE-A" not in " ".join(h["content"] for h in search(a, a["other"])["results"])
    r = client.post(f"/api/v1/projects/{a['project']}/knowledge/promote", headers=a["h"], json={"document_ids": [proj_doc]})
    assert r.json()["promoted"] == [proj_doc]
    other = search(a, a["other"])
    assert "PROJE-A" in " ".join(h["content"] for h in other["results"]) and set(other["counts"]) == {"GLOBAL"}

    summary = client.get(f"{base.format(t=a['id'])}/ai-agents/{a['agent']}/knowledge", headers=a["h"]).json()
    assert {l["layer"]: l["documents"] for l in summary["layers"]} == {"AGENT": 1, "TITLE": 1, "GLOBAL": 1, "PLATFORM_TITLE": 1}

    # Sohbet: AI personelin sistem promptuna katmanlar etiketli olarak girer
    r = client.post("/api/v1/chat/send", headers=a["h"], json={"task_id": a["task"], "content": "bilgi nedir?"})
    assert r.status_code == 200, r.text
    prompt = next(p for p in reversed(env["prompts"]) if "Bilgi kaynakların" in p)  # sohbet promptu (öğrenme adımı değil)
    for label in ("Platform Unvan Bilgisi", "Şirket Unvan Bilgisi", "AI Personel Bilgisi", "Kurum Hafızası"):
        assert label in prompt
    assert "SIRKET-B" not in prompt


def test_knowledge_permissions(client, world, env):
    a, b = world["a"], world["b"]
    url = f"/api/v1/company/{a['id']}/ai-agents/{a['agent']}/knowledge/search"
    assert client.post(url, headers=world["super"], json={"query": "bilgi"}).status_code == 403  # KVKK
    assert client.post(url, headers=b["h"], json={"query": "bilgi"}).status_code == 403
    assert client.get(f"/api/v1/projects/{a['project']}/documents", headers=b["h"]).status_code == 403


def test_chat_learning_needs_approval_for_company_memory(client, db, world, env):
    a = world["a"]
    r = client.post("/api/v1/chat/send", headers=a["h"], json={"task_id": a["task"], "content": "teklif süresi nedir?"})
    assert r.status_code == 200, r.text
    texts = {p.get("content") for p in env["q"].points.values()}
    assert any("SOHBET-AGENT" in (t or "") for t in texts)  # kişisel bilgi doğrudan öğrenilir
    assert not any("SOHBET-GLOBAL" in (t or "") for t in texts)  # şirket geneli bilgi onaysız öğrenilmez
    cands = client.get(f"/api/v1/memory?tenant_id={a['id']}&status=CANDIDATE", headers=a["h"]).json()
    cand = next(c for c in cands if "SOHBET-GLOBAL" in c["content"])
    assert client.post(f"/api/v1/memory/{cand['id']}/reject", headers=world["b"]["h"]).status_code == 403
    assert client.post(f"/api/v1/memory/promote/{cand['id']}", headers=a["h"]).status_code == 200
    other = client.post(f"/api/v1/company/{a['id']}/ai-agents/{a['other']}/knowledge/search", headers=a["h"],
                        json={"query": "teklif"}).json()
    assert any("SOHBET-GLOBAL" in h["content"] for h in other["results"])
    # Tekrar reddedilemez; yeni aday reddedilebilir
    assert client.post(f"/api/v1/memory/{cand['id']}/reject", headers=a["h"]).status_code == 409
