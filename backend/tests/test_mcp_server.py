"""
ADIM 12.6: RECOrion'un kendi MCP sunucusu (Streamable HTTP, JSON-RPC) ve kişisel erişim anahtarları.

- Anahtar bir kez gösterilir, yalnızca özeti saklanır; RECDx personeli anahtar oluşturamaz (KVKK); iptal/süre dolumu reddedilir.
- initialize / tools/list / tools/call; READ anahtarı yazma aracını göremez ve çağıramaz; onay aracı yoktur.
- Araçlar kullanıcının kendi yetkileriyle: başka şirketin projesi görünmez; adım yalnızca başlamamış projeye eklenir.
- create_project: proje taslak açılır, RECAi plan taslağı hazırlar (onay bekler); her çağrı denetim kaydına yazılır.
"""
import time
import uuid

import pytest

from tests.test_integrations import _super
from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)

URL = "/api/v1/mcp"


def _rpc(client, token, method, params=None, req_id=1):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    body = {"jsonrpc": "2.0", "method": method, "params": params or {}}
    if req_id is not None:
        body["id"] = req_id
    return client.post(URL, headers=headers, json=body)


def _call(client, token, name, args=None):
    r = _rpc(client, token, "tools/call", {"name": name, "arguments": args or {}})
    assert r.status_code == 200, r.text
    return r.json()


def _token(client, h, scopes=("READ",), name=None):
    r = client.post("/api/v1/me/personal-tokens", headers=h, json={"name": name or f"Claude {uuid.uuid4().hex[:4]}", "scopes": list(scopes), "days": 30})
    assert r.status_code == 201, r.text
    return r.json()


def test_tokens_and_auth(client, db, world):
    w = world
    t = _token(client, w["member"]["h"])
    raw = t["token"]
    assert raw.startswith("rxp_") and t["server_url"].endswith("/api/v1/mcp") and t["scopes"] == ["READ"]
    listed = client.get("/api/v1/me/personal-tokens", headers=w["member"]["h"]).json()
    assert raw not in str(listed) and listed["tokens"][0]["prefix"] == raw[:10]
    stored = _exec(db, "SELECT token_hash FROM personal_tokens WHERE id = %s", t["id"])[0]
    assert stored != raw and len(stored) == 64
    assert client.post("/api/v1/me/personal-tokens", headers=_super(client, db), json={"name": "Süper", "scopes": ["READ"]}).status_code == 403
    assert client.post("/api/v1/me/personal-tokens", headers=w["member"]["h"], json={"name": "Kötü", "scopes": ["ADMIN"]}).status_code == 422

    r = _rpc(client, None, "initialize")
    assert r.status_code == 401 and "Bearer" in r.headers["www-authenticate"]
    assert _rpc(client, "rxp_uydurma", "initialize").status_code == 401
    jwt_token = w["member"]["h"]["Authorization"].split()[1]
    assert _rpc(client, jwt_token, "initialize").status_code == 401  # oturum token'ı MCP anahtarı değildir

    r = _rpc(client, raw, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}})
    res = r.json()["result"]
    assert res["protocolVersion"] == "2025-06-18" and res["serverInfo"]["name"] == "RECOrion" and "tools" in res["capabilities"]
    assert _rpc(client, raw, "notifications/initialized", req_id=None).status_code == 202
    tools = _rpc(client, raw, "tools/list").json()["result"]["tools"]
    assert {x["name"] for x in tools} == {"list_projects", "get_project", "get_step_output", "list_my_approvals"}
    assert all(x["annotations"]["readOnlyHint"] for x in tools)
    assert not any("approve" in x["name"] or "decide" in x["name"] for x in tools)
    r = _call(client, raw, "create_project", {"name": "Yetkisiz"})
    assert r["error"]["code"] == -32003  # READ anahtarı yazamaz
    assert _rpc(client, raw, "bilinmeyen/yontem").json()["error"]["code"] == -32601

    revoked = client.delete(f"/api/v1/me/personal-tokens/{t['id']}", headers=w["member"]["h"]).json()
    assert revoked["active"] is False
    assert _rpc(client, raw, "tools/list").status_code == 401
    t2 = _token(client, w["member"]["h"])
    _exec(db, "UPDATE personal_tokens SET expires_at = now() - interval '1 minute' WHERE id = %s", t2["id"])
    assert _rpc(client, t2["token"], "tools/list").status_code == 401
    assert client.delete(f"/api/v1/me/personal-tokens/{t2['id']}", headers=w["admin"]["h"]).status_code == 404  # başkasının anahtarı


