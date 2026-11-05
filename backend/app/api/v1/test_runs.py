"""
Kod Çalıştırma Ortamı uçları (ADIM 16.2, #610).

- GET  /projects/{id}/test-runs            ekip: son koşular (dal, sonuç, geçen/kalan, kalan testler, kayıt sonları)
- GET  /projects/{id}/test-runs/{run_id}   ekip: tek koşu
- POST /projects/{id}/test-runs            proje yöneticisi: seçilen dalda testleri elle çalıştır (arka planda; koşu RUNNING döner)
"""
import re
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import Project, TestRun
from app.db.session import AsyncSessionLocal, get_db
from app.services import code_repo, sandbox
from app.services import projects as psvc

router = APIRouter(prefix="/projects", tags=["Proje Test Koşuları"])


@router.get("/{project_id}/test-runs")
async def list_runs(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    rows = (await db.execute(select(TestRun).where(TestRun.project_id == project.id).order_by(TestRun.created_at.desc()).limit(30))).scalars().all()
    return {"enabled": sandbox.enabled() and code_repo.active(project), "runs": [sandbox.view(r) for r in rows],
            "can_run": user.has("project:manage") or project.manager_actor_id == user.actor_id}


@router.get("/{project_id}/test-runs/{run_id}")
async def get_run(project_id: uuid.UUID, run_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    run = await db.get(TestRun, run_id)
    if not run or run.project_id != project.id:
        raise HTTPException(status_code=404, detail="Test koşusu bulunamadı.")
    return sandbox.view(run)


class RunIn(BaseModel):
    ref: str = Field("main", min_length=1, max_length=120)


async def _background(project_id, run_id):
    async with AsyncSessionLocal() as db:
        project, run = await db.get(Project, project_id), await db.get(TestRun, run_id)
        await sandbox.finish(db, project, run)
        await db.commit()


@router.post("/{project_id}/test-runs")
async def start_run(project_id: uuid.UUID, payload: RunIn, background: BackgroundTasks, user: CurrentUser = Depends(get_current_user),
                    db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    if not re.fullmatch(r"[\w./-]{1,120}", payload.ref) or ".." in payload.ref:
        raise HTTPException(status_code=422, detail="Geçersiz dal adı.")
    if not sandbox.enabled():
        raise HTTPException(status_code=503, detail="Kod çalıştırma ortamı bu kurulumda yapılandırılmamış; RECDx ile iletişime geçin.")
    if not code_repo.active(project):
        raise HTTPException(status_code=409, detail="Önce projenin kod deposunu açın.")
    busy = (await db.execute(select(TestRun.id).where(TestRun.project_id == project.id, TestRun.status == "RUNNING"))).first()
    if busy:
        raise HTTPException(status_code=409, detail="Bu projede süren bir test koşusu var; bitmesini bekleyin.")
    run = await sandbox.start(db, project, payload.ref, user.actor_id)
    await db.commit()
    background.add_task(_background, project.id, run.id)
    return sandbox.view(run)
