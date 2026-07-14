from datetime import datetime
from typing import Literal

from pydantic import BaseModel

class UploadPhotosResponse(BaseModel):
    status: Literal['pending']
    photo_ids: list
    message: Literal['Фото приняты в асинхронную обработку']

class GetPhotosByIDResponse(BaseModel):
    photo_id: str
    image_preview_url: str | None = None
    image_url: str | None = None
    status: Literal["pending", "processing", "done", "failed"]
    faces_count: int | None = None
    eyes_closed_count: int | None = None
    is_blurred: bool | None = None
    blur_score: float | None = None
    perceptual_hash: str | None = None
    duplicate_group_id: str | None = None
    identity_group_id: str | None = None
    quality_metric: int | None = None
    created_at: datetime
    updated_at: datetime

class GetPhotosListResponse(BaseModel):
    photo_ids: list

class HealthCheck(BaseModel):
    status: Literal['ok', 'error']


