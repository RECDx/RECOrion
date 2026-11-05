"""
ADIM 16.1 (#609): Kod Gezgini — proje ekibi depoyu salt okuma gezer (gerçek Gitea; EVREN sahte).

- Dallar: main önce; AI adımının dalı görev başlığıyla eşlenir.
- Dosya ağacı, zip arşivi, dosya adı + içerik araması; adımın fark görünümü için ayrıldığı nokta (base_sha) ve son hâli (head_sha).
- Ekip dışı göremez; geçersiz dal 422, olmayan dal 404; deposu olmayan proje 404.
"""
import io
import zipfile

import httpx
import pytest

from app.config import settings
from tests.test_code_repo import coder  # noqa: F401  (fikstür)
from tests.test_workflow import _ready_project, _wait, world  # noqa: F401  (fikstür)

pytestmark = pytest.mark.skipif(not settings.GITEA_TOKEN, reason="GITEA_TOKEN yok (kod deposu sunucusu yapılandırılmamış)")


def _gitea(method, path):
    return httpx.request(method, settings.GITEA_URL.rstrip("/") + "/api/v1" + path, headers={"Authorization": f"token {settings.GITEA_TOKEN}"}, timeout=30)


def test_code_explorer(client, world, coder):  # noqa: F811
    w = world
    admin, member, outsider = w["admin"]["h"], w["member"]["h"], w["outsider"]["h"]
    pid, _, _ = _ready_project(client, w, "Kod Gezgini Projesi")
    base = f"/api/v1/projects/{pid}/repository"
    owner = repo = None
    try:
        assert client.get(f"{base}/tree", headers=member).status_code == 404  # depo yok
        info = client.put(base, headers=admin, json={"mode": "RECORION"}).json()
        owner, repo = info["url"].rstrip("/").split("/")[-2:]
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "start"})
        tasks, _ = _wait(client, admin, pid, lambda t, f: t["AI adımı"]["status"] == "WAITING_APPROVAL", "AI adımı onaya gelmeli", 60)
        ai_id = tasks["AI adımı"]["id"]

        # Dallar: main önce, adım dalı görev başlığıyla
        refs = client.get(f"{base}/refs", headers=member).json()
        assert refs[0]["name"] == "main" and refs[0]["sha"]
        step_ref = next(r for r in refs if r["task_id"] == ai_id)
        assert step_ref["name"] == "adim-1-ai-adimi" and step_ref["task_title"] == "AI adımı"

        # Ağaç: dalda kod var, main'de yalnız README
        t = client.get(f"{base}/tree", headers=member, params={"ref": step_ref["name"]}).json()
        paths = {e["path"]: e["type"] for e in t["entries"]}
        assert paths.get("src/app/main.py") == "blob" and paths.get("src") == "tree" and not t["truncated"]
        assert "src/app/main.py" not in {e["path"] for e in client.get(f"{base}/tree", headers=member).json()["entries"]}

        # Arama: dosya adı + içerik (büyük/küçük harf duyarsız), satır numarasıyla
        s = client.get(f"{base}/search", headers=member, params={"ref": step_ref["name"], "q": "MERHABA"}).json()
        assert {"path": "src/app/main.py", "line": 2, "text": 'return "merhaba"'} in s["matches"]
        assert "config/ayarlar.json" in client.get(f"{base}/search", headers=member, params={"ref": step_ref["name"], "q": "ayarlar"}).json()["files"]
        assert client.get(f"{base}/search", headers=member, params={"q": "a"}).status_code == 422

        # Zip arşivi
        z = client.get(f"{base}/archive", headers=member, params={"ref": step_ref["name"]})
        assert z.status_code == 200 and z.headers["content-type"] == "application/zip" and "attachment" in z.headers["content-disposition"]
        names = zipfile.ZipFile(io.BytesIO(z.content)).namelist()
        assert any(n.endswith("src/app/main.py") for n in names)

        # Fark görünümü: adımın ayrıldığı nokta (main'de dosya yok) ve dalın son hâli
        step = next(s for s in client.get(base, headers=member).json()["steps"] if s["task_id"] == ai_id)
        assert step["base_sha"] and step["head_sha"] and step["base_sha"] != step["head_sha"]
        assert client.get(f"{base}/file", headers=member, params={"ref": step["base_sha"], "path": "src/app/main.py"}).status_code == 404
        assert "def main" in client.get(f"{base}/file", headers=member, params={"ref": step["head_sha"], "path": "src/app/main.py"}).json()["content"]

        # Yetki ve doğrulama
        for ep in ("refs", "tree", "archive"):
            assert client.get(f"{base}/{ep}", headers=outsider).status_code == 403, ep
        assert client.get(f"{base}/search", headers=outsider, params={"q": "main"}).status_code == 403
        assert client.get(f"{base}/tree", headers=member, params={"ref": "../main"}).status_code == 422
        assert client.get(f"{base}/tree", headers=member, params={"ref": "yok-boyle-dal"}).status_code == 404
    finally:
        client.post(f"/api/v1/projects/{pid}/status", headers=admin, json={"action": "cancel"})
        if owner and repo:
            _gitea("DELETE", f"/repos/{owner}/{repo}")
            if not _gitea("GET", f"/orgs/{owner}/repos").json():
                _gitea("DELETE", f"/orgs/{owner}")
