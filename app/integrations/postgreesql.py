from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Photos

class PhotoDatabase:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, photo: Photos) -> Photos:
        self._session.add(photo)
        await self._session.commit()
        await self._session.refresh(photo)
        return photo
    
    async def list(self) -> list[Photos]:
        result = await self._session.execute(select(Photos).order_by(Photos.load_time.desc()))
        return list(result.scalars().all())
    
    async def get_photo_by_id(self, string_id: str) -> Photos:
        result = await self._session.execute(select(Photos).where(Photos.id_string==string_id).limit(1))
        result = result.scalars().first()
        print('#############################################', result)
        return result
    

    async def update_status(self, photo_id: int, status: str) -> Photos:
        photo = await self._session.get(Photos, photo_id)
        if photo:
            photo.status = status
            await self._session.commit()
            return photo
