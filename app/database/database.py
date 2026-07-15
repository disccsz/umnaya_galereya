import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.errors import DatabaseError, AppException


logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=settings.DB_ECHO)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            if isinstance(e, AppException):
                raise
            logger.critical("Database session error", exc_info=True)
            raise DatabaseError(cause=str(e)) from e
