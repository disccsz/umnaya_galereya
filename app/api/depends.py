from fastapi import Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt_utils import decode_jwt
from app.database.database import get_session


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ")
    payload = decode_jwt(token, settings.VK_SECRET_KEY)
    if payload is None:
        return None
    return payload.get("sub")
