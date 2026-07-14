
import uuid

from fastapi import UploadFile

from app.integrations.postgreesql import PhotoDatabase
from app.integrations.minio import MinIOStorage
from app.database.models import Photos, PhotoStatuses


class PhotoService:
    def __init__(self, database: PhotoDatabase, storage: MinIOStorage) -> None:
        self._repository = database
        self._storage = storage

    async def create_photo(self, file: UploadFile) -> Photos:
        data = await file.read()

        photo_id = f"p_{uuid.uuid4().hex[:12]}"
        object_key = f"photos/{photo_id}/original.jpg"

        photo = Photos(id_string=photo_id, object_key=object_key, photo_size=len(data))
   
        await self._storage.add_photo(object_key, data, file.content_type or "application/octet-stream")

        photo = await self._repository.create(photo)
        return photo