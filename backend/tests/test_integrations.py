"""
ADIM 10.1: MCP geçidi çekirdeği (dış ağ yok; Telegram API'si sahte).

- Kimlik kasası: AES-256-GCM, şifreli metin bağlantıya bağlı; şifreler yanıtta ve veritabanında açık görünmez.
- Yalnızca integration:manage (şirket yöneticisi); ekip üyesi ve RECDx platform personeli (KVKK) erişemez.
- AI personel bazında araç yetkisi; yetkisiz çağrı DENIED kaydı. Okuma anında; yazma insan onayı (onay/ret/yetki).
- Araç çağrısı kaydı silinemez; kimliği/aracı/argümanları değiştirilemez.
"""
import uuid

import psycopg2
import pytest

from app.core import vault
from app.core.security import hash_password
from app.integrations import telegram
from tests.test_workflow import PASSWORD, _exec, _login, _ready_project, world  # noqa: F401  (fikstür)

TOKEN = "123456:SAHTE-TELEGRAM-TOKEN-abcdefghijklmnop"


@pytest.fixture
def fake_telegram(monkeypatch):
    sent = []

    async def call(ctx, method, payload=None):
        assert ctx.secrets["bot_token"] == TOKEN  # kasadan doğru çözüldü
        if method == "getMe":
            return {"username": "sahte_bot", "first_name": "Sahte"}
        sent.append(payload)
        return {"message_id": len(sent)}
    monkeypatch.setattr(telegram, "_call", call)
    return sent


def test_vault_roundtrip_and_binding():
    token = vault.seal({"bot_token": TOKEN}, "a:b")
    assert TOKEN not in token and vault.unseal(token, "a:b") == {"bot_token": TOKEN}
    with pytest.raises(vault.VaultError):
        vault.unseal(token, "a:baska")  # başka bağlantıya kopyalanan şifreli metin çözülmez


def _super(client, db):
    hq = _exec(db, "SELECT id FROM tenants WHERE slug = 'recdx_hq'")[0]
    email = f"ent_super_{uuid.uuid4().hex[:6]}@recdx.com"
    _exec(db, "INSERT INTO actors (tenant_id, actor_type, display_name, email, role, password_hash, status) "
              "VALUES (%s, 'HUMAN', 'Süper', %s, 'SUPER_ADMIN', %s, 'IDLE')", hq, email, hash_password(PASSWORD))
    return _login(client, email)


def test_connection_crud_and_access(client, db, world, fake_telegram):
    w = world
    base = f"/api/v1/company/{w['tenant']}/integrations"
    body = {"connector": "telegram", "name": f"Telegram {uuid.uuid4().hex[:4]}", "config": {"default_chat_id": "-100"},
            "secrets": {"bot_token": TOKEN}}
    assert client.post(base, headers=w["member"]["h"], json=body).status_code == 403
    assert client.get(base, headers=_super(client, db)).status_code == 403  # KVKK
    assert client.post(base, headers=w["admin"]["h"], json={**body, "config": {"bilinmeyen": 1}}).status_code == 422
    assert client.post(base, headers=w["admin"]["h"], json={**body, "secrets": {}}).status_code == 422  # token zorunlu
    r = client.post(base, headers=w["admin"]["h"], json=body)
    assert r.status_code == 201, r.text
    conn = r.json()
    assert conn["secrets_set"] == {"bot_token": True} and TOKEN not in r.text
    stored = _exec(db, "SELECT secret FROM integration_connections WHERE id = %s", conn["id"])[0]
    assert stored.startswith("v1:") and TOKEN not in stored
    assert client.post(base, headers=w["admin"]["h"], json=body).status_code == 409  # aynı ad

    t = client.post(f"{base}/{conn['id']}/test", headers=w["admin"]["h"]).json()
    assert t["ok"] is True and "sahte_bot" in t["detail"]
    # Şifre alanı boş gönderilirse korunur
    r = client.put(f"{base}/{conn['id']}", headers=w["admin"]["h"], json={"config": {"default_chat_id": "-200"}, "secrets": {"bot_token": ""}})
    assert r.status_code == 200 and r.json()["config"]["default_chat_id"] == "-200"
    assert client.post(f"{base}/{conn['id']}/test", headers=w["admin"]["h"]).json()["ok"] is True
    tools = client.get(f"{base}/{conn['id']}/tools", headers=w["admin"]["h"]).json()
    assert {t["name"]: t["kind"] for t in tools} == {"get_bot": "READ", "send_message": "WRITE"}
    # Yönetici okuma aracını dener; yazma aracı elle denenemez
    tr = client.post(f"{base}/{conn['id']}/try", headers=w["admin"]["h"], json={"tool": "get_bot"}).json()
    assert tr["status"] == "EXECUTED" and tr["result"]["username"] == "sahte_bot"
    assert client.post(f"{base}/{conn['id']}/try", headers=w["admin"]["h"], json={"tool": "send_message", "arguments": {"text": "x"}}).status_code == 409


