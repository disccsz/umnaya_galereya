from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Photos

class PhotoDatabase:
    def __init__(self, session=AsyncSession):
        self._session = session

    async def create(self, photo: Photos) -> Photos:
        self._session.add(photo)
        await self._session.commit()
        await self._session.refresh(photo)
        return photo
    
    async def get_by_id(self, photo_id: str) -> Photos | None:
        return await self._session.get(Photos, photo_id)
    
    async def list(self) -> list[Photos]:
        result = await self._session.execute(select(Photos).order_by(Photos.created_at.desc()))
        return list(result.scalars().all())

    async def update_status(self, photo_id: str, status: str) -> None:
        photo = await self.get_by_id(photo_id)
        if photo:
            photo.status = status
            await self._session.commit()
