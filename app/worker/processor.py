import asyncio
import logging

from app.core.config import settings
from app.database.models import PhotoStatuses
from app.worker import database as db
from app.worker import grpc_client
from app.worker import hasher
from app.worker import minio_client
from app.worker import preview

logger = logging.getLogger(__name__)

MAX_RETRIES = 5
RETRY_DELAYS = [10, 15, 20, 25]  # seconds, 4 retries for analyzer calls


async def _call_analyzer_with_retry(
    photo_id: str,
    object_key: str,
    image_bytes: bytes,
):
    last_error = None
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            return await grpc_client.analyze(
                photo_id=photo_id, object_key=object_key, image_bytes=image_bytes,
            )
        except Exception as e:
            last_error = e
            if attempt < len(RETRY_DELAYS):
                delay = RETRY_DELAYS[attempt]
                logger.warning(
                    "Analyzer call failed (attempt %d), retrying in %ds: %s",
                    attempt + 1, delay, e,
                )
                await asyncio.sleep(delay)
    logger.error("Analyzer call failed after all retries: %s", last_error)
    return None


async def _check_photo_identity(photo_id: int, sha256_hash: str, owner_token: str | None) -> None:
    match = await db.find_matching_identity_photo(sha256_hash, exclude_photo_id=photo_id, owner_token=owner_token)
    if match is None:
        return

    existing_photo_id, existing_group_id = match
    if existing_group_id is not None:
        await db.assign_identity_group(photo_id, existing_group_id)
        logger.info("Photo %s assigned to identity group %d", photo_id, existing_group_id)
    else:
        group_id = await db.create_group(True, sha256_hash, owner_token)
        await db.assign_identity_group(existing_photo_id, group_id)
        await db.assign_identity_group(photo_id, group_id)
        logger.info("Created identity group %d for photos %d and %d", group_id, existing_photo_id, photo_id)


async def _check_photo_duplicates(photo_id: int, perceptual_hash: str, owner_token: str | None) -> None:
    match = await db.find_matching_duplicate_photo(
        perceptual_hash, 20, exclude_photo_id=photo_id, owner_token=owner_token,
    )
    if match is None:
        return

    existing_photo_id, existing_group_id = match
    if existing_group_id is not None:
        await db.assign_duplicate_group(photo_id, existing_group_id)
        logger.info("Photo %s assigned to duplicate group %d", photo_id, existing_group_id)
    else:
        group_id = await db.create_group(False, perceptual_hash, owner_token)
        await db.assign_duplicate_group(existing_photo_id, group_id)
        await db.assign_duplicate_group(photo_id, group_id)
        logger.info("Created duplicate group %d for photos %d and %d", group_id, existing_photo_id, photo_id)


async def process_message(photo_id: str, object_key: str, msg) -> None:
    photo = await db.get_photo_by_string_id(photo_id)
    if not photo:
        raise RuntimeError(f"Photo {photo_id} not found in DB")

    attempts = await db.claim_photo(photo.id)
    if attempts is None:
        logger.info("Photo %s already claimed by another worker", photo_id)
        return

    try:
        logger.info("Processing photo %s (attempt %d)", photo_id, attempts)

        image_data = await minio_client.read(object_key)

        analysis = await _call_analyzer_with_retry(
            photo_id=photo_id, object_key=object_key, image_bytes=image_data,
        )
        if analysis is None:
            await db.update_status(
                photo.id, PhotoStatuses.failed,
                attempts=attempts,
                last_error_message="Analyzer unavailable after all retries",
            )
            logger.warning("Photo %s moved to failed (analyzer down)", photo_id)
            return

        sha256 = hasher.sha256(image_data)
        phash = hasher.perceptual(image_data)

        preview_data = preview.generate(image_data)
        preview_key = f"photos/{photo_id}/preview.jpg"
        await minio_client.upload(preview_key, preview_data)

        quality_metric = max(0, 255 - int(analysis.blur_score))

        await db.save_analysis_and_finish(
            photo_id=photo.id,
            status=PhotoStatuses.done,
            preview_key=preview_key,
            faces_count=analysis.faces_count,
            eyes_closed_count=analysis.eyes_closed_count,
            is_blurred=analysis.is_blurred,
            blur_score=analysis.blur_score,
            quality_metric=quality_metric,
            perceptual_hash=phash or analysis.perceptual_hash,
            sha256_hash=sha256,
            dominant_color=analysis.dominant_color,
            tags=list(analysis.tags) if analysis.tags else None,
            model_version=analysis.model_version,
        )

        logger.info("Photo %s processed successfully", photo_id)

        try:
            await _check_photo_identity(photo.id, sha256, photo.owner_data_token)
        except Exception as e:
            logger.error("Identity check failed for photo %s: %s", photo_id, e, exc_info=True)
        try:
            if phash is not None:
                await _check_photo_duplicates(photo.id, phash, photo.owner_data_token)
        except Exception as e:
            logger.error("Duplicate check failed for photo %s: %s", photo_id, e, exc_info=True)

    except Exception as e:
        logger.error("Photo %s processing failed: %s", photo_id, e, exc_info=True)

        if attempts >= MAX_RETRIES:
            error_msg = str(e)[:1000]
            await db.update_status(
                photo.id, PhotoStatuses.failed,
                attempts=attempts,
                last_error_message=error_msg,
            )
            logger.warning("Photo %s moved to failed after %d attempts", photo_id, attempts)
