"""
ADIM 12.5: Logo'ya Edge ajanının REST şablonlarıyla yazma — gerçek ajan kodu + sahte Logo REST servisi (edge_agent/fake_logo_rest.py;
GERÇEK LOGO DEĞİL) + RECOrion eşleme/aktarım. Gerçek ağa çıkılmaz (sahte servis 127.0.0.1'de).

- Ajan: REST şablonu doğrulaması (adres/'..'/'?' yasak, yer tutucular tanımlı parametrelerle aynı, okuma=GET), yalnızca tam değer
  yer tutucusu, boş isteğe bağlı alan gövdeden çıkar, parola akışıyla giriş + 401'de yeniden giriş, hedef hatası anlaşılır ileti.
- RECOrion: hazır "Logo malzeme kartı" eşlemesi ajanın araç şemasıyla doğrulanır; aktarım onaydan sonra Logo'da kart açar;
  aynı stok koduyla ikinci aktarım güncelleme aracıyla güncellenir (çift kart yok); güncelleme aracı olmayan cari zaten
  varsa yeni kart açılmaz.
"""
import json
import socket
import uuid

import httpx
import pytest

from app.config import settings
from tests.test_edge import AGENT_DIR, Running, _agent_module
from tests.test_integration_catalog import _seed as _seed_catalog
from tests.test_mappings import _seed
from tests.test_transfers import _project_with_done_step, _wait, fake_extract  # noqa: F401  (fikstür)
from tests.test_workflow import world  # noqa: F401  (fikstür)