def test_agent_tools_approval_and_log(client, db, world, fake_telegram):
    from app.db.models import Actor, Project
    from app.db.session import AsyncSessionLocal
    from app.services import tool_gateway

    w = world
    base = f"/api/v1/company/{w['tenant']}/integrations"
    conn = client.post(base, headers=w["admin"]["h"], json={"connector": "telegram", "name": f"Ekip {uuid.uuid4().hex[:4]}",
                                                             "config": {"default_chat_id": "-100"}, "secrets": {"bot_token": TOKEN}}).json()
    other_tenant_agent = _exec(db, "SELECT id FROM actors WHERE actor_type = 'AI_AGENT' AND tenant_id <> %s LIMIT 1", w["tenant"])
    if other_tenant_agent:
        r = client.put(f"{base}/{conn['id']}/grants", headers=w["admin"]["h"], json={"grants": [{"actor_id": str(other_tenant_agent[0]), "tool": "*"}]})
        assert r.status_code == 422  # başka şirketin AI personeline yetki verilemez
    assert client.put(f"{base}/{conn['id']}/grants", headers=w["admin"]["h"], json={"grants": [{"actor_id": w["agent"], "tool": "yok"}]}).status_code == 422
    r = client.put(f"{base}/{conn['id']}/grants", headers=w["admin"]["h"],
                   json={"grants": [{"actor_id": w["agent"], "tool": "get_bot"}, {"actor_id": w["agent"], "tool": "send_message"}]})
    assert r.status_code == 200 and len(r.json()) == 2
    pid, _, _ = _ready_project(client, w, "Araç Projesi")

    async def run(agent_id, name, args):
        async with AsyncSessionLocal() as s:
            agent = await s.get(Actor, uuid.UUID(agent_id))
            project = await s.get(Project, uuid.UUID(pid))
            items = await tool_gateway.available(s, agent)
            fn = {t.name: tool_gateway.fn_name(c, t.name) for c, t in items if str(c.id) == conn["id"]}
            call = await tool_gateway.invoke(s, agent, fn.get(name, name), args, project=project)
            await s.commit()
            return tool_gateway.call_out(call), sorted(fn), tool_gateway.openai_tools(items)

    read, names, defs = client.portal.call(run, w["agent"], "get_bot", {})
    assert names == ["get_bot", "send_message"] and read["status"] == "EXECUTED" and read["result"]["username"] == "sahte_bot"
    assert any("insan onayından sonra" in d["function"]["description"] for d in defs)
    write, _, _ = client.portal.call(run, w["agent"], "send_message", {"text": "Proje başladı"})
    assert write["status"] == "PENDING_APPROVAL" and write["approver_actor_id"] == w["admin"]["id"] and not fake_telegram
    denied, names2, _ = client.portal.call(run, w["reviewer"], "get_bot", {})  # yetki verilmemiş AI personel
    assert denied["status"] == "DENIED" and names2 == []

    pending = client.get("/api/v1/me/tool-approvals", headers=w["admin"]["h"]).json()
    assert any(p["id"] == write["id"] for p in pending)
    assert not client.get("/api/v1/me/tool-approvals", headers=w["member"]["h"]).json()
    assert client.post(f"/api/v1/tool-calls/{write['id']}/decision", headers=w["member"]["h"], json={"approve": True}).status_code == 403
    done = client.post(f"/api/v1/tool-calls/{write['id']}/decision", headers=w["admin"]["h"], json={"approve": True}).json()
    assert done["status"] == "EXECUTED" and fake_telegram == [{"chat_id": "-100", "text": "Proje başladı"}]
    assert client.post(f"/api/v1/tool-calls/{write['id']}/decision", headers=w["admin"]["h"], json={"approve": True}).status_code == 409
    second, _, _ = client.portal.call(run, w["agent"], "send_message", {"text": "İkinci"})
    rej = client.post(f"/api/v1/tool-calls/{second['id']}/decision", headers=w["admin"]["h"], json={"approve": False, "note": "Gerek yok"}).json()
    assert rej["status"] == "REJECTED" and len(fake_telegram) == 1

    log = client.get(f"/api/v1/company/{w['tenant']}/tool-calls", headers=w["admin"]["h"]).json()
    assert {"EXECUTED", "DENIED", "REJECTED"} <= {c["status"] for c in log}
    with pytest.raises(psycopg2.Error, match="değiştirilemez"):
        _exec(db, "UPDATE tool_calls SET arguments = '{}'::jsonb WHERE id = %s", write["id"])
    with pytest.raises(psycopg2.Error, match="silinemez"):
        _exec(db, "DELETE FROM tool_calls WHERE id = %s", write["id"])


