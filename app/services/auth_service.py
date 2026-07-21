import logging
import time
import hashlib
import hmac
import base64
from urllib.parse import urlencode

from app.core.config import settings
from app.core.errors import MissingParamError, AccessDeniedError
from app.core.jwt_utils import encode_jwt
from app.integrations.postgreesql import TokenDatabase
from app.schemas.auth import VKAuthRequest

logger = logging.getLogger(__name__)


class VKAuthService:
    def __init__(self, database: TokenDatabase):
        self._database = database

    async def authenticate(self, body: VKAuthRequest) -> str:
        if not body.vk_user_id or not body.vk_app_id or not body.sign:
            raise MissingParamError()

        if not self._verify_sign(body):
            raise AccessDeniedError()

        data_token = self._compute_data_token(body.vk_user_id)

        now = int(time.time())
        exp = now + settings.JWT_EXPIRE_MINUTES * 60
        jwt_payload = {
            "sub": data_token,
            "vk_user_id": body.vk_user_id,
            "iat": now,
            "exp": exp,
        }
        auth_token = encode_jwt(jwt_payload, settings.VK_SECRET_KEY)

        await self._database.upsert_token(
            data_token=data_token,
            vk_user_id=body.vk_user_id,
            auth_token=auth_token,
            created_at=now,
            expires_at=exp,
        )

        logger.info("Auth token issued for vk_user_id=%s", body.vk_user_id)
        return auth_token

    def _verify_sign(self, body: VKAuthRequest) -> bool:
        vk_params = {}
        for key, value in body.model_dump().items():
            if key.startswith("vk_") and value is not None:
                vk_params[key] = value

        vk_params = dict(sorted(vk_params.items()))
        signature_string = urlencode(vk_params, doseq=True)

        digest = hmac.new(
            settings.VK_SECRET_KEY.encode(),
            signature_string.encode(),
            hashlib.sha256,
        ).digest()
        calculated_sign = base64.urlsafe_b64encode(digest).decode().rstrip("=")

        logger.warning("=== VK SIGN VERIFICATION ===")
        logger.warning("vk_params: %s", vk_params)
        logger.warning("signature_string: %s", signature_string)
        logger.warning("secret_key: %s", settings.VK_SECRET_KEY)
        logger.warning("calculated_sign: %s", calculated_sign)
        logger.warning("received_sign:    %s", body.sign)
        logger.warning("match: %s", calculated_sign == body.sign)

        return calculated_sign == body.sign

    def _compute_data_token(self, vk_user_id: str) -> str:
        digest = hmac.new(
            settings.VK_SECRET_KEY.encode(),
            vk_user_id.encode(),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode()
