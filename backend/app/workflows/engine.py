"""
Temporal bağlantısı, worker ve akış komutları (ADIM 7.1).

Worker backend sürecinde arka plan görevi olarak çalışır (WORKFLOW_ENABLED). API, akışları buradaki
fonksiyonlarla başlatır ve sinyal gönderir.
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError
from temporalio.worker import Worker

from app.config import settings
from app.workflows import activities
from app.workflows.definitions import ProjectWorkflow, TaskWorkflow, project_workflow_id, task_workflow_id

logger = logging.getLogger("recorion.workflow")

_client: Optional[Client] = None
_lock = asyncio.Lock()
UNAVAILABLE = "İş akışı motoruna şu an ulaşılamıyor; lütfen biraz sonra tekrar deneyin."


async def client() -> Client:
    global _client
    async with _lock:
        if _client is None:
            _client = await Client.connect(f"{settings.TEMPORAL_HOST}:{settings.TEMPORAL_PORT}", namespace=settings.TEMPORAL_NAMESPACE)
        return _client


async def run_worker() -> None:
    """Temporal'a bağlanana kadar dener, sonra worker'ı çalıştırır."""
    global _client
    delay = 2
    while True:
        try:
            c = await client()
            logger.info("İş akışı worker'ı başladı (kuyruk: %s).", settings.TEMPORAL_TASK_QUEUE)
            await Worker(c, task_queue=settings.TEMPORAL_TASK_QUEUE, workflows=[ProjectWorkflow, TaskWorkflow],
                         activities=activities.ALL).run()
            return
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            _client = None
            logger.warning("İş akışı motoruna bağlanılamadı (%s); %s sn sonra tekrar denenecek.", exc, delay)
            await asyncio.sleep(delay)
            delay = min(delay * 2, 60)


async def start_project(project_id: str, actor_id: str) -> str:
    wid = project_workflow_id(project_id)
    try:
        c = await client()
        await c.start_workflow(ProjectWorkflow.run, args=[project_id, actor_id], id=wid, task_queue=settings.TEMPORAL_TASK_QUEUE,
                               id_reuse_policy=WorkflowIDReusePolicy.ALLOW_DUPLICATE)
    except WorkflowAlreadyStartedError:
        pass
    except (RPCError, OSError, RuntimeError) as exc:
        logger.error("Proje akışı başlatılamadı: %s", exc)
        raise HTTPException(status_code=503, detail=UNAVAILABLE) from exc
    return wid


async def _signal(workflow_id: str, name: str, payload: Optional[Dict[str, Any]] = None, ignore_closed: bool = False) -> None:
    """ignore_closed: akış zaten bitmişse (ör. tüm adımlar tamamlandıktan sonra proje kapatılırken) sessizce geç."""
    try:
        handle = (await client()).get_workflow_handle(workflow_id)
        if payload is None:
            await handle.signal(name)
        else:
            await handle.signal(name, payload)
    except RPCError as exc:
        if ignore_closed and ("already completed" in str(exc).lower() or "not found" in str(exc).lower()):
            return
        logger.error("Akış sinyali gönderilemedi (%s %s): %s", workflow_id, name, exc)
        raise HTTPException(status_code=409 if "not found" in str(exc).lower() else 503,
                            detail="Bu iş adımının akışı bulunamadı; proje başlatılmamış olabilir." if "not found" in str(exc).lower() else UNAVAILABLE) from exc
    except (OSError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=UNAVAILABLE) from exc


async def signal_project(project_id: str, name: str, payload: Optional[Dict[str, Any]] = None) -> None:
    # Proje akışı tüm adımlar kapanınca kendiliğinden biter; sonraki duraklat/kapat komutları akışa iletilmez
    await _signal(project_workflow_id(project_id), name, payload, ignore_closed=True)


async def signal_task(task_id: str, name: str, payload: Dict[str, Any]) -> None:
    await _signal(task_workflow_id(task_id), name, payload)
