"""
ADIM 8.5: Proje kod deposu (gerçek Gitea; EVREN sahte).

- Depoyu yalnızca proje yöneticisi açar; ekip görür, ekip dışı göremez.
- AI personelin çıktısı adımın dalına commit edilir: çıktı dokümanı + yolu belirtilmiş kod blokları; ana dala istek açılır.
- İnsan onayı ana dala birleştirmedir; onaydan önce main'de kod yoktur. Güvensiz dosya yolları commit edilmez.
"""
import json

import httpx
import pytest

from app.config import settings
from app.services import code_repo, storage
from app.services.evren_client import ChatResult, evren_client
from tests.test_workflow import _ready_project, _wait, world  # noqa: F401  (fikstür)

pytestmark = pytest.mark.skipif(not settings.GITEA_TOKEN, reason="GITEA_TOKEN yok (kod deposu sunucusu yapılandırılmamış)")

CODE = '''# Uygulama iskeleti

Aşağıdaki dosyalar depoya eklenecek.

```python src/app/main.py
def main():
    return "merhaba"
```

```text ../../etc/kacak.txt
güvensiz yol
```

```json config/ayarlar.json
{"port": 8080}
```
'''


@pytest.fixture
def coder(monkeypatch):
    objects = {}

    async def put_object(key, data, content_type=None):
        objects[key] = data

    async def get_object(key):
        return objects[key]

    async def chat(model_code, messages, **kw):
        if "kontrol personelisin" in messages[0]["content"]:
            return ChatResult(json.dumps({"passed": True, "score": 95, "issues": [], "summary": "Uygun"}), None, 100, 20, {})
        return ChatResult(CODE, None, 800, 300, {})
    monkeypatch.setattr(evren_client, "chat", chat)
    monkeypatch.setattr(storage, "put_object", put_object)
    monkeypatch.setattr(storage, "get_object", get_object)


def _gitea(method, path):
    return httpx.request(method, settings.GITEA_URL.rstrip("/") + "/api/v1" + path, headers={"Authorization": f"token {settings.GITEA_TOKEN}"}, timeout=30)


def test_files_from_output_rejects_unsafe_paths():
    class T:
        order_index, title = 2, "Geliştirme Adımı"
    files = code_repo.files_from_output(T(), CODE)
    assert set(files) == {"docs/adimlar/02-gelistirme-adimi.md", "src/app/main.py", "config/ayarlar.json"}
    assert files["src/app/main.py"].startswith("def main():")
    safe = code_repo._safe_path
    assert safe("./src/a.py") == "src/a.py" and safe("a\\b.py") == "a/b.py"
    for bad in ("../x.py", "src/../../x.py", "/etc/passwd", ".git/config", "src//a.py", "src/./a.py", ""):
        assert safe(bad) is None, bad


def test_repository_lifecycle(client, world, coder):
    w = world
    admin, member, outsider = w["admin"]["h"], w["member"]["h"], w["outsider"]["h"]
    pid, _, _ = _ready_project(client, w, "Kod Deposu Projesi")
    base = f"/api/v1/projects/{pid}/repository"
    owner = repo = None
    try:
        assert client.get(base, headers=admin).json()["mode"] == "NONE"
        assert client.put(base, headers=member, json={"mode": "RECORION"}).status_code == 403
        r = client.put(base, headers=admin, json={"mode": "RECORION"})
        assert r.status_code == 200, r.text
        info = r.json()
        assert info["mode"] == "RECORION" and info["url"].startswith(settings.GITEA_PUBLIC_URL)
        owner, repo = info["url"].rstrip("/").split("/")[-2:]
        assert _gitea("GET", f"/repos/{owner}/{repo}").json()["private"] is True
        assert client.put(base, headers=admin, json={"mode": "RECORION"}).status_code == 200  # tekrar açmak güvenli
        assert client.get(base, headers=outsider).status_code == 403

        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
        tasks, flow = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI adımı onaya gelmeli", 60)
        ai_id = tasks["AI adımı"]["id"]
        step = next(s for s in client.get(base, headers=member).json()["steps"] if s["task_id"] == ai_id)
        assert step["branch"] == "adim-1-ai-adimi" and step["pr"] and step["state"] == "OPEN"
        paths = {f["path"] for f in step["files"]}
        assert {"docs/adimlar/01-ai-adimi.md", "src/app/main.py", "config/ayarlar.json"} <= paths
        assert not any("kacak" in p for p in paths)
        assert any(e["kind"] == "REPO_COMMIT" for e in flow["events"] if e["task_id"] == ai_id)

        # Dosya okuma: dalda var, main'de henüz yok (birleştirme onayla olur)
        f = client.get(f"{base}/file", headers=member, params={"ref": step["branch"], "path": "src/app/main.py"})
        assert f.status_code == 200 and "def main" in f.json()["content"]
        assert client.get(f"{base}/file", headers=member, params={"ref": "main", "path": "src/app/main.py"}).status_code == 404
        assert client.get(f"{base}/file", headers=member, params={"ref": "main", "path": "../x"}).status_code == 422

        # Onay = ana dala birleştirme
        assert client.post(f"/api/v1/tasks/{ai_id}/decision", headers=admin, json={"approve": True}).status_code == 200
        _wait(client, admin, pid, lambda t, f: any(e["kind"] == "REPO_MERGED" and e["task_id"] == ai_id for e in f["events"]),
              "onaydan sonra ana dala birleştirilmeli", 45)
        step = next(s for s in client.get(base, headers=admin).json()["steps"] if s["task_id"] == ai_id)
        assert step["state"] == "MERGED" and step["merged_at"]
        assert "def main" in client.get(f"{base}/file", headers=member, params={"ref": "main", "path": "src/app/main.py"}).json()["content"]
        assert client.post(f"{base}/steps/{ai_id}/merge", headers=member).status_code == 403
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
        if owner and repo:
            _gitea("DELETE", f"/repos/{owner}/{repo}")
            if not _gitea("GET", f"/orgs/{owner}/repos").json():
                _gitea("DELETE", f"/orgs/{owner}")


