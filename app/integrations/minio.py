import asyncio
import logging
from io import BytesIO
from datetime import timedelta
from urllib.parse import urlparse, urlunparse

from minio import Minio

from app.core.config import settings
from app.core.errors import StorageError, ErrorCodes
from app.core.metrics import storage_upload_errors_total


logger = logging.getLogger(__name__)


class MinIOStorage:
    def __init__(self) -> None:           
        self._bucket = settings.MINIO_BUCKET_NAME
        self._client: Minio | None = None

    async def startup(self) -> None:
        try:
            self._client = await asyncio.wait_for(
                asyncio.to_thread(
                    Minio,
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ROOT_USER,
                    secret_key=settings.MINIO_ROOT_PASSWORD,
                    secure=False,
                ),
                timeout=settings.SERVICE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.critical("MinIO client creation timed out after %ss", settings.SERVICE_TIMEOUT)
            storage_upload_errors_total.labels(error_code=ErrorCodes.STORAGE_TIMEOUT).inc()
            raise StorageError(cause="timeout", code=ErrorCodes.STORAGE_TIMEOUT)
        await self._ensure_bucket()

    async def shutdown(self) -> None:    
        if self._client:
            self._client = None

    async def _ensure_bucket(self):
        def _sync():
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
        try:
            await asyncio.wait_for(
                asyncio.to_thread(_sync),
                timeout=settings.SERVICE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.critical("MinIO ensure_bucket timed out after %ss", settings.SERVICE_TIMEOUT)
            storage_upload_errors_total.labels(error_code=ErrorCodes.STORAGE_TIMEOUT).inc()
            raise StorageError(cause="timeout", code=ErrorCodes.STORAGE_TIMEOUT)
        except Exception as e:
            logger.critical("MinIO ensure_bucket failed")
            storage_upload_errors_total.labels(error_code=ErrorCodes.BUCKET_ERROR).inc()
            raise StorageError(cause=str(e), code=ErrorCodes.BUCKET_ERROR)

    async def add_photo(self, object_key: str, data: bytes, content_type: str) -> None:
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.put_object,
                    self._bucket, object_key, BytesIO(data),
                    length=len(data), content_type=content_type,
                ),
                timeout=settings.SERVICE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error(
                "MinIO put_object timed out after %ss: %s", settings.SERVICE_TIMEOUT, object_key,
            )
            storage_upload_errors_total.labels(error_code=ErrorCodes.STORAGE_TIMEOUT).inc()
            raise StorageError(cause="timeout", code=ErrorCodes.STORAGE_TIMEOUT)
        except Exception as e:
            logger.error(
                "MinIO put_object failed: %s", object_key, exc_info=True,
            )
            storage_upload_errors_total.labels(error_code=ErrorCodes.PHOTO_NOT_ADD_TO_STORAGE).inc()
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
            url = await asyncio.wait_for(
                asyncio.to_thread(
                    self._client.presigned_get_object,
                    bucket_name=self._bucket,
                    object_name=object_key,
                    expires=timedelta(seconds=expires),
                ),
                timeout=settings.SERVICE_TIMEOUT,
            )
            if settings.MINIO_PUBLIC_URL:
                parts = urlparse(url)
                url = urlunparse(parts._replace(netloc=settings.MINIO_PUBLIC_URL))
            return url
        except asyncio.TimeoutError:
            logger.error(
                "MinIO presigned URL timed out after %ss: %s", settings.SERVICE_TIMEOUT, object_key,
            )
            storage_upload_errors_total.labels(error_code=ErrorCodes.STORAGE_TIMEOUT).inc()
            raise StorageError(cause="timeout", code=ErrorCodes.STORAGE_TIMEOUT)
        except Exception as e:
            logger.error(
                "MinIO presigned URL failed: %s", object_key, exc_info=True,
            )
            storage_upload_errors_total.labels(error_code=ErrorCodes.PHOTO_URL_NOT_TAKEN).inc()
            raise StorageError(cause=str(e), code=ErrorCodes.PHOTO_URL_NOT_TAKEN)
