import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.database.database import async_session
from app.integrations.minio import MinIOStorage
from sqlalchemy import text


logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz(request: Request):
    checks = {}
    healthy = True

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        logger.warning("Health check — database failed: %s", e)
        checks["database"] = str(e)
        healthy = False

    storage: MinIOStorage = request.app.state.storage
    try:
        await asyncio.to_thread(storage._client.list_buckets)
        checks["storage"] = "ok"
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