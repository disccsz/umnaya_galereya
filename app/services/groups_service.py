import logging

from app.integrations.postgreesql import GroupDatabase
from app.core.errors import GroupNotFoundError

logger = logging.getLogger(__name__)


class GroupService:
    def __init__(self, database: GroupDatabase):
        self._database = database

    async def list_groups(self) -> list[dict]:
        groups = await self._database.list_groups()
        result = []
        for g in groups:
            photos = g.duplicate_photos if not g.is_identity_group else g.identity_photos
            result.append({
                "id_string": g.id_string,
                "is_identity_group": g.is_identity_group,
                "created_at": g.created_at,
                "photos_count": len(photos),
            })
        return result

    async def get_group_by_id(self, id_string: str) -> dict:
        group = await self._database.get_group_by_id(id_string)
        if not group:
            raise GroupNotFoundError(group_id=id_string)

        photos_rel = group.duplicate_photos if not group.is_identity_group else group.identity_photos

        best_quality = -1
        photos = []
        for p in photos_rel:
            qm = p.analysis.quality_metric if p.analysis else None
            photos.append({
                "photo_id": p.id_string,
                "is_best": False,
                "quality_metric": qm,
                "faces_count": p.analysis.faces_count if p.analysis else None,
                "is_blurred": p.analysis.is_blurred if p.analysis else None,
            })
            if qm is not None and qm > best_quality:
                best_quality = qm

        for photo in photos:
            if photo["quality_metric"] is not None and photo["quality_metric"] == best_quality:
                photo["is_best"] = True
                break

        return {
            "id_string": group.id_string,
            "is_identity_group": group.is_identity_group,
            "created_at": group.created_at,
            "photos": photos,
        }
