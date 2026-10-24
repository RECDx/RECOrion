"""
ADIM 10.3: ilk bağlayıcılar (Odoo, Trello, GitHub/Gitea) — sahte dış sunucularla (httpx.MockTransport; gerçek ağa çıkılmaz).

- Odoo: giriş, arama/sayma/model bulma, oluşturma/güncelleme; izinli modeller dışı reddedilir; hatalı anahtar anlaşılır hata.
- Odoo JSON-2 (ADIM 12.2): Odoo 19+ sunucuda /json/2 (Bearer anahtar, kullanıcı adı gerekmez); eski sunucuda JSON-RPC'ye düşülür.
- Trello: pano/kart okuma, kart açma; anahtar/token hata mesajında görünmez.
- GitHub/Gitea: depo/issue/dosya okuma, issue açma; doğru yetki başlığı.
- Ortak "yalnızca okuma" erişimi: yazma araçları listelenmez (API'de de); geçersiz seçim 422.
"""
import asyncio
import base64
import json
import uuid

import httpx
import pytest

from app.integrations import base, get
from app.integrations.base import Context, ToolError
from tests.test_workflow import _exec, world  # noqa: F401  (fikstür)

ODOO_KEY = "odoo-sahte-anahtar-123"
TRELLO_KEY, TRELLO_TOKEN = "trellokey0000", "trellotoken1111"
GH_TOKEN = "ghp_sahte_token"


@pytest.fixture
def fake_http(monkeypatch):
    seen = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        host = req.url.host
        if host == "odoo.example" and req.url.path.startswith("/json/2/"):
            return httpx.Response(404, headers={"content-type": "text/html"}, text="<h1>Not Found</h1>")  # Odoo 18: JSON-2 yok
        if host == "odoo20.example":
            if req.headers.get("authorization") != f"bearer {ODOO_KEY}":
                return httpx.Response(401, json={"name": "werkzeug.exceptions.Unauthorized", "message": "Invalid apikey"})
            assert req.headers.get("x-odoo-database") == "sirket" and req.url.path.startswith("/json/2/")
            _, _, _, model, method = req.url.path.split("/")
            body = json.loads(req.content)
            if model == "yok.model":
                return httpx.Response(404, json={"name": "NotFound", "message": "the model 'yok.model' does not exist"})
            res = {"search_read": [{"id": 5, "display_name": "Yeni Nesil"}], "search_count": 9, "create": [77], "write": True,
                   "context_get": {"uid": 2, "lang": "tr_TR"},
                   "fields_get": {"name": {"string": "Ad", "type": "char", "required": True},
                                  "uom_id": {"string": "Birim", "type": "many2one", "relation": "uom.uom", "required": True},
                                  "type": {"string": "Tür", "type": "selection", "selection": [["consu", "Mal"], ["service", "Hizmet"]]},
                                  "create_date": {"string": "Oluşturma", "type": "datetime", "readonly": True},
                                  "message_ids": {"string": "Mesajlar", "type": "one2many"}}}[method]
            seen.append(("json2", method, body))
            return httpx.Response(200, headers={"content-type": "application/json"}, json=res)
        if host == "odoo.example":
            body = json.loads(req.content)
            p = body["params"]
            if p["service"] == "common" and p["method"] == "version":
                return httpx.Response(200, json={"result": {"server_version": "19.0"}})
            if p["service"] == "common" and p["method"] == "login":
                return httpx.Response(200, json={"result": 7 if p["args"][2] == ODOO_KEY else False})
            db, uid, key, model, method, args, kw = p["args"]
            assert (db, uid, key) == ("sirket", 7, ODOO_KEY)
            if model == "secret.model":
                return httpx.Response(200, json={"error": {"message": "Odoo Server Error", "data": {"message": "Erişim reddedildi"}}})
            res = {"search_read": [{"id": 1, "display_name": "ACME"}], "search_count": 3, "create": 42, "write": True}[method]
            if model == "ir.model":
                res = [{"model": "res.partner", "name": "Kontak"}]
            return httpx.Response(200, json={"result": res})
        if host == "api.trello.com":
            if req.url.params.get("token") != TRELLO_TOKEN:
                return httpx.Response(401, text=f"invalid token {req.url.params.get('token')}")
            path = req.url.path
            if path.endswith("/members/me/boards"):
                return httpx.Response(200, json=[{"id": "b1", "name": "Pazarlama", "url": "https://trello.com/b/b1"}])
            if path.endswith("/boards/b1/cards"):
                return httpx.Response(200, json=[{"id": "c1", "name": "Afiş", "idList": "l1", "closed": False},
                                                 {"id": "c2", "name": "Eski", "idList": "l1", "closed": True}])
            if path.endswith("/cards") and req.method == "POST":
                return httpx.Response(200, json={"id": "c9", "url": "https://trello.com/c/c9"})
            if path.endswith("/members/me"):
                return httpx.Response(200, json={"username": "test", "fullName": "Test Kullanıcı"})
        if host in ("api.github.com", "git.sirket.example"):
            auth = req.headers.get("authorization")
            assert auth == (f"Bearer {GH_TOKEN}" if host == "api.github.com" else f"token {GH_TOKEN}")
            path = req.url.path.removeprefix("/api/v1")
            if path == "/user":
                return httpx.Response(200, json={"login": "acme-bot"})
            if path == "/repos/acme/portal/issues" and req.method == "GET":
                return httpx.Response(200, json=[{"number": 5, "title": "Hata", "state": "open", "html_url": "u", "labels": []},
                                                 {"number": 6, "title": "PR", "state": "open", "pull_request": {}}])
            if path == "/repos/acme/portal/issues":
                return httpx.Response(201, json={"number": 7, "html_url": "https://github.com/acme/portal/issues/7"})
            if path == "/repos/acme/portal/contents/README.md":
                return httpx.Response(200, json={"path": "README.md", "size": 5, "content": base64.b64encode(b"Merhaba").decode()})
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(599)
    monkeypatch.setattr(base, "TRANSPORT", httpx.MockTransport(handler))
    return seen


