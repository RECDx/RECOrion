"""
Senaryo Aşama 4, C4-22 (19.11.2026): paralel iki adım (Ziyaretçi arayüzü, Yönetim paneli) aynı dosyalara yazdı; ikincisi kendi
eski görüşüyle tam dosya yazınca birincinin ana dala birleşmiş onaylı özellikleri (mobil menü, süzgeç, rezervasyon penceresi)
silindi. Artık commit, adımın önceki sürümünü taban alıp üç yollu birleştirir; çakışan dosya yazılmaz. Depo bağlamında adımın
kendi dosyaları ve recorion.json önce ve tam verilir.
"""
import asyncio
import base64

from app.services import code_repo
from app.services.code_repo import merge3
from tests.test_workflow import world  # noqa: F401  (fikstür)

BASE = "<nav>\n<a>Anasayfa</a>\n</nav>\n<main>\n<p>turlar</p>\n</main>\n<footer>(c)</footer>\n"


def test_merge3_keeps_both_sides_when_changes_do_not_overlap():
    theirs = BASE.replace("<a>Anasayfa</a>\n", "<a>Anasayfa</a>\n<button class=\"hamburger\">≡</button>\n")  # başka adım: menü
    ours = BASE.replace("<footer>(c)</footer>\n", "<footer>(c) <a href=\"/admin\">Personel Girişi</a></footer>\n")  # bu adım
    text, n = merge3(BASE, ours, theirs)
    assert n == 0 and "hamburger" in text and "Personel Girişi" in text


def test_merge3_reports_conflict_on_same_lines():
    theirs = BASE.replace("<p>turlar</p>", "<p>turlar + süzgeç</p>")
    ours = BASE.replace("<p>turlar</p>", "<p>tur kartları</p>")
    text, n = merge3(BASE, ours, theirs)
    assert text is None and n == 1


def test_merge3_trivial_cases():
    ours = BASE + "<script>yeni</script>\n"
    assert merge3(BASE, ours, BASE) == (ours, 0)  # başka değişiklik yok → bu adımın sürümü
    assert merge3(BASE, BASE, ours) == (ours, 0)  # bu adım dokunmadı → daldaki hâl
    assert merge3(BASE, ours, ours) == (ours, 0)


class P:
    id, repo_owner, repo_name = "p1", "org", "repo"


class T:
    id, title, order_index, repo_branch, repo_pr_number = "t1", "Yönetim Paneli", 6, "adim-6-yonetim-paneli", 7


def _out(index_html, extra=""):
    return f"## Çıktı\n\n```html src/templates/index.html\n{index_html}```\n{extra}"


def test_commit_step_merges_or_skips_instead_of_overwriting(monkeypatch):
    """Dalda başka adımın (ana daldan gelen) değişikliği varsa adımın yeni tam dosyası onu silmez."""
    branch = {"src/templates/index.html": BASE.replace("<a>Anasayfa</a>\n", "<a>Anasayfa</a>\n<button class=\"hamburger\">≡</button>\n")}
    sent = {}

    async def exists(path):
        if path.endswith("/branches/adim-6-yonetim-paneli"):
            return {"name": "x"}
        for p, body in branch.items():
            if f"/contents/{p}?" in path:
                return {"sha": "s1", "content": base64.b64encode(body.encode()).decode()}
        return None

    async def call(method, path, json=None, ok=(200, 201, 204), params=None):
        if method == "POST" and path.endswith("/contents"):
            sent["files"] = {f["path"]: base64.b64decode(f["content"]).decode() for f in json["files"]}
            return 201, {"commit": {"sha": "c2"}}
        return 200, {}

    monkeypatch.setattr(code_repo, "_exists", exists)
    monkeypatch.setattr(code_repo, "_call", call)
    previous = _out(BASE)
    # Birleşebilir değişiklik: panel adımı alt bilgiye bağlantı ekledi → menü (başka adım) korunur
    ours = BASE.replace("<footer>(c)</footer>\n", "<footer>(c) <a href=\"/admin\">Personel Girişi</a></footer>\n")
    r = asyncio.run(code_repo.commit_step(P(), T(), 2, _out(ours), "Web Geliştirici", previous=previous))
    body = sent["files"]["src/templates/index.html"]
    assert r["merged"] == ["src/templates/index.html"] and r["conflicts"] == []
    assert "hamburger" in body and "Personel Girişi" in body

    # Çakışan değişiklik: aynı satır → dosya yazılmaz, daldaki (onaylı) hâl durur
    branch["src/templates/index.html"] = BASE.replace("<p>turlar</p>", "<p>turlar + süzgeç</p>")
    r = asyncio.run(code_repo.commit_step(P(), T(), 3, _out(BASE.replace("<p>turlar</p>", "<p>kartlar</p>")), "Web Geliştirici",
                                          previous=previous))
    assert r["conflicts"] == ["src/templates/index.html"] and "src/templates/index.html" not in sent["files"]
    assert any(p.startswith("docs/adimlar/") for p in sent["files"])  # adım dokümanı yine yazılır

    # Önceki sürüm yoksa (ilk sürüm) eski davranış: çıktı yazılır
    r = asyncio.run(code_repo.commit_step(P(), T(), 1, _out(ours), "Web Geliştirici"))
    assert r["conflicts"] == [] and sent["files"]["src/templates/index.html"] == ours


