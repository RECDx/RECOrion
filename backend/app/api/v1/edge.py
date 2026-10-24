"""
Edge Connector uçları (ADIM 10.5).

Ajan (müşteri sunucusu; kimlik = ajan anahtarı, kullanıcı girişi yok):
- POST /edge/poll                 yoklama: ajan bilgisi + şablon kataloğu bildirilir; kuyruktaki işler alınır (uzun yoklama)
- POST /edge/jobs/{job_id}/result işin sonucu
Şirket yöneticisi (integration:manage):
- POST /company/{tid}/integrations/{cid}/agent-token   yeni ajan anahtarı (bir kez gösterilir; eskisi geçersizleşir)
"""
import asyncio
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser, get_current_user
from app.db.models import EdgeJob, IntegrationConnection
from app.db.session import AsyncSessionLocal, get_db
from app.integrations import edge as edge_connector
from app.integrations.base import clip

router = APIRouter(tags=["Edge Connector"])

MAX_WAIT = 25
BATCH = 5
QUEUE_TTL = timedelta(seconds=60)  # bu süreden eski, alınmamış iş süresi dolmuş sayılır (araç çağrısı zaten beklemeyi bıraktı)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def _agent(db: AsyncSession, edge_token: Optional[str]) -> IntegrationConnection:
    token = (edge_token or "").strip()
    if len(token) < 32:
        raise HTTPException(status_code=401, detail="Ajan anahtarı geçersiz.")
    conn = (await db.execute(select(IntegrationConnection).where(
        IntegrationConnection.agent_token_hash == token_hash(token), IntegrationConnection.connector == "edge"))).scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=401, detail="Ajan anahtarı geçersiz.")
    if conn.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Bu Edge bağlantısı devre dışı.")
    return conn


class PollIn(BaseModel):
    version: str = Field("", max_length=40)
    hostname: str = Field("", max_length=120)
    templates: List[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    wait: int = Field(MAX_WAIT, ge=0, le=MAX_WAIT)


async def _claim(cid: uuid.UUID) -> List[Dict[str, Any]]:
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        await db.execute(update(EdgeJob).where(EdgeJob.connection_id == cid, EdgeJob.status == "QUEUED",
                                               EdgeJob.created_at < now - QUEUE_TTL)
                         .values(status="EXPIRED", error="Ajan zamanında almadı", done_at=now))
        jobs = (await db.execute(select(EdgeJob).where(EdgeJob.connection_id == cid, EdgeJob.status == "QUEUED")
                                 .order_by(EdgeJob.created_at).limit(BATCH).with_for_update(skip_locked=True))).scalars().all()
        for j in jobs:
            j.status, j.picked_at = "RUNNING", now
        await db.commit()
        return [{"id": str(j.id), "template": j.template, "params": j.params} for j in jobs]


@router.post("/edge/poll")
async def poll(payload: PollIn, x_recorion_edge_token: Optional[str] = Header(None), db: AsyncSession = Depends(get_db)):
    conn = await _agent(db, x_recorion_edge_token)
    conn.agent_seen_at = datetime.now(timezone.utc)
    conn.agent_info = {"version": payload.version, "hostname": payload.hostname,
                       "templates": edge_connector.clean_catalog(payload.templates)}
    await db.commit()
    cid = conn.id
    deadline = asyncio.get_running_loop().time() + payload.wait
    while True:
        jobs = await _claim(cid)
        if jobs or asyncio.get_running_loop().time() >= deadline:
            return {"jobs": jobs, "next_poll_seconds": 1 if jobs else 0}
        await asyncio.sleep(0.5)


class ResultIn(BaseModel):
    ok: bool
    result: Optional[Any] = None
    error: Optional[str] = Field(None, max_length=2000)


@router.post("/edge/jobs/{job_id}/result")
async def job_result(job_id: uuid.UUID, payload: ResultIn, x_recorion_edge_token: Optional[str] = Header(None),
                     db: AsyncSession = Depends(get_db)):
    conn = await _agent(db, x_recorion_edge_token)
    job = await db.get(EdgeJob, job_id)
    if not job or job.connection_id != conn.id:  # başka bağlantının işi: varlığı da sızdırılmaz
        raise HTTPException(status_code=404, detail="İş bulunamadı.")
    if job.status != "RUNNING":
        raise HTTPException(status_code=409, detail="Bu iş artık sonuç beklemiyor.")
    job.status = "DONE" if payload.ok else "FAILED"
    job.result = clip(payload.result) if payload.ok else None
    job.error = None if payload.ok else (payload.error or "Hata")
    job.done_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": job.status}


@router.post("/company/{tenant_id}/integrations/{cid}/agent-token")
async def new_agent_token(tenant_id: uuid.UUID, cid: uuid.UUID, user: CurrentUser = Depends(get_current_user),
                          db: AsyncSession = Depends(get_db)):
    from app.api.v1.integrations import _conn

    conn = await _conn(db, user, tenant_id, cid)
    if conn.connector != "edge":
        raise HTTPException(status_code=409, detail="Ajan anahtarı yalnızca Edge Connector bağlantısında üretilir.")
    token = "rxe_" + secrets.token_urlsafe(32)
    conn.agent_token_hash, conn.agent_seen_at = token_hash(token), None  # eski anahtar geçersiz; ajan yeni anahtarla bağlanınca çevrimiçi
    await db.commit()
    return {"token": token, "note": "Bu anahtar bir daha gösterilmez. Müşteri sunucusundaki ajanın RECORION_EDGE_TOKEN ayarına girin."}
