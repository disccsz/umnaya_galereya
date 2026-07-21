from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session
from app.integrations.metrics_db import get_db_metrics_text

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics(session: AsyncSession = Depends(get_session)):
    api_metrics = generate_latest().decode()
    db_metrics = await get_db_metrics_text(session)
    return Response(
        content=api_metrics + "\n" + db_metrics,
        media_type=CONTENT_TYPE_LATEST,
    )