def test_agent_uses_tools_in_chat(client, db, world, fake_telegram, monkeypatch):
    """ADIM 10.2: AI personel sohbette aracı kendisi çağırır; okuma sonucu yanıta girer, yazma onaya düşer."""
    from app.services.evren_client import ChatResult, evren_client

    w = world
    base = f"/api/v1/company/{w['tenant']}/integrations"
    conn = client.post(base, headers=w["admin"]["h"], json={"connector": "telegram", "name": f"Sohbet {uuid.uuid4().hex[:4]}",
                                                             "config": {"default_chat_id": "-100"}, "secrets": {"bot_token": TOKEN}}).json()
    client.put(f"{base}/{conn['id']}/grants", headers=w["admin"]["h"], json={"grants": [{"actor_id": w["agent"], "tool": "*"}]})
    pid, _, _ = _ready_project(client, w, "Araçlı Sohbet")
    ai_task = str(_exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'AI adımı'", pid)[0])
    seen = {"tools": [], "system": []}
    plan = {"want": "get_bot"}

    async def chat(model_code, messages, **kw):
        tools = kw.get("tools") or []
        seen["tools"].append([t["function"]["name"] for t in tools])
        seen["system"].append(messages[0]["content"])
        tool_msgs = [m for m in messages if m.get("role") == "tool"]
        if tools and not tool_msgs:
            name = next(t["function"]["name"] for t in tools if t["function"]["name"].endswith(plan["want"]))
            args = '{"text": "Merhaba ekip"}' if plan["want"] == "send_message" else "{}"
            return ChatResult("", None, 50, 5, {}, tool_calls=[{"id": "t1", "type": "function", "function": {"name": name, "arguments": args}}])
        return ChatResult(f"Araç sonucu: {tool_msgs[-1]['content'] if tool_msgs else 'yok'}", None, 80, 20, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    r = client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": ai_task, "content": "Botumuzun adı ne?"})
    assert r.status_code == 200, r.text
    assert "sahte_bot" in r.json()["assistant_message"]["content"]
    assert any(n.endswith("get_bot") for n in seen["tools"][0]) and "Yazma işlemleri insan onayına düşer" in seen["system"][0]
    log = client.get(f"/api/v1/company/{w['tenant']}/tool-calls", headers=w["admin"]["h"]).json()
    assert any(c["tool"] == "get_bot" and c["status"] == "EXECUTED" and c["actor_id"] == w["agent"] and c["project_id"] == pid for c in log)

    plan["want"] = "send_message"
    r = client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": ai_task, "content": "Ekibe merhaba de"})
    assert r.status_code == 200 and "pending_approval" in r.json()["assistant_message"]["content"]
    assert not fake_telegram  # onaysız gönderilmedi
    pending = [c for c in client.get(f"/api/v1/company/{w['tenant']}/tool-calls?status=PENDING_APPROVAL", headers=w["admin"]["h"]).json()
               if c["tool"] == "send_message" and c["arguments"] == {"text": "Merhaba ekip"}]
    assert pending

    # Yetkisi olmayan insan adımında (RECAi) araç verilmez
    human = str(_exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'İnsan adımı'", pid)[0])
    seen["tools"].clear()
    client.post("/api/v1/chat/send", headers=w["admin"]["h"], json={"task_id": human, "content": "Durum?"})
    assert seen["tools"] and seen["tools"][0] == []
