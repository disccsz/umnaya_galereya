import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_session
from app.integrations.postgreesql import TokenDatabase
from app.schemas.auth import VKAuthRequest, VKAuthResponse
from app.services.auth_service import VKAuthService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1")


@router.post("/photo/auth", response_model=VKAuthResponse)
async def vk_auth(
    body: VKAuthRequest,
    session: AsyncSession = Depends(get_session),
) -> VKAuthResponse:
    db = TokenDatabase(session)
    service = VKAuthService(db)
    token = await service.authenticate(body)
    return VKAuthResponse(auth_token=token)
