from datetime import datetime
from pydantic import BaseModel


class DuplicateGroupItem(BaseModel):
    id_string: str
    is_identity_group: bool
    created_at: datetime
    photos_count: int


class DuplicateGroupListResponse(BaseModel):
    duplicate_groups: list[DuplicateGroupItem]


class GroupPhotoItem(BaseModel):
    photo_id: str
    is_best: bool = False
    quality_metric: int | None = None
    faces_count: int | None = None
    is_blurred: bool | None = None


class DuplicateGroupDetailResponse(BaseModel):
    id_string: str
    is_identity_group: bool
    created_at: datetime
    photos: list[GroupPhotoItem]
