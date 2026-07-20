import asyncio
import logging
from io import BytesIO
from datetime import timedelta

from minio import Minio

from app.core.config import settings
from app.core.errors import StorageError, ErrorCodes


logger = logging.getLogger(__name__)


class MinIOStorage:
    def __init__(self) -> None:           
        self._bucket = settings.MINIO_BUCKET_NAME
        self._client: Minio | None = None

    async def startup(self) -> None:       # вызывается один раз в lifespan
        self._client = await asyncio.to_thread(
            Minio,
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ROOT_USER,
            secret_key=settings.MINIO_ROOT_PASSWORD,
            secure=False,
        )
        await self._ensure_bucket()

    async def shutdown(self) -> None:    
        if self._client:
            self._client = None

    async def _ensure_bucket(self):
        def _sync():
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
        try:
            await asyncio.to_thread(_sync)
        except Exception as e:
            logger.critical("MinIO ensure_bucket failed")
            raise StorageError(cause=str(e), code=ErrorCodes.BUCKET_ERROR)

    async def add_photo(self, object_key: str, data: bytes, content_type: str) -> None:
        try:
            await asyncio.to_thread(
                self._client.put_object,
                self._bucket, object_key, BytesIO(data),
                length=len(data), content_type=content_type,
            )
        except Exception as e:
            logger.error(
                "MinIO put_object failed: %s", object_key, exc_info=True,
            )
            raise StorageError(cause=str(e), code=ErrorCodes.PHOTO_NOT_ADD_TO_STORAGE)

    def get_photo(self, object_key: str) -> bytes:
        try:
            return self._client.get_object(self._bucket, object_key).read()
        except Exception as e:
            logger.error(
                "MinIO get_object failed: %s", object_key, exc_info=True,
            )
            raise StorageError(cause=str(e), code=ErrorCodes.PHOTO_NOT_TAKEN_FROM_STORAGE)

    async def get_presigned_url(self, object_key: str, expires: int = 3600) -> str:
        try:
            return await asyncio.to_thread(
                self._client.presigned_get_object,
                bucket_name=self._bucket,
                object_name=object_key,
                expires=timedelta(seconds=expires),
            )
        except Exception as e:
            logger.error(
                "MinIO presigned URL failed: %s", object_key, exc_info=True,
            )
            raise StorageError(cause=str(e), code=ErrorCodes.PHOTO_URL_NOT_TAKEN)
