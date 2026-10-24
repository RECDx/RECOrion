"""
Proje şablonları (ADIM 11.1).

- Şablon = plan iskeleti: adımlar, roller (unvan/departman), süreler, bağımlılıklar, onay ayarları, şema konumu, riskler.
  Kişi kimliği (AI/insan personel, kontrol personeli, onaylayıcı), çıktı, ek ve yazışma şablona GİRMEZ.
- Şirket şablonu yalnızca o şirkette görünür (KVKK: RECDx göremez). RECDx platform şablonları tüm şirketlere açıktır;
  başlangıç seti app/seed/project_templates.json (açılışta yalnızca eksik kodlar eklenir; Süper Admin düzenlemesi korunur).
- Şablondan proje: plan TASLAK olarak gelir; unvanı uyan AI personel otomatik eşleşir; proje yöneticisi inceleyip onaylar.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, ProjectTemplate
from app.services import project_planning as planning

logger = logging.getLogger("recorion.templates")

SEED_FILE = Path(__file__).resolve().parent.parent / "seed" / "project_templates.json"
PERSON_KEYS = ("agent_id", "reviewer_agent_id", "approver_actor_id")


def skeleton(plan: Dict[str, Any], keep_descriptions: bool = True) -> Dict[str, Any]:
    """Planı şablon iskeletine çevirir: doğrular, kişi kimliklerini ve projeye özgü alanları atar."""
    clean = planning.validate_plan(plan or {}, pool_ids=set(), human_ids=None)
    steps = []
    for s in clean["steps"]:
        s = {k: v for k, v in s.items() if k not in PERSON_KEYS}
        if not keep_descriptions:
            s["description"], s["acceptance_criteria"] = "", ""
        steps.append(s)
    return {"summary": clean["summary"] if keep_descriptions else "", "steps": steps, "risks": clean["risks"]}


def total_days(plan: Dict[str, Any]) -> float:
    """Kritik yol (bağımlılıklar boyunca en uzun süre), iş günü."""
    steps = {s["key"]: s for s in (plan or {}).get("steps") or []}
    memo: Dict[str, float] = {}

    def finish(k: str) -> float:
        if k not in memo:
            s = steps[k]
            memo[k] = float(s.get("estimated_days") or 1) + max((finish(d) for d in s.get("depends_on") or [] if d in steps), default=0)
        return memo[k]
    return round(max((finish(k) for k in steps), default=0), 1)


def out(t: ProjectTemplate, full: bool = False) -> Dict[str, Any]:
    plan = t.plan or {}
    d = {"id": str(t.id), "scope": "PLATFORM" if t.tenant_id is None else "COMPANY", "name": t.name, "description": t.description,
         "category": t.category, "kind": t.kind, "field_package": t.field_package, "status": t.status, "use_count": t.use_count,
         "step_count": len(plan.get("steps") or []), "total_days": total_days(plan),
         "roles": sorted({s["job_title"] for s in plan.get("steps") or [] if s.get("job_title")}),
         "created_at": t.created_at, "updated_at": t.updated_at}
    if full:
        d["plan"] = plan
    return d


async def apply(db: AsyncSession, template: ProjectTemplate, project: Project) -> Dict[str, Any]:
    """Şablon planını projeye taslak olarak koyar; unvanı uyan AI personeli eşleştirir (iş yükü en az olan)."""
    pool = await planning._team_pool(db, project.tenant_id)
    by_title: Dict[str, list] = {}
    for a in pool:
        if a.get("title"):
            by_title.setdefault(a["title"].strip().lower(), []).append(a)
    steps, matched = [], 0
    for s in (template.plan or {}).get("steps") or []:
        cands = sorted(by_title.get((s.get("job_title") or "").strip().lower(), []), key=lambda a: a["open_tasks_elsewhere"])
        s = {**s, "agent_id": cands[0]["agent_id"] if cands else None}
        matched += bool(cands)
        steps.append(s)
    plan = planning.validate_plan({**template.plan, "steps": steps}, {a["agent_id"] for a in pool}, human_ids=set())
    unmatched = sorted({s["job_title"] for s in plan["steps"] if not s.get("agent_id") and s.get("job_title")})
    plan["hire_suggestions"] = [{"job_title": t, "department": None, "reason": f"'{template.name}' şablonundaki rol şirkette yok."}
                                for t in unmatched][:10]
    project.plan = {**plan, "approved": False, "from_template": {"id": str(template.id), "name": template.name}}
    project.template_id = template.id
    template.use_count = (template.use_count or 0) + 1
    return {"matched_steps": matched, "unmatched_roles": unmatched}


async def ensure_platform_templates(db: AsyncSession, path: Path = SEED_FILE) -> int:
    """Tohum dosyasındaki platform şablonlarından eksik olanları ekler (var olana dokunulmaz)."""
    if not path.exists():
        return 0
    have = set((await db.execute(select(ProjectTemplate.code).where(ProjectTemplate.code.isnot(None)))).scalars())
    added = 0
    for t in json.loads(path.read_text(encoding="utf-8")):
        if t["code"] in have:
            continue
        db.add(ProjectTemplate(tenant_id=None, code=t["code"], name=t["name"], description=t.get("description"),
                               category=t.get("category"), kind=t.get("kind", "PROJECT"), field_package=t.get("field_package", "GENEL"),
                               plan=skeleton(t["plan"])))
        added += 1
    await db.commit()
    return added


def visible(user, template: Optional[ProjectTemplate]) -> bool:
    """Platform şablonu herkese; şirket şablonu yalnızca kendi şirketine (RECDx personeli dahil değil: KVKK)."""
    if not template:
        return False
    if template.tenant_id is None:
        return True
    return template.tenant_id == user.tenant_id and not user.is_platform_staff
