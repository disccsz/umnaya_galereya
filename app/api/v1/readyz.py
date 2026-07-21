import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.database import async_session
from app.integrations.minio import MinIOStorage
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["readyz"])

@router.get("/readyz")
async def readyz(request: Request):
    checks = {}
    healthy = True

    try:
        async with async_session() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=settings.SERVICE_TIMEOUT,
            )
        checks["database"] = "ok"
    except asyncio.TimeoutError:
        logger.warning("Health check — database timed out after %ss", settings.SERVICE_TIMEOUT)
        checks["database"] = "timeout"
        healthy = False
    except Exception as e:
        logger.warning("Health check — database failed: %s", e)
        checks["database"] = str(e)
        healthy = False

    storage: MinIOStorage = request.app.state.storage
    try:
        await asyncio.wait_for(
            asyncio.to_thread(storage._client.list_buckets),
            timeout=settings.SERVICE_TIMEOUT,
        )
        checks["storage"] = "ok"
    except asyncio.TimeoutError:
        logger.warning("Health check — storage timed out after %ss", settings.SERVICE_TIMEOUT)
        checks["storage"] = "timeout"
        healthy = False
    except Exception as e:
        logger.warning("Health check — storage failed: %s", e)
        checks["storage"] = str(e)
        healthy = False

    if healthy:
        return {"status": "ok", "checks": checks}

    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "checks": checks},
    )