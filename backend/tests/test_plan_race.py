"""
Plan önerisi uzun sürerken proje iptal edilirse öneri, iptal durumunun üzerine yazmaz (e2e751'de MCP Case'i iptalden sonra
PLANNING'e döndü).
"""
import json
import uuid

from tests.test_workflow import _exec, _ready_project, world  # noqa: F401  (fikstür)


def test_plan_suggest_does_not_overwrite_cancelled_project(client, db, world, monkeypatch):
    from app.services.evren_client import ChatResult, evren_client

    w = world
    h = w["admin"]["h"]
    pid, _, _ = _ready_project(client, w, f"Yarış {uuid.uuid4().hex[:4]}")
    _exec(db, "UPDATE projects SET status = 'DRAFT', plan = NULL, settings = %s WHERE id = %s",
          json.dumps({"discovery": {"status": "SKIPPED", "skipped_reason": "test"}}), pid)

    async def chat(model_code, messages, **kw):
        _exec(db, "UPDATE projects SET status = 'CANCELLED' WHERE id = %s", pid)  # LLM yanıt verirken iptal edildi
        out = {"summary": "plan", "steps": [{"key": "S1", "title": "İnceleme", "description": "x", "acceptance_criteria": "rapor",
                                              "department": "", "job_title": "Analist", "agent_id": "", "estimated_days": 1, "depends_on": []}],
               "hire_suggestions": [], "risks": [], "questions": []}
        return ChatResult(json.dumps(out, ensure_ascii=False), None, 100, 50, {})
    monkeypatch.setattr(evren_client, "chat", chat)

    r = client.post(f"/api/v1/projects/{pid}/plan/suggest", headers=h, json={})
    assert r.status_code == 409, r.text
    status, plan = _exec(db, "SELECT status, plan FROM projects WHERE id = %s", pid)
    assert status == "CANCELLED" and plan is None
