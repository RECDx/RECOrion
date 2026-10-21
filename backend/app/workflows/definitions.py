"""
Temporal akış tanımları (ADIM 7.1). Akış kodu deterministik olmalıdır: veritabanı, saat ve ağ işleri yalnızca
aktivitelerde (activities.py) yapılır.

ProjectWorkflow ("project-<id>"): bağımlılıkları kapanan iş adımları için TaskWorkflow başlatır; tüm adımlar
  kapanınca yöneticiye bildirir. Sinyaller: pause, resume, cancel, refresh.
TaskWorkflow ("task-<id>"): çalışma > teslim > (onay gerekiyorsa) onay/ret döngüsü; ret sınırında karantina.
  Sinyaller: submit, decide, release, cancel.
"""
import asyncio
from datetime import timedelta
from typing import Any, Dict, Optional, Set

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from app.workflows import activities as act

OPTS = {"start_to_close_timeout": timedelta(minutes=2),
        "retry_policy": RetryPolicy(initial_interval=timedelta(seconds=2), maximum_interval=timedelta(minutes=1), maximum_attempts=0)}


def task_workflow_id(task_id: str) -> str:
    return f"task-{task_id}"


def project_workflow_id(project_id: str) -> str:
    return f"project-{project_id}"


@workflow.defn(name="TaskWorkflow")
class TaskWorkflow:
    def __init__(self) -> None:
        self.submitted: Optional[Dict[str, Any]] = None
        self.decision: Optional[Dict[str, Any]] = None
        self.released: Optional[Dict[str, Any]] = None
        self.cancelled: Optional[Dict[str, Any]] = None

    @workflow.signal
    def submit(self, payload: Dict[str, Any]) -> None:
        self.submitted = payload

    @workflow.signal
    def decide(self, payload: Dict[str, Any]) -> None:
        self.decision = payload

    @workflow.signal
    def release(self, payload: Dict[str, Any]) -> None:
        self.released = payload

    @workflow.signal
    def cancel(self, payload: Dict[str, Any]) -> None:
        self.cancelled = payload or {}

    async def _wait(self, attr: str) -> Optional[Dict[str, Any]]:
        """Sinyal veya iptal gelene kadar bekler; iptalde None döner."""
        await workflow.wait_condition(lambda: getattr(self, attr) is not None or self.cancelled is not None)
        if self.cancelled is not None:
            return None
        value = getattr(self, attr)
        setattr(self, attr, None)
        return value

    async def _cancel(self, task_id: str) -> str:
        await workflow.execute_activity(act.cancel_task, args=[task_id, self.cancelled or {}], **OPTS)
        return "CANCELLED"

    @workflow.run
    async def run(self, task_id: str) -> str:
        await workflow.execute_activity(act.start_task, task_id, **OPTS)
        while True:
            # Çalışma: insan personel teslim eder; AI personelin otomatik çalışması ADIM 7.2'de bu noktaya eklenir
            work = await self._wait("submitted")
            if work is None:
                return await self._cancel(task_id)
            result = await workflow.execute_activity(act.submit_task, args=[task_id, work], **OPTS)
            if result["status"] == "DONE":
                return "DONE"
            decision = await self._wait("decision")
            if decision is None:
                return await self._cancel(task_id)
            if decision.get("approve"):
                await workflow.execute_activity(act.approve_task, args=[task_id, decision], **OPTS)
                return "DONE"
            result = await workflow.execute_activity(act.reject_task, args=[task_id, decision], **OPTS)
            if result["quarantined"]:
                choice = await self._wait("released")
                if choice is None:
                    return await self._cancel(task_id)
                await workflow.execute_activity(act.release_task, args=[task_id, choice], **OPTS)
                if choice.get("action") == "cancel":
                    return "CANCELLED"


@workflow.defn(name="ProjectWorkflow")
class ProjectWorkflow:
    def __init__(self) -> None:
        self.paused = False
        self.cancelled: Optional[Dict[str, Any]] = None
        self.dirty = False
        self.running: Dict[str, Any] = {}
        self.finished: Set[str] = set()

    @workflow.signal
    def pause(self) -> None:
        self.paused = True

    @workflow.signal
    def resume(self) -> None:
        self.paused, self.dirty = False, True

    @workflow.signal
    def refresh(self) -> None:
        self.dirty = True

    @workflow.signal
    def cancel(self, payload: Dict[str, Any]) -> None:
        self.cancelled = payload or {}

    async def _child(self, task_id: str) -> None:
        try:
            await workflow.execute_child_workflow(TaskWorkflow.run, task_id, id=task_workflow_id(task_id))
        finally:
            self.finished.add(task_id)

    @workflow.run
    async def run(self, project_id: str, actor_id: str = "") -> str:
        await workflow.execute_activity(act.project_started, args=[project_id, actor_id], **OPTS)
        while True:
            for tid in list(self.finished):
                self.running.pop(tid, None)
            self.finished.clear()
            if self.cancelled is not None:
                for tid in list(self.running):
                    await workflow.get_external_workflow_handle(task_workflow_id(tid)).signal(TaskWorkflow.cancel, self.cancelled)
                if self.running:
                    await asyncio.gather(*self.running.values(), return_exceptions=True)
                await workflow.execute_activity(act.cancel_remaining, args=[project_id, self.cancelled], **OPTS)
                return "CANCELLED"
            if not self.paused:
                state = await workflow.execute_activity(act.next_ready_tasks, args=[project_id, list(self.running)], **OPTS)
                for tid in state["ready"]:
                    self.running[tid] = asyncio.create_task(self._child(tid))
                if not self.running and state["remaining"] == 0:
                    await workflow.execute_activity(act.project_finished, project_id, **OPTS)
                    return "FINISHED"
            self.dirty = False
            await workflow.wait_condition(lambda: self.dirty or bool(self.finished) or self.cancelled is not None)
