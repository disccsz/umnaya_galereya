from typing import Any

from pydantic import BaseModel, model_validator


class VKAuthRequest(BaseModel):
    vk_user_id: str
    vk_app_id: str
    vk_access_token_settings: str | None = None
    vk_are_notifications_enabled: str | None = None
    vk_chat_id: str | None = None
    vk_group_id: str | None = None
    vk_has_profile_button: str | None = None
    vk_is_app_user: str | None = None
    vk_is_favorite: str | None = None
    vk_is_play_machine: str | None = None
    vk_is_recommended: str | None = None
    vk_is_widescreen: str | None = None
    vk_language: str | None = None
    vk_platform: str | None = None
    vk_profile_id: str | None = None
    vk_ref: str | None = None
    vk_request_key: str | None = None
    vk_testing_group_id: str | None = None
    vk_ts: str | None = None
    vk_viewer_group_role: str | None = None
    sign: str

    @model_validator(mode="before")
    @classmethod
    def coerce_vk_params(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for key in list(data.keys()):
                if key.startswith("vk_") and data[key] is not None:
                    if isinstance(data[key], bool):
                        data[key] = "1" if data[key] else "0"
                    else:
                        data[key] = str(data[key])
        return data


class VKAuthResponse(BaseModel):
    auth_token: str