def test_tools_with_user_permissions(client, db, world, monkeypatch):
    from app.services import project_planning

    w = world
    admin_w = _token(client, w["admin"]["h"], ("READ", "WRITE"))["token"]
    member_r = _token(client, w["member"]["h"])["token"]
    pid, human, _ = _ready_project(client, w, f"MCP Proje {uuid.uuid4().hex[:4]}")

    listed = _call(client, admin_w, "list_projects")["result"]
    assert listed["isError"] is False
    mine = next(p for p in listed["structuredContent"]["projects"] if p["id"] == pid)
    assert mine["status"] == "READY" and mine["steps_total"] >= 2 and mine["url"].endswith(f"project={pid}")
    detail = _call(client, admin_w, "get_project", {"project_id": pid})["result"]["structuredContent"]
    assert {s["title"] for s in detail["steps"]} >= {"İnsan adımı", "Bağımlı adım"}
    other = _exec(db, "SELECT id FROM projects WHERE tenant_id <> %s LIMIT 1", w["tenant"])
    if other:
        r = _call(client, admin_w, "get_project", {"project_id": str(other[0])})["result"]
        assert r["isError"] is True  # başka şirketin projesi
    out = _call(client, member_r, "get_step_output", {"task_id": human})["result"]
    assert out["isError"] is False and out["structuredContent"]["output"] is None  # henüz çıktı yok
    appr = _call(client, admin_w, "list_my_approvals")["result"]["structuredContent"]
    assert "steps" in appr and "transfers" in appr and "Onaylarım" in appr["note"]

    # Dışarıdan proje: taslak açılır, RECAi plan taslağı hazırlar (onay bekler)
    async def fake_plan(db_, project, feedback=None):
        project.plan = {"summary": "s", "steps": [{"key": "S1", "title": "Analiz", "estimated_days": 2}], "approved": False}
        project.status = "PLANNING"
        await db_.commit()
        return project.plan
    monkeypatch.setattr(project_planning, "suggest_plan", fake_plan)
    r = _call(client, admin_w, "create_project", {"name": "Dışarıdan Case", "kind": "CASE", "requirements": "Müşteri şikâyetini incele."})["result"]
    created = r["structuredContent"]
    assert r["isError"] is False and created["kind"] == "CASE" and "onay" in created["message"]
    end = time.time() + 10
    while time.time() < end:
        d = _call(client, admin_w, "get_project", {"project_id": created["id"]})["result"]["structuredContent"]
        if d["status"] == "PLANNING":
            break
        time.sleep(0.3)
    assert d["status"] == "PLANNING" and d["plan_approved"] is False and d["plan_draft_steps"][0]["title"] == "Analiz"
    r = _call(client, admin_w, "add_step", {"project_id": created["id"], "title": "Rapor", "job_title": "Analist", "estimated_days": 1,
                                            "depends_on": ["S1", "S9"]})["result"]["structuredContent"]
    assert r["step"]["key"] == "S2" and r["step"]["depends_on"] == ["S1"] and r["plan_steps"] == 2
    r = _call(client, admin_w, "add_step", {"project_id": pid, "title": "Geç adım"})["result"]
    assert r["isError"] is True and "başlamamış" in r["structuredContent"]["error"]  # READY proje: plan kilitli
    member_w = _token(client, w["member"]["h"], ("READ", "WRITE"))["token"]
    r = _call(client, member_w, "add_step", {"project_id": created["id"], "title": "İzinsiz"})["result"]
    assert r["isError"] is True  # proje yöneticisi değil
    audit = _exec(db, "SELECT count(*) FROM audit_events WHERE action = 'MCP_TOOL_CALL' AND tenant_id = %s", w["tenant"])[0]
    assert audit >= 6
