import json
import logging
from typing import Optional, Dict, Any
import redis.asyncio as aioredis
from app.config import settings

logger = logging.getLogger("redis_stream")


class RedisStreamService:
    """
    Redis 7 Streams ve Pub/Sub Servisi:
    Canlı Düşünce Akışı (Live Reasoning Stream), WebSockets ve olay bildirimleri.
    """

    def __init__(self):
        self.redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        self.client: Optional[aioredis.Redis] = None

    async def get_client(self) -> aioredis.Redis:
        if self.client is None:
            self.client = aioredis.from_url(
                self.redis_url,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True
            )
        return self.client

    async def publish_thought(self, task_id: str, step: str, thought_text: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Work Area orta panelinde anlık "Düşünce Adımı" (Reasoning) yayınlar.
        """
        try:
            client = await self.get_client()
            channel = f"task:thought:{task_id}"
            message = {
                "task_id": str(task_id),
                "step": step,
                "thought": thought_text,
                "metadata": metadata or {}
            }
            await client.publish(channel, json.dumps(message))
        except Exception as e:
            logger.warning(f"Redis düşünce yayınlama hatası: {e}")

    async def publish_chat_token(self, task_id: str, token: str):
        """
        Daktilo efekti için anlık token parçasını yayınlar.
        """
        try:
            client = await self.get_client()
            channel = f"task:stream:{task_id}"
            await client.publish(channel, token)
        except Exception as e:
            logger.warning(f"Redis token yayınlama hatası: {e}")


redis_stream = RedisStreamService()