def test_context_for_ai_puts_priority_files_and_recorion_json_first_in_full(monkeypatch):
    files = {"src/app/main.py": "print('x')\n" * 50, "src/static/js/app.js": "a" * 20000,
             "src/templates/index.html": "<nav>" + "b" * 20000, "recorion.json": '{"checks": []}' + " " * 12000}

    async def tree(project, ref):
        return {"entries": [{"path": p, "type": "blob", "size": len(c)} for p, c in files.items()]}

    async def read_file(project, ref, path):
        return {"content": files[path]}

    monkeypatch.setattr(code_repo, "tree", tree)
    monkeypatch.setattr(code_repo, "read_file", read_file)
    out = asyncio.run(code_repo.context_for_ai(P(), priority=["src/templates/index.html"]))
    assert out.index("### src/templates/index.html") < out.index("### src/app/main.py")
    assert out.index("### recorion.json") < out.index("### src/app/main.py")
    assert "b" * 20000 in out  # öncelikli dosya kısaltılmadan
    assert "GÜNCEL hâlini temel al" in out


def test_shrinks_blocks_placeholder_replacing_existing_file(monkeypatch):
    """C4-25: bakım adımının ilk sürümü işleyen yönetim panelini "Panel içeriği burada yüklenecek" taslağıyla değiştirdi."""
    panel = "\n".join(f"function ekran{i}() {{ return {i}; }}" for i in range(40)) + "\n"
    stub = "<h2>Yönetim Paneli</h2>\n<p>Panel içeriği burada yüklenecek.</p>\n"
    assert code_repo.shrinks(panel, stub) is True
    assert code_repo.shrinks(panel, panel + "function yeni() {}\n") is False  # ekleme
    assert code_repo.shrinks("a\nb\n", "c\n") is False  # küçük dosya serbest
    branch = {"src/static/js/admin.js": panel}
    sent = {}

    async def exists(path):
        if "/branches/" in path:
            return {"name": "x"}
        for p, body in branch.items():
            if f"/contents/{p}?" in path:
                return {"sha": "s1", "content": base64.b64encode(body.encode()).decode()}
        return None

    async def call(method, path, json=None, ok=(200, 201, 204), params=None):
        if method == "POST" and path.endswith("/contents"):
            sent["files"] = {f["path"] for f in json["files"]}
            return 201, {"commit": {"sha": "c"}}
        return 200, {}

    monkeypatch.setattr(code_repo, "_exists", exists)
    monkeypatch.setattr(code_repo, "_call", call)
    out = f"```js src/static/js/admin.js\n{stub}```\n"
    r = asyncio.run(code_repo.commit_step(P(), T(), 1, out, "Web Geliştirici"))
    assert r["shrunk"] == ["src/static/js/admin.js"] and "src/static/js/admin.js" not in sent["files"]
    # adımın kendi önceki sürümü varsa (kendi dosyası) üç yollu birleştirme kuralı geçerli, küçültme engeli uygulanmaz
    r = asyncio.run(code_repo.commit_step(P(), T(), 2, out, "Web Geliştirici", previous=f"```js src/static/js/admin.js\n{panel}```\n"))
    assert r["shrunk"] == [] and "src/static/js/admin.js" in sent["files"]


def test_acceptance_gate_counts_runs_on_merged_step_branches(client, db, world, monkeypatch):  # noqa: F811
    """C4-25: insan kabul adımında 'uygulama hiç çalıştırılıp denenmedi' yanlış uyarısı — koşular birleşmiş adım dallarındaydı."""
    import uuid as _uuid

    from app.db.models import Project, Task
    from app.db.session import AsyncSessionLocal
    from app.services import sandbox
    from tests.test_workflow import _exec, _ready_project

    w = world
    pid, human_id, ai_id = _ready_project(client, w, f"Kapı {_uuid.uuid4().hex[:4]}")
    monkeypatch.setattr(sandbox, "enabled", lambda: True)
    monkeypatch.setattr(code_repo, "active", lambda project: True)
    ai_task = _exec(db, "SELECT id FROM tasks WHERE project_id = %s AND title = 'AI adımı'", pid)[0]
    human_task = _exec(db, "SELECT id FROM tasks WHERE project_id = %s AND id <> %s ORDER BY created_at LIMIT 1", pid, ai_task)[0]
    _exec(db, "UPDATE tasks SET status = 'DONE', repo_branch = 'adim-1-ai', repo_merged_at = now() WHERE id = %s", ai_task)
    _exec(db, "UPDATE tasks SET title = 'Kullanıcı kabul testi', repo_branch = NULL WHERE id = %s", human_task)

    async def gate():
        async with AsyncSessionLocal() as s:
            return await sandbox.acceptance_gate(s, await s.get(Project, pid), await s.get(Task, human_task))
    assert "hiç çalıştırılıp denenmedi" in client.portal.call(gate)
    _exec(db, "INSERT INTO test_runs (id, tenant_id, project_id, task_id, ref, status, passed, failed, skipped, result) "
              "SELECT gen_random_uuid(), tenant_id, id, %s, 'adim-1-ai', 'PASSED', 27, 0, 0, "
              "'{\"smoke\": {\"status\": \"PASSED\", \"checks\": []}}'::jsonb FROM projects WHERE id = %s", ai_task, pid)
    warn = client.portal.call(gate)
    assert warn is None or "hiç çalıştırılıp denenmedi" not in warn, warn