pytestmark = pytest.mark.skipif(not (AGENT_DIR / "fake_logo_rest.py").exists(), reason="edge_agent bağlı değil")


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def logo_rest(monkeypatch):
    import importlib.util

    spec = importlib.util.spec_from_file_location("fake_logo_rest", AGENT_DIR / "fake_logo_rest.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for k in ("items", "Arps"):
        mod.STATE[k].clear()
    port = _free_port()
    srv = mod.serve(port)
    monkeypatch.setenv("LOGO_USER", mod.USER)
    monkeypatch.setenv("LOGO_PASSWORD", mod.PASSWORD)
    monkeypatch.setenv("LOGO_CLIENT_ID", mod.CLIENT.split(":")[0])
    monkeypatch.setenv("LOGO_CLIENT_SECRET", mod.CLIENT.split(":")[1])
    yield mod, f"http://127.0.0.1:{port}"
    srv.shutdown()


def _cfg(tmp_path, base_url, templates=None, allow_write=True):
    tfile = tmp_path / "templates.json"
    tfile.write_text(json.dumps(templates) if templates is not None else (AGENT_DIR / "templates.logo_rest.example.json").read_text(encoding="utf-8"),
                     encoding="utf-8")
    cfg = tmp_path / "edge_config.json"
    cfg.write_text(json.dumps({"hostname": "LOGO-REST-TEST", "templates_file": str(tfile), "allow_write": allow_write, "audit_log": str(tmp_path / "audit.log"),
                               "http_api": {"base_url": base_url, "auth": {"type": "oauth_password", "token_path": "/api/v1/token",
                                                                           "username_env": "LOGO_USER", "password_env": "LOGO_PASSWORD",
                                                                           "client_id_env": "LOGO_CLIENT_ID", "client_secret_env": "LOGO_CLIENT_SECRET",
                                                                           "form": {"firmno": "1"}}}}), encoding="utf-8")
    return cfg


def test_agent_rest_templates_validation_and_calls(tmp_path, logo_rest):
    edge = _agent_module()
    mod, url = logo_rest
    bad = [{"name": "kotu", "kind": "WRITE", "params": [], "http": {"method": "POST", "path": "http://baska.example/x"}}]
    with pytest.raises(SystemExit, match="yol"):
        edge.load_config(_cfg(tmp_path, url, bad))
    mismatch = [{"name": "kotu", "kind": "WRITE", "params": [{"name": "a", "type": "string"}], "http": {"method": "POST", "path": "/x", "body": {"A": ":b"}}}]
    with pytest.raises(SystemExit, match="aynı olmalı"):
        edge.load_config(_cfg(tmp_path, url, mismatch))
    readpost = [{"name": "kotu", "kind": "READ", "params": [], "http": {"method": "POST", "path": "/x"}}]
    with pytest.raises(SystemExit, match="GET"):
        edge.load_config(_cfg(tmp_path, url, readpost))

    cfg = edge.load_config(_cfg(tmp_path, url))
    api = edge.HTTPApi(cfg["http_api"])
    job = {"template": "logo_malzeme_ekle", "params": {"kod": "RECT-ELT-01", "ad": "El terminali", "kart_turu": 1, "birim_seti": "ADET", "kdv_orani": 20}}
    r = edge.execute(cfg, None, job, api)
    assert r["status"] == 201 and r["id"] == 1001
    stored = mod.STATE["items"][1001]
    assert stored == {"INTERNAL_REFERENCE": 1001, "CARD_TYPE": 1, "CODE": "RECT-ELT-01", "NAME": "El terminali", "UNITSET_CODE": "ADET", "VAT": 20}
    # Metin içine "yer tutucu" sızdırma işe yaramaz: değer olduğu gibi yazılır
    r = edge.execute(cfg, None, {"template": "logo_malzeme_ekle", "params": {**job["params"], "kod": "X-2", "ad": ":kod"}}, api)
    assert mod.STATE["items"][r["id"]]["NAME"] == ":kod"
    with pytest.raises(edge.TemplateError, match="HTTP 409: Bu kodla kayıt zaten var"):
        edge.execute(cfg, None, job, api)
    found = edge.execute(cfg, None, {"template": "logo_malzeme_bul", "params": {"kod": "RECT-ELT-01"}}, api)
    assert found["id"] == 1001 and found["row_count"] == 1
    assert edge.execute(cfg, None, {"template": "logo_malzeme_bul", "params": {"kod": "YOK"}}, api)["id"] is None
    mod.STATE["token"] = "yeni-token"  # oturum düştü: ajan bir kez yeniden giriş yapar
    assert edge.execute(cfg, None, {"template": "logo_malzeme_bul", "params": {"kod": "RECT-ELT-01"}}, api)["id"] == 1001
    assert mod.STATE["issued"] == 2
    ro = edge.load_config(_cfg(tmp_path, url, allow_write=False))
    assert {t["name"] for t in edge.catalog(ro)} == {"logo_malzeme_bul", "logo_cari_bul"}  # yazma kapalıyken bildirilmez
    with pytest.raises(edge.TemplateError, match="allow_write"):
        edge.execute(ro, None, job, api)


def test_logo_material_transfer_via_edge(client, db, world, tmp_path, logo_rest, fake_extract, monkeypatch):
    edge = _agent_module()
    mod, url = logo_rest
    monkeypatch.setattr(settings, "WORKFLOW_ENABLED", False)
    w = world
    h = w["admin"]["h"]
    _seed(client)
    _seed_catalog(client)
    base = f"/api/v1/company/{w['tenant']}/integrations"
    conn = client.post(base, headers=h, json={"connector": "edge", "name": f"Logo {uuid.uuid4().hex[:4]}", "catalog_code": "logo"}).json()
    token = client.post(f"{base}/{conn['id']}/agent-token", headers=h).json()["token"]
    agent = edge.Agent(edge.load_config(_cfg(tmp_path, url)), "", token, client=client, wait=1)
    agent.poll_once()
    tools = {t["name"]: t["kind"] for t in client.get(f"{base}/{conn['id']}/tools", headers=h).json()}
    assert tools == {"logo_malzeme_bul": "READ", "logo_malzeme_ekle": "WRITE", "logo_malzeme_guncelle": "WRITE", "logo_cari_bul": "READ",
                     "logo_cari_ekle": "WRITE"}
    murl = f"/api/v1/company/{w['tenant']}/mappings"
    tpls = {t["code"]: t for t in client.get(f"{murl}/templates?connector=edge", headers=h).json()}
    assert {"logo_material", "logo_partner"} <= set(tpls)
    with Running(agent) as run:
        m = client.post(murl, headers=h, json={"connection_id": conn["id"], "object_type": "PRODUCT", "name": "Ürün → Logo",
                                               "template_id": tpls["logo_material"]["id"]}).json()
        assert "id" in m, m
        c = client.post(f"{murl}/{m['id']}/check", headers=h).json()
        assert c["ok"] is True, c
        d = client.post(f"{murl}/{m['id']}/dry-run", headers=h, json={}).json()
        assert d["ok"] and d["action"] == "CREATE" and d["values"]["birim_seti"] == "ADET" and d["values"]["kart_turu"] == 1
        assert client.post(f"{murl}/{m['id']}/approve", headers=h).status_code == 200

        pid, task_id = _project_with_done_step(client, db, w)
        client.post(f"/api/v1/tasks/{task_id}/transfers", headers=h, json={"mapping_id": m["id"]})
        rows = _wait(client, h, pid, lambda rs: len(rs) == 3 and all(x["status"] != "EXTRACTING" for x in rs), timeout=60)
        by = {(x["object"].get("code") or x["object"].get("name")): x for x in rows}
        svc = by["Kurulum hizmeti"]
        assert svc["status"] == "NEEDS_FIX" and any("SERVICE" in e for e in svc["problems"]["errors"])  # hizmet Logo'da ayrı kart
        elt = by["RECT-ELT-01"]
        assert elt["status"] == "PENDING_APPROVAL" and elt["action"] == "CREATE"
        client.post(f"/api/v1/transfers/{elt['id']}/decision", headers=h, json={"approve": True})
        rows = _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == elt["id"])["status"] in ("DONE", "FAILED"), timeout=60)
        done = next(x for x in rows if x["id"] == elt["id"])
        assert done["status"] == "DONE", done
        card = next(r for r in mod.STATE["items"].values() if r["CODE"] == "RECT-ELT-01")
        assert card["NAME"] == "El terminali" and card["UNITSET_CODE"] == "ADET" and card["VAT"] == 20 and done["external_id"] == str(card["INTERNAL_REFERENCE"])

        # Aynı stok koduyla ikinci aktarım: Logo'da aranır, güncelleme şablonuyla güncellenir (çift kart yok)
        client.post(f"/api/v1/tasks/{task_id}/transfers", headers=h, json={"mapping_id": m["id"]})
        rows = _wait(client, h, pid, lambda rs: len(rs) == 6 and all(x["status"] != "EXTRACTING" for x in rs), timeout=60)
        again = next(x for x in rows if x["object"].get("code") == "RECT-ELT-01" and x["status"] == "PENDING_APPROVAL")
        assert again["action"] == "UPDATE"
        client.post(f"/api/v1/transfers/{again['id']}/decision", headers=h, json={"approve": True})
        rows = _wait(client, h, pid, lambda rs: next(x for x in rs if x["id"] == again["id"])["status"] in ("DONE", "FAILED"), timeout=60)
        assert next(x for x in rows if x["id"] == again["id"])["status"] == "DONE"
        assert len([r for r in mod.STATE["items"].values() if r["CODE"] == "RECT-ELT-01"]) == 1
        # Geri alma bu sistemde desteklenmez: anlaşılır ret
        r = client.post(f"/api/v1/transfers/{again['id']}/rollback", headers=h)
        assert r.status_code == 409 and "desteklenmiyor" in r.json()["detail"]
        assert not run.errors
