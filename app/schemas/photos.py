from datetime import datetime
from typing import Literal

from pydantic import BaseModel

class UploadPhotosResponse(BaseModel):
    status: Literal['pending']
    photo_id: str
    message: Literal['Фото приняты в асинхронную обработку'] = 'Фото приняты в асинхронную обработку'

class GetPhotoContentByIDResponse(BaseModel):
    photo_id: str
    image_preview_url: str | None = None
    image_url: str | None = None

class GetPhotosByIDResponse(BaseModel):
    photo_id: str
    status: Literal["uploading", "pending", "processing", "done", "failed"]
    faces_count: int | None = None
    eyes_closed_count: int | None = None
    is_blurred: bool | None = None
    blur_score: float | None = None
    duplicate_group_id: str | None = None
    identity_group_id: str | None = None
    quality_metric: int | None = None
    tags: list[str] | None = None
    created_at: datetime

class PhotoItem(BaseModel):
    photo_id: str
    status: Literal['uploading', "pending", "processing", "done", "failed"]
    original_image_url: str | None = None
    preview_image_url: str | None = None
    created_at: datetime | None = None
    groups_ids: list[str] | None = None

class GetPhotosListResponse(BaseModel):
    photos: list[PhotoItem]

class HealthCheck(BaseModel):
    status: Literal['ok', 'error']


