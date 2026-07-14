from io import BytesIO

from minio import Minio

from app.core.config import settings

class MinIOStorage:
    def __init__(self) -> None:
        self._client = Minio(settings.MINIO_ENDPOINT, access_key=settings.MINIO_ROOT_USER, secret_key=settings.MINIO_ROOT_PASSWORD, secure=False)
        self._bucket = settings.MINIO_BUCKET_NAME
        self._ensure_bucket()

    def _ensure_bucket(self):
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    def add_photo(self, object_key: str, data: bytes, content_type: str) -> None:
        self._client.put_object(self._bucket, object_key, bytesIO(data), length=len(data), content_type=content_type)

    def get_photo(self, object_key) -> bytes:
        return self._client.get_object(self._bucket, object_key).read()


storage = MinIOStorage()