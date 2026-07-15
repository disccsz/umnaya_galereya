from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Photos
from app.core.errors import DatabaseError, ErrorCodes

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
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_CREATE)


    async def list(self) -> list[Photos]:
        try:
                
            result = await self._session.execute(select(Photos).order_by(Photos.load_time.desc()))
            return list(result.scalars().all())
        except Exception as e:
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)    
        
    async def get_photo_by_id(self, string_id: str) -> Photos:
        try:
            result = await self._session.execute(select(Photos).where(Photos.id_string==string_id).limit(1))
            result = result.scalars().first()
            return result
        except Exception as e:
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_EXECUTE)  

    async def update_status(self, photo_id: int, status: str) -> Photos:
        try:
            photo = await self._session.get(Photos, photo_id)
            if not photo:
                raise PhotoNotFoundError(str(photo_id))
            photo.status = status
            await self._session.commit()
            return photo
        except AppException:  # пробрасываем PhotoNotFoundError
            raise
        except Exception as e:
            raise DatabaseError(cause=str(e), code=ErrorCodes.DATABASE_CANT_GET) from e