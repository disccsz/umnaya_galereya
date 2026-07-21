import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.database import async_session
from app.integrations.minio import MinIOStorage
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(tags=["healthz"])

@router.get("/healthz")
async def healthz(request: Request):
    return JSONResponse(
            status_code=200,
            content={"status": "ok"},
        )
        
