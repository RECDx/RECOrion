"""
Proje kod deposu uçları (ADIM 8.5).

- GET  /projects/{id}/repository                       ekip: depo adresi, adımların dalı, birleştirme isteği durumu ve dosyaları
- PUT  /projects/{id}/repository                       proje yöneticisi: depoyu aç (RECORION) / kullanma (NONE)
- GET  /projects/{id}/repository/file?ref=&path=       ekip: dosya içeriği (dal veya main)
- POST /projects/{id}/repository/steps/{task_id}/merge proje yöneticisi: onay gerektirmeyen/birleşemeyen adımı birleştir
"""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import Task
from app.db.session import get_db
from app.services import code_repo, task_flow
from app.services import projects as psvc
from app.services.code_repo import RepoError

router = APIRouter(prefix="/projects", tags=["Proje Kod Deposu"])


def _fail(exc: RepoError):
    raise HTTPException(status_code=503 if exc.status >= 500 or exc.status == 503 else 502, detail=exc.message)


async def _tasks(db: AsyncSession, project_id):
    return (await db.execute(select(Task).where(Task.project_id == project_id).order_by(Task.order_index))).scalars().all()


@router.get("/{project_id}/repository")
async def get_repository(project_id: uuid.UUID, user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    out = await code_repo.overview(project, await _tasks(db, project.id))
    out["can_manage"] = user.has("project:manage") or project.manager_actor_id == user.actor_id
    return out


class RepoModeIn(BaseModel):
    mode: Literal["NONE", "RECORION"]


@router.put("/{project_id}/repository")
async def set_repository(project_id: uuid.UUID, payload: RepoModeIn, user: CurrentUser = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    if project.status in ("COMPLETED", "CANCELLED"):
        raise HTTPException(status_code=409, detail="Kapanmış projenin depo ayarı değiştirilemez.")
    if payload.mode == "RECORION":
        if not code_repo.enabled():
            raise HTTPException(status_code=503, detail="Kod deposu sunucusu yapılandırılmamış; RECDx ile iletişime geçin.")
        try:
            await code_repo.enable(db, project)
        except RepoError as exc:
            _fail(exc)
        await task_flow.log(db, project, None, "REPO_ENABLED", user.actor_id, project.repo_url)
    else:
        # Depo silinmez (kayıt ve geçmiş korunur); yeni çıktılar artık commit edilmez
        project.repo_mode = "NONE"
    await db.commit()
    return await code_repo.overview(project, await _tasks(db, project.id))


@router.get("/{project_id}/repository/file")
async def repository_file(project_id: uuid.UUID, path: str = Query(..., max_length=200), ref: str = Query("main", max_length=120),
                          user: CurrentUser = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id)
    if not code_repo.active(project) and not (project.repo_owner and project.repo_name):
        raise HTTPException(status_code=404, detail="Bu projenin kod deposu yok.")
    try:
        return await code_repo.read_file(project, ref, path)
    except RepoError as exc:
        _fail(exc)


@router.post("/{project_id}/repository/steps/{task_id}/merge")
async def merge_step(project_id: uuid.UUID, task_id: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                     db: AsyncSession = Depends(get_db)):
    project = await psvc.load(db, user, project_id, manage=True)
    task = await db.get(Task, task_id)
    if not task or task.project_id != project.id:
        raise HTTPException(status_code=404, detail="İş adımı bulunamadı.")
    if task.status != "DONE":
        raise HTTPException(status_code=409, detail="Yalnızca tamamlanmış adım ana dala birleştirilebilir.")
    if not task.repo_pr_number:
        raise HTTPException(status_code=409, detail="Bu adımın birleştirilecek değişikliği yok.")
    try:
        r = await code_repo.merge_step(project, task, user.actor.display_name)
    except RepoError as exc:
        _fail(exc)
    await task_flow.log(db, project, task, "REPO_MERGED", user.actor_id, f"#{task.repo_pr_number} yönetici tarafından ana dala birleştirildi.", r)
    await db.commit()
    return r
