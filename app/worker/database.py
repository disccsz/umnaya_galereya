import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, text

from app.database.database import async_session
from app.database.models import Group, PhotoAnalysis, PhotoStatuses, Photos

logger = logging.getLogger(__name__)


async def get_photo_by_string_id(string_id: str) -> Photos | None:
    async with async_session() as session:
        result = await session.execute(
            select(Photos).where(Photos.id_string == string_id).limit(1),
        )
        return result.scalars().first()


async def update_status(
    photo_id: int,
    status: PhotoStatuses,
    attempts: int | None = None,
    last_error_message: str | None = None,
) -> None:
    async with async_session() as session:
        photo = await session.get(Photos, photo_id)
        if not photo:
            logger.error("Photo %s not found for status update", photo_id)
            return
        photo.status = status
        if attempts is not None:
            photo.attempts = attempts
        if last_error_message is not None:
            photo.last_error_message = last_error_message
        await session.commit()


async def save_analysis(
    photo_id: int,
    faces_count: int | None = None,
    eyes_closed_count: int | None = None,
    is_blurred: bool | None = None,
    blur_score: float | None = None,
    quality_metric: int | None = None,
    perceptual_hash: str | None = None,
    sha256_hash: str | None = None,
    dominant_color: str | None = None,
    tags: list[str] | None = None,
    model_version: str | None = None,
) -> None:
    async with async_session() as session:
        analysis = PhotoAnalysis(
            photo_id=photo_id,
            faces_count=faces_count,
            eyes_closed_count=eyes_closed_count,
            is_blurred=is_blurred,
            blur_score=blur_score,
            quality_metric=quality_metric,
            perceptual_hash=perceptual_hash,
            sha256_hash=sha256_hash,
            dominant_color=dominant_color,
            tags=json.dumps(tags) if tags else None,
            model_version=model_version,
            analysis_at=datetime.now(timezone.utc),
        )
        session.add(analysis)
        await session.commit()


async def update_photo_after_analysis(
    photo_id: int,
    status: PhotoStatuses,
    preview_key: str | None = None,
) -> None:
    async with async_session() as session:
        photo = await session.get(Photos, photo_id)
        if not photo:
            logger.error("Photo %s not found for post-analysis update", photo_id)
            return
        photo.status = status
        if preview_key:
            photo.preview_key = preview_key
        await session.commit()


async def find_matching_identity_photo(sha256_hash: str, exclude_photo_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(Photos.id, Photos.identity_photo_group_id)
            .join(PhotoAnalysis, PhotoAnalysis.photo_id == Photos.id)
            .where(PhotoAnalysis.sha256_hash == sha256_hash)
            .where(Photos.id != exclude_photo_id)
            .limit(1)
        )
        return result.one_or_none()


async def find_matching_duplicate_photo(phash: str, threshold: int, exclude_photo_id: int):
    async with async_session() as session:
        result = await session.execute(
            text("""
                SELECT pa.photo_id, p.duplicate_group_id, pa.perceptual_hash
                FROM photo_analysis pa
                JOIN photos p ON p.id = pa.photo_id
                WHERE pa.photo_id != :exclude_photo_id
                  AND pa.perceptual_hash IS NOT NULL
            """),
            {"exclude_photo_id": exclude_photo_id}
        )
        rows = result.all()

    target = int(phash, 16)
    best_photo_id = None
    best_group_id = None
    best_dist = threshold + 1

    for photo_id, group_id, hash_str in rows:
        dist = (target ^ int(hash_str, 16)).bit_count()
        if dist < best_dist:
            best_dist = dist
            best_photo_id = photo_id
            best_group_id = group_id

    if best_photo_id is None:
        return None

    return best_photo_id, best_group_id


async def create_group(is_identity: bool, standart_hash: str, owner_token: str | None = None) -> int:
    async with async_session() as session:
        group = Group(
            is_identity_group=is_identity,
            standart_hash=standart_hash,
            owner_data_token=owner_token,
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group.id


async def assign_identity_group(photo_id: int, group_id: int) -> None:
    async with async_session() as session:
        photo = await session.get(Photos, photo_id)
        if photo:
            photo.identity_photo_group_id = group_id
            await session.commit()


async def assign_duplicate_group(photo_id: int, group_id: int) -> None:
    async with async_session() as session:
        photo = await session.get(Photos, photo_id)
        if photo:
            photo.duplicate_group_id = group_id
            await session.commit()


async def claim_photo(photo_int_id: int) -> int | None:
    async with async_session() as session:
        result = await session.execute(
            text("""
                UPDATE photos
                SET status = 'processing', attempts = attempts + 1
                WHERE id = :id AND status = 'pending'
                RETURNING attempts
            """),
            {"id": photo_int_id}
        )
        await session.commit()
        row = result.one_or_none()
        if row is None:
            return None
        return row.attempts


async def save_analysis_and_finish(
    photo_id: int,
    status: PhotoStatuses,
    preview_key: str | None = None,
    faces_count: int | None = None,
    eyes_closed_count: int | None = None,
    is_blurred: bool | None = None,
    blur_score: float | None = None,
    quality_metric: int | None = None,
    perceptual_hash: str | None = None,
    sha256_hash: str | None = None,
    dominant_color: str | None = None,
    tags: list[str] | None = None,
    model_version: str | None = None,
) -> None:
    async with async_session() as session:
        photo = await session.get(Photos, photo_id)
        if not photo:
            logger.error("Photo %s not found for save_analysis_and_finish", photo_id)
            return

        analysis = PhotoAnalysis(
            photo_id=photo_id,
            faces_count=faces_count,
            eyes_closed_count=eyes_closed_count,
            is_blurred=is_blurred,
            blur_score=blur_score,
            quality_metric=quality_metric,
            perceptual_hash=perceptual_hash,
            sha256_hash=sha256_hash,
            dominant_color=dominant_color,
            tags=json.dumps(tags) if tags else None,
            model_version=model_version,
            analysis_at=datetime.now(timezone.utc),
        )
        session.add(analysis)

        photo.status = status
        if preview_key:
            photo.preview_key = preview_key

        await session.commit()