def _gitea_json(method, path, body):
    return httpx.request(method, settings.GITEA_URL.rstrip("/") + "/api/v1" + path, json=body,
                         headers={"Authorization": f"token {settings.GITEA_TOKEN}"}, timeout=30)


def test_repository_mirror_to_company_account(client, world):
    """ADIM 10.3 (#297): proje deposu şirketin Gitea/GitHub hesabına yansıtılır (gerçek Gitea; hedef aynı sunucuda ayrı depo)."""
    import time
    import uuid as _uuid

    w = world
    admin, member = w["admin"]["h"], w["member"]["h"]
    pid, _, _ = _ready_project(client, w, "Yansıtma Projesi")
    base = f"/api/v1/projects/{pid}/repository"
    org = f"ct-ayna-{_uuid.uuid4().hex[:6]}"
    ig = f"/api/v1/company/{w['tenant']}/integrations"
    owner = repo = cid = None
    try:
        info = client.put(base, headers=admin, json={"mode": "RECORION"}).json()
        owner, repo = info["url"].rstrip("/").split("/")[-2:]
        assert _gitea_json("POST", "/orgs", {"username": org, "visibility": "private"}).status_code == 201
        assert _gitea_json("POST", f"/orgs/{org}/repos", {"name": "hedef", "private": True}).status_code == 201
        me = _gitea("GET", "/user").json()["login"]
        r = client.post(ig, headers=admin, json={"connector": "gitea", "name": "Şirket Gitea",
                                                 "config": {"base_url": settings.GITEA_URL, "username": me},
                                                 "secrets": {"token": settings.GITEA_TOKEN}})
        assert r.status_code == 201, r.text
        cid = r.json()["id"]

        assert client.get(f"{base}/mirror-targets", headers=member).status_code == 403
        targets = client.get(f"{base}/mirror-targets", headers=admin).json()
        assert [t["id"] for t in targets] == [cid] and set(targets[0]) == {"id", "name", "connector"}  # ayar/kimlik yok
        assert client.put(f"{base}/mirror", headers=member, json={"connection_id": cid, "repo": f"{org}/hedef"}).status_code == 403
        assert client.put(f"{base}/mirror", headers=admin, json={"connection_id": cid, "repo": "gecersiz"}).status_code == 422
        r = client.put(f"{base}/mirror", headers=admin, json={"connection_id": cid, "repo": f"{org}/hedef"})
        assert r.status_code == 200, r.text
        m = r.json()["mirror"]
        assert m["repo"] == f"{org}/hedef" and settings.GITEA_TOKEN not in json.dumps(r.json())
        for _ in range(20):  # ilk gönderim hemen tetiklenir
            if _gitea("GET", f"/repos/{org}/hedef/branches").json():
                break
            time.sleep(1)
        assert [b["name"] for b in _gitea("GET", f"/repos/{org}/hedef/branches").json()] == ["main"]
        assert client.get(base, headers=member).json()["mirror"]["repo"] == f"{org}/hedef"  # ekip durumu görür

        # Bağlantı devre dışı bırakılınca yansıtma Gitea'dan kaldırılır (eski token'la gönderim sürmez)
        assert client.put(f"{ig}/{cid}", headers=admin, json={"status": "DISABLED"}).status_code == 200
        assert _gitea("GET", f"/repos/{owner}/{repo}/push_mirrors").json() == []
        assert client.get(base, headers=admin).json()["mirror"] is None
        assert client.put(f"{base}/mirror", headers=admin, json={"connection_id": cid, "repo": f"{org}/hedef"}).status_code == 404
    finally:
        if cid:  # kasadaki gerçek token test kaydında kalmasın
            client.put(f"{ig}/{cid}", headers=admin, json={"status": "DISABLED", "secrets": {"token": "silindi"}})
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
        _gitea("DELETE", f"/repos/{org}/hedef")
        _gitea("DELETE", f"/orgs/{org}")
        if owner and repo:
            _gitea("DELETE", f"/repos/{owner}/{repo}")
            if not _gitea("GET", f"/orgs/{owner}/repos").json():
                _gitea("DELETE", f"/orgs/{owner}")
