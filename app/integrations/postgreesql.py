import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Group, Photos, Token
from app.core.errors import DatabaseError, ErrorCodes, PhotoNotFoundError, AccessDeniedError, AppException


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

    async def list(self, owner_data_token: str | None = None) -> list[Photos]:
        try:
            stmt = select(Photos).order_by(Photos.load_time.desc())
            if owner_data_token is not None:
                stmt = stmt.where(Photos.owner_data_token == owner_data_token)
            else:
                stmt = stmt.where(Photos.is_private == False)
            result = await self._session.execute(
                stmt.options(
                    selectinload(Photos.duplicate_group_rel),
                    selectinload(Photos.identity_group_rel),
                )
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database list failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)

    async def get_photo_by_id(self, string_id: str, owner_data_token: str | None = None) -> Photos:
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
            photo = result.scalars().first()
            if photo is None:
                return None
            if photo.is_private and photo.owner_data_token != owner_data_token:
                raise AccessDeniedError()
            return photo
        except AppException:
            raise
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

    async def list_groups(self, owner_data_token: str | None = None) -> list[Group]:
        try:
            stmt = (
                select(Group)
                .options(
                    selectinload(Group.duplicate_photos),
                    selectinload(Group.identity_photos),
                )
                .order_by(Group.created_at.desc())
            )
            if owner_data_token is not None:
                stmt = stmt.where(Group.owner_data_token == owner_data_token)
            else:
                stmt = stmt.where(Group.is_private == False)
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error("Database list_groups failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)

    async def get_group_by_id(self, id_string: str, owner_data_token: str | None = None) -> Group | None:
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
            group = result.scalars().first()
            if group is None:
                return None
            if group.is_private and group.owner_data_token != owner_data_token:
                raise AccessDeniedError()
            return group
        except AppException:
            raise
        except Exception as e:
            logger.error(
                "Database get_group_by_id failed: %s", id_string, exc_info=True,
            )
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)


class TokenDatabase:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert_token(
        self,
        data_token: str,
        vk_user_id: str,
        auth_token: str,
        created_at: int,
        expires_at: int,
    ) -> None:
        try:
            existing = await self._session.get(Token, data_token)
            if existing:
                existing.auth_token = auth_token
                existing.created_at_time = datetime.fromtimestamp(created_at, tz=timezone.utc)
                existing.expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            else:
                token = Token(
                    data_token=data_token,
                    auth_token=auth_token,
                    vk_owner_user_id=vk_user_id,
                    created_at_time=datetime.fromtimestamp(created_at, tz=timezone.utc),
                    expires_at=datetime.fromtimestamp(expires_at, tz=timezone.utc),
                )
                self._session.add(token)
            await self._session.commit()
        except Exception as e:
            logger.error("Token upsert failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_CREATE)

    async def get_by_data_token(self, data_token: str) -> Token | None:
        try:
            return await self._session.get(Token, data_token)
        except Exception as e:
            logger.error("Token get_by_data_token failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)

    async def get_by_auth_token(self, auth_token: str) -> Token | None:
        try:
            result = await self._session.execute(
                select(Token).where(Token.auth_token == auth_token).limit(1)
            )
            return result.scalars().first()
        except Exception as e:
            logger.error("Token get_by_auth_token failed", exc_info=True)
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)
