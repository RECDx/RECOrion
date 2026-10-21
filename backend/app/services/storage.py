"""
MinIO nesne deposu (öğrenme dokümanları). minio istemcisi eşzamanlı çalıştığı için çağrılar iş parçacığında yapılır.
Anahtar düzeni: {tenant_id | platform}/{katman}/{sahip_id}/{doküman_id}/{dosya_adı}
"""
import asyncio
import io
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger("recorion.storage")


class StorageError(Exception):
    pass


_client = None
_bucket_ready = False


def _get_client():
    global _client
    if _client is None:
        from minio import Minio

        _client = Minio(settings.MINIO_ENDPOINT, access_key=settings.MINIO_ROOT_USER,
                        secret_key=settings.MINIO_ROOT_PASSWORD, secure=settings.MINIO_USE_SSL)
    return _client


def _ensure_bucket(client) -> None:
    global _bucket_ready
    if not _bucket_ready:
        if not client.bucket_exists(settings.MINIO_DOCUMENTS_BUCKET):
            client.make_bucket(settings.MINIO_DOCUMENTS_BUCKET)
        _bucket_ready = True


def _put(key: str, data: bytes, content_type: str) -> None:
    client = _get_client()
    _ensure_bucket(client)
    client.put_object(settings.MINIO_DOCUMENTS_BUCKET, key, io.BytesIO(data), len(data), content_type=content_type)


def _get(key: str) -> bytes:
    resp = _get_client().get_object(settings.MINIO_DOCUMENTS_BUCKET, key)
    try:
        return resp.read()
    finally:
        resp.close()
        resp.release_conn()


def _delete(key: str) -> None:
    _get_client().remove_object(settings.MINIO_DOCUMENTS_BUCKET, key)


async def put_object(key: str, data: bytes, content_type: Optional[str] = None) -> None:
    try:
        await asyncio.to_thread(_put, key, data, content_type or "application/octet-stream")
    except Exception as exc:
        logger.error("MinIO yazma hatası (%s): %s", key, exc)
        raise StorageError("Dosya depoya kaydedilemedi.") from exc


async def get_object(key: str) -> bytes:
    try:
        return await asyncio.to_thread(_get, key)
    except Exception as exc:
        logger.error("MinIO okuma hatası (%s): %s", key, exc)
        raise StorageError("Dosya depodan okunamadı.") from exc


async def delete_object(key: str) -> None:
    try:
        await asyncio.to_thread(_delete, key)
    except Exception as exc:  # silinemeyen nesne kaydı bozmaz; loglanır
        logger.warning("MinIO silme hatası (%s): %s", key, exc)