def _run(code, tool, args, config=None, secrets=None):
    async def go():
        ctx = Context(config=config or {}, secrets=secrets or {})
        t = next(t for t in await get(code).tools(ctx) if t.name == tool)
        return await t.run(ctx, args)
    return asyncio.run(go())


ODOO_CFG = {"url": "https://odoo.example", "db": "sirket", "username": "bot@sirket.com"}


def test_odoo_connector(fake_http):
    sec = {"api_key": ODOO_KEY}
    assert asyncio.run(get("odoo").test(Context(ODOO_CFG, sec))).startswith("Odoo 19.0 · JSON-RPC · kullanıcı #7")
    r = _run("odoo", "search_records", {"model": "res.partner", "domain": [["is_company", "=", True]], "limit": 999}, ODOO_CFG, sec)
    assert r["records"][0]["display_name"] == "ACME"
    kw = json.loads(fake_http[-1].content)["params"]["args"][6]
    assert kw["limit"] == 100  # üst sınır
    assert _run("odoo", "count_records", {"model": "res.partner"}, ODOO_CFG, sec)["count"] == 3
    assert _run("odoo", "find_models", {"keyword": "partner"}, ODOO_CFG, sec)[0]["model"] == "res.partner"
    assert _run("odoo", "create_record", {"model": "res.partner", "values": {"name": "Yeni"}}, ODOO_CFG, sec) == {"model": "res.partner", "id": 42}
    assert _run("odoo", "update_record", {"model": "res.partner", "ids": [1], "values": {"name": "X"}}, ODOO_CFG, sec)["updated"] == [1]
    with pytest.raises(ToolError, match="izinli değil"):
        _run("odoo", "search_records", {"model": "hr.employee"}, {**ODOO_CFG, "allowed_models": "res.partner, sale.order"}, sec)
    with pytest.raises(ToolError, match="Erişim reddedildi"):
        _run("odoo", "search_records", {"model": "secret.model"}, ODOO_CFG, sec)
    with pytest.raises(ToolError, match="girişi reddedildi") as e:
        _run("odoo", "count_records", {"model": "res.partner"}, ODOO_CFG, {"api_key": "yanlis-anahtar"})
    assert "yanlis-anahtar" not in str(e.value)
    with pytest.raises(ToolError, match="tam sayı"):
        _run("odoo", "update_record", {"model": "res.partner", "ids": ["1 or 1=1"], "values": {"a": 1}}, ODOO_CFG, sec)
    with pytest.raises(ToolError, match="kullanıcı \\(e-posta\\)"):  # eski sürümde kullanıcı adı zorunlu
        _run("odoo", "count_records", {"model": "res.partner"}, {**ODOO_CFG, "username": ""}, sec)


