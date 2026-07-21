import asyncio
import logging
from io import BytesIO
from datetime import timedelta

from minio import Minio

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _get_client() -> Minio:
    client = await asyncio.wait_for(
        asyncio.to_thread(
            Minio,
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        ),
        timeout=settings.SERVICE_TIMEOUT,
    )
    return client


async def read(object_key: str) -> bytes:
    client = await _get_client()
    try:
        response = await asyncio.to_thread(
            client.get_object, settings.MINIO_BUCKET_NAME, object_key,
        )
        data = response.read()
        response.close()
        response.release_conn()
        logger.info("Read from MinIO: %s (%d bytes)", object_key, len(data))
        return data
    except Exception as e:
        logger.error("MinIO read failed: %s", object_key, exc_info=True)
        raise


async def upload(object_key: str, data: bytes, content_type: str = "image/jpeg") -> None:
    client = await _get_client()
    try:
        await asyncio.to_thread(
            client.put_object,
            settings.MINIO_BUCKET_NAME, object_key,
            BytesIO(data), length=len(data),
            content_type=content_type,
        )
        logger.info("Uploaded to MinIO: %s (%d bytes)", object_key, len(data))
    except Exception as e:
        logger.error("MinIO upload failed: %s", object_key, exc_info=True)
        raise
