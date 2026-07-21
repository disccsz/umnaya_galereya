import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Group, Photos
from app.core.errors import DatabaseError, ErrorCodes, PhotoNotFoundError, AppException


logger = logging.getLogger(__name__)


class PhotoDatabase:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, photo: Photos) -> Photos:
        try:
            self._session.add(photo)
            await self._session.commit()
            await self._session.refresh(photo)
            return photo
        except Exception as e:
            logger.error("Database create failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_CREATE)

    async def list(self) -> list[Photos]:
        try:
            result = await self._session.execute(
                select(Photos).order_by(Photos.load_time.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database list failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)

    async def get_photo_by_id(self, string_id: str) -> Photos:
        try:
            result = await self._session.execute(
                select(Photos)
                .where(Photos.id_string == string_id)
                .limit(1)
                .options(
                    selectinload(Photos.analysis),
                    selectinload(Photos.duplicate_group_rel),
                    selectinload(Photos.identity_group_rel),
                )
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(
                "Database get_photo_by_id failed: %s", string_id, exc_info=True,
            )
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)

    async def update_status(self, photo_id: int, status: str) -> Photos:
        try:
            photo = await self._session.get(Photos, photo_id)
            if not photo:
                raise PhotoNotFoundError(str(photo_id))
            photo.status = status
            await self._session.commit()
            return photo
        except AppException:
            raise
        except Exception as e:
            logger.error(
                "Database update_status failed: id=%s, status=%s",
                photo_id, status, exc_info=True,
            )
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_GET) from e


class GroupDatabase:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_groups(self) -> list[Group]:
        try:
            result = await self._session.execute(
                select(Group)
                .options(
                    selectinload(Group.duplicate_photos),
                    selectinload(Group.identity_photos),
                )
                .order_by(Group.created_at.desc())
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database list_groups failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)

    async def get_group_by_id(self, id_string: str) -> Group | None:
        try:
            result = await self._session.execute(
                select(Group)
                .where(Group.id_string == id_string)
                .limit(1)
                .options(
                    selectinload(Group.duplicate_photos).selectinload(Photos.analysis),
                    selectinload(Group.identity_photos).selectinload(Photos.analysis),
                )
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(
                "Database get_group_by_id failed: %s", id_string, exc_info=True,
            )
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)