def test_odoo_json2_api(fake_http):
    from app.integrations import odoo

    cfg = {"url": "https://odoo20.example", "db": "sirket"}  # kullanıcı adı yok: JSON-2'de gerekmez
    sec = {"api_key": ODOO_KEY}
    odoo._styles.clear()
    info = asyncio.run(get("odoo").test(Context(cfg, sec)))
    assert "JSON-2 API · kullanıcı #2" in info
    r = _run("odoo", "search_records", {"model": "res.partner", "domain": [["is_company", "=", True]], "limit": 999, "order": "name"}, cfg, sec)
    assert r["records"][0]["display_name"] == "Yeni Nesil"
    assert fake_http[-1] == ("json2", "search_read", {"domain": [["is_company", "=", True]], "fields": ["display_name"], "limit": 100, "order": "name"})
    assert _run("odoo", "count_records", {"model": "res.partner"}, cfg, sec)["count"] == 9
    assert _run("odoo", "create_record", {"model": "product.template", "values": {"name": "Vida"}}, cfg, sec) == {"model": "product.template", "id": 77}
    assert fake_http[-1] == ("json2", "create", {"vals_list": [{"name": "Vida"}]})
    _run("odoo", "update_record", {"model": "res.partner", "ids": [5], "values": {"name": "X"}}, cfg, sec)
    assert fake_http[-1] == ("json2", "write", {"ids": [5], "vals": {"name": "X"}})
    d = _run("odoo", "describe_model", {"model": "product.template"}, cfg, sec)
    names = {f["name"]: f for f in d["fields"]}
    assert set(names) == {"name", "type", "uom_id"}  # salt okunur ve çoklu ilişki alanları gizlenir
    assert names["uom_id"]["relation"] == "uom.uom" and names["type"]["selection"][1] == ["service", "Hizmet"]
    with pytest.raises(ToolError, match="does not exist"):
        _run("odoo", "count_records", {"model": "yok.model"}, cfg, sec)
    with pytest.raises(ToolError, match="anahtarı geçersiz") as e:
        _run("odoo", "count_records", {"model": "res.partner"}, cfg, {"api_key": "yanlis-anahtar"})
    assert "yanlis-anahtar" not in str(e.value)
    with pytest.raises(ToolError, match="JSON-2 API'si yok"):  # eski sunucuda JSON-2 zorlanırsa anlaşılır hata
        _run("odoo", "count_records", {"model": "res.partner"}, {**ODOO_CFG, "api_style": "json2"}, sec)


def test_trello_connector(fake_http):
    sec = {"api_key": TRELLO_KEY, "token": TRELLO_TOKEN}
    assert _run("trello", "list_boards", {}, secrets=sec)[0]["name"] == "Pazarlama"
    cards = _run("trello", "list_cards", {}, {"default_board_id": "b1"}, sec)
    assert [c["id"] for c in cards] == ["c1"]  # kapalı kart dönmez
    assert _run("trello", "create_card", {"list_id": "l1", "name": "Yeni kart"}, secrets=sec)["id"] == "c9"
    with pytest.raises(ToolError, match="Pano") :
        _run("trello", "list_lists", {}, secrets=sec)
    with pytest.raises(ToolError) as e:
        _run("trello", "list_boards", {}, secrets={"api_key": TRELLO_KEY, "token": "sizan-token-999"})
    assert "401" in str(e.value) and "sizan-token-999" not in str(e.value) and TRELLO_KEY not in str(e.value)


@pytest.mark.parametrize("code,config", [("github", {}), ("gitea", {"base_url": "https://git.sirket.example"})])
def test_git_hosting_connectors(fake_http, code, config):
    sec = {"token": GH_TOKEN}
    assert "@acme-bot" in asyncio.run(get(code).test(Context(config, sec)))
    issues = _run(code, "list_issues", {"repo": "acme/portal"}, config, sec)
    assert [i["number"] for i in issues] == [5]  # PR'lar issue sayılmaz
    assert _run(code, "read_file", {"repo": "https://github.com/acme/portal.git", "path": "README.md"}, config, sec)["content"] == "Merhaba"
    assert _run(code, "create_issue", {"repo": "acme/portal", "title": "Yeni"}, config, sec)["number"] == 7
    with pytest.raises(ToolError, match="sahip/depo"):
        _run(code, "list_issues", {"repo": "../../etc"}, config, sec)
    with pytest.raises(ToolError, match="404"):
        _run(code, "list_issues", {"repo": "acme/yok"}, config, sec)


def test_read_only_access_hides_write_tools(client, db, world, fake_http):
    w = world
    names = lambda cfg: {t.name for t in asyncio.run(get("odoo").tools(Context(cfg, {})))}  # noqa: E731
    assert "create_record" in names(ODOO_CFG) and "create_record" not in names({**ODOO_CFG, "access": "READ_ONLY"})
    base_url = f"/api/v1/company/{w['tenant']}/integrations"
    body = {"connector": "odoo", "name": f"Odoo {uuid.uuid4().hex[:4]}", "config": {**ODOO_CFG, "access": "HERSEY"},
            "secrets": {"api_key": ODOO_KEY}}
    assert client.post(base_url, headers=w["admin"]["h"], json=body).status_code == 422  # geçersiz seçim
    r = client.post(base_url, headers=w["admin"]["h"], json={**body, "config": {**ODOO_CFG, "access": "READ_ONLY"}})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    tools = client.get(f"{base_url}/{cid}/tools", headers=w["admin"]["h"]).json()
    assert {t["name"] for t in tools} == {"find_models", "search_records", "count_records", "describe_model"}
    assert all(t["kind"] == "READ" for t in tools)
    t = client.post(f"{base_url}/{cid}/test", headers=w["admin"]["h"]).json()
    assert t["ok"] is True and ODOO_KEY not in json.dumps(t)
    cat = client.get("/api/v1/integrations/connectors", headers=w["admin"]["h"]).json()["connectors"]
    assert {"odoo", "trello", "github", "gitea", "telegram"} <= {c["code"] for c in cat}
    assert all(any(f["key"] == "access" for f in c["config_fields"]) for c in cat)
