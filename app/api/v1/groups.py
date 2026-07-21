import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session
from app.integrations.postgreesql import GroupDatabase
from app.schemas.groups import (
    DuplicateGroupListResponse,
    DuplicateGroupItem,
    DuplicateGroupDetailResponse,
)
from app.services.groups_service import GroupService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/duplicate-groups")


def get_group_service(
    request: Request, session: AsyncSession = Depends(get_session)
) -> GroupService:
    database = GroupDatabase(session)
    return GroupService(database=database)


@router.get("/", response_model=DuplicateGroupListResponse)
async def list_duplicate_groups(
    service: GroupService = Depends(get_group_service),
) -> DuplicateGroupListResponse:
    groups = await service.list_groups()
    return DuplicateGroupListResponse(
        duplicate_groups=[DuplicateGroupItem(**g) for g in groups]
    )


@router.get("/{id_string}", response_model=DuplicateGroupDetailResponse)
async def get_duplicate_group_by_id(
    id_string: str,
    service: GroupService = Depends(get_group_service),
) -> DuplicateGroupDetailResponse:
    group = await service.get_group_by_id(id_string=id_string)
    return DuplicateGroupDetailResponse(**group)
