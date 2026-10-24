"""
ADIM 10.5: Edge Connector — gerçek ajan kodu (edge_agent/recorion_edge.py) ile RECOrion geçidi birlikte, sahte Logo veritabanıyla.

- Ajan anahtarı yalnızca şirket yöneticisinde; bir kez gösterilir, özet saklanır; yenisi eskisini geçersiz kılar.
- Ajan yalnızca dışa bağlanır (yoklama); kataloğu bildirir (SQL gitmez); yazma kapalıyken yazma şablonu hiç görünmez.
- Okuma aracı: iş kuyruğa → ajan alır → sahte Logo'da şablon → sonuç; parametre hatası anlaşılır döner.
- Yazma (allow_write): AI personel çağırınca insan onayı; onaydan sonra ajan çalıştırır.
- Yanlış anahtar 401, devre dışı bağlantı 403, başka bağlantının işi 404, çevrimdışı ajan anlaşılır hata.
"""
import importlib.util
import json
import sys
import threading
import uuid
from pathlib import Path

import pytest

from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)

AGENT_DIR = Path("/edge_agent")
pytestmark = pytest.mark.skipif(not (AGENT_DIR / "recorion_edge.py").exists(), reason="edge_agent bağlı değil")


def _agent_module():
    spec = importlib.util.spec_from_file_location("recorion_edge", AGENT_DIR / "recorion_edge.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["recorion_edge"] = mod
    spec.loader.exec_module(mod)
    return mod


def _fake_logo(tmp_path: Path) -> Path:
    spec = importlib.util.spec_from_file_location("fake_logo", AGENT_DIR / "fake_logo.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    db = tmp_path / "sahte_logo.db"
    mod.build(str(db))
    return db


def _config(tmp_path: Path, allow_write: bool) -> Path:
    cfg = tmp_path / f"edge_config_{int(allow_write)}.json"
    cfg.write_text(json.dumps({"hostname": "LOGO-TEST", "database": {"driver": "sqlite", "path": str(_fake_logo(tmp_path))},
                               "templates_file": str(AGENT_DIR / "templates.example.json"), "allow_write": allow_write,
                               "audit_log": str(tmp_path / "audit.log")}), encoding="utf-8")
    return cfg


class Running:
    """Ajanı ayrı iş parçacığında sürekli yoklatır (gerçek kurulumdaki run_forever gibi)."""

    def __init__(self, agent):
        self.agent, self.stop, self.errors = agent, threading.Event(), []
        self.t = threading.Thread(target=self.loop, daemon=True)

    def loop(self):
        while not self.stop.is_set():
            try:
                self.agent.poll_once()
            except BaseException as exc:  # noqa: BLE001 (test sırasında görünür olsun)
                self.errors.append(exc)
                return

    def __enter__(self):
        self.t.start()
        return self

    def __exit__(self, *a):
        self.stop.set()
        self.t.join(timeout=10)


def test_edge_connector_end_to_end(client, db, world, tmp_path):
    edge = _agent_module()
    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    base = f"/api/v1/company/{w['tenant']}/integrations"
    conn = client.post(base, headers=admin, json={"connector": "edge", "name": f"Logo {uuid.uuid4().hex[:4]}"}).json()
    cid = conn["id"]
    assert conn["agent"] == {"has_token": False, "online": False, "seen_at": None, "hostname": None, "version": None, "templates": 0}
    assert client.post(f"{base}/{cid}/agent-token", headers=member).status_code == 403
    r = client.post(f"{base}/{cid}/agent-token", headers=admin)
    token = r.json()["token"]
    assert token.startswith("rxe_") and len(token) > 40
    assert token not in json.dumps(client.get(base, headers=admin).json())  # liste anahtarı döndürmez
    stored = _exec(db, "SELECT agent_token_hash FROM integration_connections WHERE id = %s", cid)[0]
    assert stored != token and len(stored) == 64
    t = client.post(f"{base}/{cid}/test", headers=admin).json()
    assert t["ok"] is False and "henüz bağlanmadı" in t["detail"]

    # Yanlış anahtar reddedilir
    bad = edge.Agent(edge.load_config(_config(tmp_path, False)), "", "rxe_" + "x" * 40, client=client, wait=0)
    with pytest.raises(SystemExit, match="401"):
        bad.poll_once()

    agent = edge.Agent(edge.load_config(_config(tmp_path, False)), "", token, client=client, wait=1)
    assert agent.poll_once() == 0
    info = next(c for c in client.get(base, headers=admin).json() if c["id"] == cid)["agent"]
    assert info["online"] and info["hostname"] == "LOGO-TEST" and info["templates"] == 4  # yazma şablonu bildirilmedi
    tools = client.get(f"{base}/{cid}/tools", headers=admin).json()
    assert {x["name"] for x in tools} == {"cari_ara", "cari_bakiye", "cari_hareketleri", "stok_miktari"}
    assert all(x["kind"] == "READ" for x in tools)
    assert "SELECT" not in json.dumps(tools)  # SQL RECOrion'a hiç gelmedi
    assert "LOGO-TEST" in client.post(f"{base}/{cid}/test", headers=admin).json()["detail"]

    with Running(agent) as run:
        r = client.post(f"{base}/{cid}/try", headers=admin, json={"tool": "cari_bakiye", "arguments": {"cari_kodu": "120.01.001"}}).json()
        assert r["status"] == "EXECUTED", r
        assert r["result"]["rows"] == [["120.01.001", "ABC Makine Sanayi Ltd. Şti.", 103500.5]]
        r = client.post(f"{base}/{cid}/try", headers=admin, json={"tool": "cari_bakiye", "arguments": {"cari_kodu": "x' OR '1'='1"}}).json()
        assert r["status"] == "EXECUTED" and r["result"]["row_count"] == 0  # parametre bağlanır, enjeksiyon yok
        r = client.post(f"{base}/{cid}/try", headers=admin,
                        json={"tool": "cari_hareketleri", "arguments": {"cari_kodu": "120.01.001", "baslangic": "dün"}}).json()
        assert r["status"] == "FAILED" and "YYYY-AA-GG" in r["error"]
        assert not run.errors
    audit = (tmp_path / "audit.log").read_text(encoding="utf-8").splitlines()
    assert len(audit) == 3 and "ABC Makine" not in "".join(audit)  # denetim kaydı sonuç verisini yazmaz

    # Başka bağlantının işine sonuç yazılamaz
    other = client.post(base, headers=admin, json={"connector": "edge", "name": f"Mikro {uuid.uuid4().hex[:4]}"}).json()
    other_token = client.post(f"{base}/{other['id']}/agent-token", headers=admin).json()["token"]
    job = _exec(db, "SELECT id FROM edge_jobs WHERE connection_id = %s LIMIT 1", cid)[0]
    r = client.post(f"/api/v1/edge/jobs/{job}/result", headers={"X-RECOrion-Edge-Token": other_token}, json={"ok": True, "result": {}})
    assert r.status_code == 404

    # Ajan çevrimdışı: anlaşılır hata, iş beklemeden döner
    _exec(db, "UPDATE integration_connections SET agent_seen_at = now() - interval '10 minutes' WHERE id = %s", cid)
    r = client.post(f"{base}/{cid}/try", headers=admin, json={"tool": "stok_miktari", "arguments": {"stok_kodu": "STK-001"}}).json()
    assert r["status"] == "FAILED" and "çevrimdışı" in r["error"]

    # Yeni anahtar eskisini geçersiz kılar; devre dışı bağlantı yoklayamaz
    new_token = client.post(f"{base}/{cid}/agent-token", headers=admin).json()["token"]
    with pytest.raises(SystemExit, match="401"):
        agent.poll_once()
    assert client.put(f"{base}/{cid}", headers=admin, json={"status": "DISABLED"}).status_code == 200
    with pytest.raises(SystemExit, match="403"):
        edge.Agent(edge.load_config(_config(tmp_path, False)), "", new_token, client=client, wait=0).poll_once()


def test_edge_write_template_needs_human_approval(client, db, world, tmp_path):
    from app.db.models import Actor, Project
    from app.db.session import AsyncSessionLocal
    from app.services import tool_gateway

    edge = _agent_module()
    w = world
    admin = w["admin"]["h"]
    base = f"/api/v1/company/{w['tenant']}/integrations"
    cid = client.post(base, headers=admin, json={"connector": "edge", "name": f"Logo yazma {uuid.uuid4().hex[:4]}"}).json()["id"]
    token = client.post(f"{base}/{cid}/agent-token", headers=admin).json()["token"]
    cfg_path = _config(tmp_path, True)
    agent = edge.Agent(edge.load_config(cfg_path), "", token, client=client, wait=1)
    agent.poll_once()
    kinds = {x["name"]: x["kind"] for x in client.get(f"{base}/{cid}/tools", headers=admin).json()}
    assert kinds["cari_not_ekle"] == "WRITE"
    assert client.post(f"{base}/{cid}/try", headers=admin, json={"tool": "cari_not_ekle", "arguments": {}}).status_code == 409
    assert client.put(f"{base}/{cid}/grants", headers=admin, json={"grants": [{"actor_id": w["agent"], "tool": "*"}]}).status_code == 200
    pid, _, _ = _ready_project(client, w, "Logo Not Projesi")

    async def call(name, args):
        async with AsyncSessionLocal() as s:
            ai = await s.get(Actor, uuid.UUID(w["agent"]))
            items = await tool_gateway.available(s, ai)
            fn = next(tool_gateway.fn_name(c, t.name) for c, t in items if str(c.id) == cid and t.name == name)
            c = await tool_gateway.invoke(s, ai, fn, args, project=await s.get(Project, uuid.UUID(pid)))
            await s.commit()
            return tool_gateway.call_out(c)

    pending = client.portal.call(call, "cari_not_ekle", {"cari_kodu": "120.01.001", "not_metni": "Vade görüşmesi yapıldı"})
    assert pending["status"] == "PENDING_APPROVAL"
    import sqlite3
    logo = json.loads(cfg_path.read_text())["database"]["path"]
    assert sqlite3.connect(logo).execute("SELECT COUNT(*) FROM RECORION_NOTLAR").fetchone()[0] == 0  # onaysız yazılmadı
    with Running(agent):
        done = client.post(f"/api/v1/tool-calls/{pending['id']}/decision", headers=admin, json={"approve": True}).json()
    assert done["status"] == "EXECUTED" and done["result"] == {"affected_rows": 1}
    assert sqlite3.connect(logo).execute("SELECT CARI_KODU, NOT_ FROM RECORION_NOTLAR").fetchall() == [("120.01.001", "Vade görüşmesi yapıldı")]
