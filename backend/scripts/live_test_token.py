"""
Canlı e2e testi için onay bağlantısı belirteci (e-postadakiyle aynı tür). Yalnızca "recorion_canli_test" şirketinin
iş adımları için çalışır; gerçek müşteri şirketlerinde reddeder.

Kullanım: docker exec -w /app recorion_backend python scripts/live_test_token.py <task_id>
Çıktı: tek satır belirteç (ekrana basılmaz; test süreci bellekte kullanır).
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.models import Project, Task, Tenant  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.services import approvals  # noqa: E402


async def main(task_id: str) -> None:
    async with AsyncSessionLocal() as db:
        task = await db.get(Task, uuid.UUID(task_id))
        project = await db.get(Project, task.project_id) if task else None
        tenant = await db.get(Tenant, project.tenant_id) if project else None
        if not tenant or tenant.slug != "recorion_canli_test":
            raise SystemExit("Yalnızca canlı test şirketinin iş adımları için belirteç üretilebilir.")
        raw, _ = await approvals.create(db, task, task.approver_actor_id or project.manager_actor_id, "EMAIL")
        await db.commit()
        print(raw)


asyncio.run(main(sys.argv[1]))
