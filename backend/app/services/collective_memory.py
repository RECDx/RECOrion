import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from app.config import settings
from app.services.evren_gateway import evren_gateway

logger = logging.getLogger("collective_memory")


class CollectiveMemoryService:
    """
    2 Kademeli Kolektif Hafıza Servisi (Qdrant & PostgreSQL):
    1. AI Personelleri Hafızası (NS_AGENT): Her ajanın kendi uzmanlık dokümanları ve tecrübeleri.
    2. Şirket Kurum Hafızası (NS_GLOBAL): Şirketteki tüm AI personellerinin hafıza ve know-how toplamı.
    """

    def __init__(self):
        self.client = AsyncQdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, check_compatibility=False)
        self.collection_name = settings.QDRANT_COLLECTION_NAME

    async def add_memory(
        self,
        tenant_id: str,
        scope: str,  # 'GLOBAL' veya 'AGENT'
        content: str,
        agent_id: Optional[str] = None,
        source_reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Hafızaya yeni bir bilgi maddesi ekler ve vektörize eder.
        """
        assert scope in ["GLOBAL", "AGENT"], "Scope yalnızca 'GLOBAL' veya 'AGENT' olabilir."
        if scope == "AGENT":
            assert agent_id is not None, "Ajan hafızası için agent_id zorunludur."

        point_id = str(uuid.uuid4())
        metadata = metadata or {}

        # 1. Embedding üret (Qwen3-Embedding-8b)
        vector = await evren_gateway.create_embedding(content)

        payload = {
            "tenant_id": str(tenant_id),
            "scope": scope,
            "agent_id": str(agent_id) if agent_id else None,
            "source_reference": source_reference,
            "content": content,
            "metadata": metadata
        }

        # 2. Qdrant'a yaz
        try:
            await self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=vector,
                        payload=payload
                    )
                ]
            )
            logger.info(f"Hafıza noktası Qdrant'a eklendi: {point_id} (Scope: {scope})")
        except Exception as e:
            logger.error(f"Qdrant ekleme hatası: {e}")

        return {
            "point_id": point_id,
            "tenant_id": tenant_id,
            "scope": scope,
            "agent_id": agent_id,
            "content": content,
            "source_reference": source_reference
        }

    async def search_memory(
        self,
        tenant_id: str,
        query: str,
        assigned_agent_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        2 Kademeli RAG Arama:
        - Zorunlu olarak tenant_id filtresi uygulanır.
        - Şirket Kurum Hafızası (NS_GLOBAL) VE (varsa) görevli ajanın hafızası (NS_AGENT) taranır.
        """
        query_vector = await evren_gateway.create_embedding(query)

        # Qdrant Filtreleri
        must_conditions: List[Any] = [
            qmodels.FieldCondition(key="tenant_id", match=qmodels.MatchValue(value=str(tenant_id)))
        ]

        # Scope filtresi: GLOBAL olanlar HER ZAMAN dahil; AGENT ise sadece bu ajana ait olanlar dahil
        if assigned_agent_id:
            should_conditions = [
                qmodels.FieldCondition(key="scope", match=qmodels.MatchValue(value="GLOBAL")),
                qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(key="scope", match=qmodels.MatchValue(value="AGENT")),
                        qmodels.FieldCondition(key="agent_id", match=qmodels.MatchValue(value=str(assigned_agent_id)))
                    ]
                )
            ]
            filter_query = qmodels.Filter(must=must_conditions, should=should_conditions)
        else:
            # Sadece Kurumsal Hafıza
            must_conditions.append(qmodels.FieldCondition(key="scope", match=qmodels.MatchValue(value="GLOBAL")))
            filter_query = qmodels.Filter(must=must_conditions)

        try:
            # Modern qdrant-client query_points API
            response = await self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                query_filter=filter_query,
                limit=limit * 2  # Rerank için 2 kat aday topla
            )
            results = response.points

            hits = []
            doc_texts = []
            for hit in results:
                payload = hit.payload or {}
                hits.append({
                    "id": str(hit.id),
                    "score": hit.score,
                    "scope": payload.get("scope"),
                    "source": payload.get("source_reference"),
                    "content": payload.get("content", ""),
                    "agent_id": payload.get("agent_id")
                })
                doc_texts.append(payload.get("content", ""))

            # Qwen3-Reranker-8b ile en iyi sonuçları sırala
            if doc_texts:
                reranked = await evren_gateway.rerank(query, doc_texts, top_n=limit)
                ordered_hits = []
                for item in reranked:
                    idx = item["index"]
                    if idx < len(hits):
                        hit_copy = hits[idx]
                        hit_copy["rerank_score"] = item["relevance_score"]
                        ordered_hits.append(hit_copy)
                return ordered_hits

            return hits[:limit]
        except Exception as e:
            logger.error(f"Qdrant hafıza arama hatası: {e}")
            return []


collective_memory = CollectiveMemoryService()
