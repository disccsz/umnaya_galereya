
import uuid

from typing import List
from fastapi import UploadFile, HTTPException, status

from app.integrations.postgreesql import PhotoDatabase
from app.integrations.minio import MinIOStorage
from app.database.models import Photos, PhotoStatuses
from app.schemas.photos import PhotoItem

from app.core.errors import PhotoNotFoundError, InvalidFile, ErrorCodes


class PhotoService:
    def __init__(self, database: PhotoDatabase, storage: MinIOStorage) -> None:
        self._database = database
        self._storage = storage

    async def create_photo(self, file: UploadFile) -> Photos:
        if file.size > 3 * 1024 * 1024:
            raise InvalidFile(file.size)
        if file.content_type not in ['image/jpeg', 'image/png', 'image/jpg']:
            raise InvalidFile(file.content_type)
        data = await file.read()

        photo_id = f"p_{uuid.uuid4().hex[:12]}"
        object_key = f"photos/{photo_id}/original.jpg"

        photo = Photos(id_string=photo_id, object_key=object_key, photo_size=len(data), status=PhotoStatuses.uploading)
   
        photo = await self._database.create(photo)
        await self._storage.add_photo(object_key, data, file.content_type or "application/octet-stream")
        photo = await self._database.update_status(photo_id=photo.id, status=PhotoStatuses.pending)
        
        return photo
    

    async def list_photos(self) -> List[PhotoItem]:
        photos = await self._database.list()
        response = []
        
        for photo in photos:
            if photo.status != PhotoStatuses.uploading:
                photo_data = {'photo_id': photo.id_string, 'status': photo.status}
            
                original_photo_url = await self._storage.get_presigned_url(object_key=photo.object_key)
                photo_data['original_image_url'] = original_photo_url
                if photo.preview_key:
                    preview_photo_url = await self._storage.get_presigned_url(object_key=photo.preview_key)
                    photo_data['preview_image_url'] = preview_photo_url
                response.append(photo_data)

        return response
    
    async def get_photo_by_id(self, string_id: str) -> Photos:
        photo = await self._database.get_photo_by_id(string_id=string_id)

        if not photo:
            raise PhotoNotFoundError(photo_id=string_id)

        photo_data = {'photo_id': photo.id_string, 'status': photo.status,'created_at': photo.load_time}

        return photo_data

    async def get_photo_content_by_id(self, string_id: str) -> Photos:
        photo = await self._database.get_photo_by_id(string_id=string_id)
        if not photo:
            raise PhotoNotFoundError(photo_id=string_id)
        original_photo_url, preview_photo_url = None, None
        if photo.object_key:
            original_photo_url = await self._storage.get_presigned_url(object_key=photo.object_key)
            if photo.preview_key:
                preview_photo_url = await self._storage.get_presigned_url(object_key=photo.preview_key)

        photo_data = {'photo_id': photo.id_string, 'image_preview_url': preview_photo_url, 'image_url': original_photo_url}

        return photo_data
