import asyncio
import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.errors import DatabaseError, ErrorCodes


logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_timeout=settings.SERVICE_TIMEOUT,
)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session():
    async with async_session() as session:
        try:
            yield session
        except asyncio.TimeoutError:
            logger.critical("Database pool timeout after %ss", settings.SERVICE_TIMEOUT)
            raise DatabaseError(cause="pool timeout", code=ErrorCodes.DATABASE_TIMEOUT) from None
        except SQLAlchemyError as e:
            logger.critical("Database session error", exc_info=True)
            raise DatabaseError(cause=str(e)) from e
