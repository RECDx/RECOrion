"""
4 katmanlı bilgi + proje ekleri (ADIM 5.5, Odoo #274).

Bir AI personel soru aldığında şu katmanlar birlikte aranır (Qdrant, tek sorgu + yeniden sıralama):
  PROJECT         Proje Ekleri          yalnızca o projede görülür; proje kapanınca onaylananlar Kurum Hafızasına aktarılır
  AGENT           AI Personel Bilgisi   personelin kendi dokümanları ve öğrendikleri
  TITLE           Şirket Unvan Bilgisi  şirketin bu unvan için verdiği bilgiler (o unvandaki tüm personel)
  GLOBAL          Kurum Hafızası        şirketin tüm AI personelinin ortak bilgisi
  PLATFORM_TITLE  Platform Unvan Bilgisi RECOrion kataloğundaki genel mesleki bilgi (tüm müşterilere açık)

KVKK: şirket katmanları yalnızca o şirketin tenant_id'si ile, platform katmanı yalnızca "PLATFORM" ile eşleşir;
bir şirketin bilgisi başka şirkete veya platform katmanına karışmaz.
"""
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from qdrant_client.http import models as qm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Actor, JobTitle
from app.services import llm_gateway
from app.services.llm_gateway import LLMContext, LLMError

logger = logging.getLogger("recorion.knowledge")

LABELS = {
    "PROJECT": "Proje Ekleri", "AGENT": "AI Personel Bilgisi", "TITLE": "Şirket Unvan Bilgisi",
    "GLOBAL": "Kurum Hafızası", "PLATFORM_TITLE": "Platform Unvan Bilgisi",
}
PRIORITY = ["PROJECT", "AGENT", "TITLE", "GLOBAL", "PLATFORM_TITLE"]


@dataclass
class Scope:
    """Aramanın kapsamı: hangi şirket, hangi personel/unvan/proje."""
    tenant_id: uuid.UUID
    agent_id: Optional[uuid.UUID] = None
    company_title_id: Optional[uuid.UUID] = None
    platform_title_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None


async def scope_for_agent(db: AsyncSession, tenant_id: uuid.UUID, agent_id: Optional[uuid.UUID],
                          project_id: Optional[uuid.UUID] = None) -> Scope:
    """AI personelin unvanından şirket ve platform unvan katmanlarını çözer."""
    scope = Scope(tenant_id=tenant_id, agent_id=agent_id, project_id=project_id)
    if agent_id:
        agent = await db.get(Actor, agent_id)
        if agent and agent.tenant_id == tenant_id and agent.job_title_id:
            title = await db.get(JobTitle, agent.job_title_id)
            if title and title.tenant_id == tenant_id:
                scope.company_title_id = title.id
                scope.platform_title_id = title.source_title_id
            elif title and title.tenant_id is None:  # eski kayıtlar: doğrudan katalog unvanı
                scope.platform_title_id = title.id
    return scope


def _match(key: str, value) -> qm.FieldCondition:
    return qm.FieldCondition(key=key, match=qm.MatchValue(value=str(value)))


def build_filter(scope: Scope, layers: Optional[List[str]] = None) -> qm.Filter:
    tenant = _match("tenant_id", scope.tenant_id)
    wanted = set(layers or PRIORITY)
    branches = []
    if "GLOBAL" in wanted:
        branches.append(qm.Filter(must=[tenant, _match("scope", "GLOBAL")]))
    if "AGENT" in wanted and scope.agent_id:
        branches.append(qm.Filter(must=[tenant, _match("scope", "AGENT"), _match("agent_id", scope.agent_id)]))
    if "TITLE" in wanted and scope.company_title_id:
        branches.append(qm.Filter(must=[tenant, _match("scope", "TITLE"), _match("job_title_id", scope.company_title_id)]))
    if "PROJECT" in wanted and scope.project_id:
        branches.append(qm.Filter(must=[tenant, _match("scope", "PROJECT"), _match("project_id", scope.project_id)]))
    if "PLATFORM_TITLE" in wanted and scope.platform_title_id:
        branches.append(qm.Filter(must=[_match("tenant_id", "PLATFORM"), _match("scope", "PLATFORM_TITLE"),
                                        _match("job_title_id", scope.platform_title_id)]))
    return qm.Filter(should=branches)


async def retrieve(scope: Scope, query: str, limit: int = 6, layers: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Katmanlardan en ilgili parçaları döner: [{layer, label, content, source, document_id, score}]."""
    from app.services.collective_memory import collective_memory

    try:
        vector = await llm_gateway.embed(LLMContext(tenant_id=scope.tenant_id, actor_id=scope.agent_id), query)
    except LLMError as exc:
        logger.warning("Bilgi araması yapılamadı (vektörleme): %s", exc)
        return []
    try:
        resp = await collective_memory.client.query_points(
            collection_name=collective_memory.collection_name, query=vector,
            query_filter=build_filter(scope, layers), limit=limit * 3,
        )
    except Exception as exc:
        logger.error("Qdrant bilgi araması hatası: %s", exc)
        return []

    hits = []
    for p in resp.points:
        pl = p.payload or {}
        layer = pl.get("scope") or "GLOBAL"
        hits.append({"layer": layer, "label": LABELS.get(layer, layer), "content": pl.get("content", ""),
                     "source": pl.get("source_reference"), "document_id": pl.get("document_id"), "score": p.score})
    if len(hits) > limit:
        try:
            ranked = await llm_gateway.rerank(LLMContext(tenant_id=scope.tenant_id), query, [h["content"] for h in hits], top_n=limit)
            hits = [dict(hits[r["index"]], rerank_score=r.get("relevance_score")) for r in ranked if r.get("index", -1) < len(hits)]
        except LLMError as exc:
            logger.warning("Yeniden sıralama yapılamadı, vektör sırası kullanılıyor: %s", exc)
            hits = hits[:limit]
    return hits


def format_context(hits: List[Dict[str, Any]], max_chars: int = 9000) -> str:
    """Modele verilecek bilgi bölümü: katmanlara göre gruplu, kaynak adıyla."""
    if not hits:
        return ""
    out, used = ["\n\n# Bilgi kaynakların (önce şirkete ve projeye özel olanlar)"], 0
    for layer in PRIORITY:
        items = [h for h in hits if h["layer"] == layer]
        if not items:
            continue
        out.append(f"\n## {LABELS[layer]}")
        for h in items:
            text = h["content"].strip()
            if used + len(text) > max_chars:
                text = text[:max(0, max_chars - used)]
            if not text:
                break
            used += len(text)
            out.append(f"- [{h.get('source') or 'kaynak'}] {text}")
    out.append("\nBu bilgileri kullan ve hangi kaynağa dayandığını belirt. Şirkete/projeye özel bilgi platform bilgisiyle "
               "çelişirse şirkete özel olanı esas al. Bilgi yoksa uydurma, eksikliği söyle.")
    return "\n".join(out)


def layer_counts(hits: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for h in hits:
        counts[h["layer"]] = counts.get(h["layer"], 0) + 1
    return counts
