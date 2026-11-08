"""Senaryo F98 (08.11.2026): AI personel depodaki gerçek kodu görür (önce uygulama kodu, sonra testler; sınır içinde)."""
import asyncio

from app.services import code_repo


class P:
    id, repo_owner, repo_name = "p1", "org", "repo"


def test_context_for_ai_orders_code_first_and_respects_limit(monkeypatch):
    files = {
        "src/main.py": "@app.post('/token')\ndef login(): ...\n",
        "tests/test_api.py": "def test_x(): ...\n",
        "requirements.txt": "fastapi\nbcrypt==4.0.1\n",
        "docs/adimlar/01-analiz.md": "uzun doküman",
        "web/logo.png": "ikili",
        "src/big.py": "x" * 20000,
    }

    async def tree(project, ref):
        return {"entries": [{"path": p, "type": "blob", "size": len(c)} for p, c in files.items()] + [{"path": "src", "type": "tree", "size": 0}]}

    async def read_file(project, ref, path):
        return {"content": files[path]}

    monkeypatch.setattr(code_repo, "tree", tree)
    monkeypatch.setattr(code_repo, "read_file", read_file)
    out = asyncio.run(code_repo.context_for_ai(P(), limit=30000))
    assert "# Depodaki kod (dal: main)" in out and "- docs/adimlar/01-analiz.md" in out  # listede var
    assert "### src/main.py" in out and "/token" in out and "### requirements.txt" in out and "### tests/test_api.py" in out
    assert "uzun doküman" not in out and "ikili" not in out  # docs/ ve ikili dosya içeriği girmez
    assert out.index("### src/main.py") < out.index("### tests/test_api.py")  # önce uygulama kodu
    assert "(dosyanın devamı kısaltıldı)" in out  # büyük dosya kısaltıldı
    small = asyncio.run(code_repo.context_for_ai(P(), limit=400))
    assert len(small) < 1200 and "### src/big.py" not in small


def test_context_for_ai_survives_repo_errors(monkeypatch):
    async def tree(project, ref):
        raise RuntimeError("gitea kapalı")

    monkeypatch.setattr(code_repo, "tree", tree)
    assert asyncio.run(code_repo.context_for_ai(P())) == ""
