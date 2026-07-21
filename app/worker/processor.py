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


async def process_message(photo_id: str, object_key: str, msg) -> None:
    photo = await db.get_photo_by_string_id(photo_id)
    if not photo:
        raise RuntimeError(f"Photo {photo_id} not found in DB")

    attempts = photo.attempts + 1

    try:
        await db.update_status(
            photo.id, PhotoStatuses.processing, attempts=attempts,
        )
        logger.info("Processing photo %s (attempt %d)", photo_id, attempts)

        image_data = await minio_client.read(object_key)

        analysis = await grpc_client.analyze(
            photo_id=photo_id, object_key=object_key, image_bytes=image_data,
        )

        sha256 = hasher.sha256(image_data)
        phash = hasher.perceptual(image_data)

        preview_data = preview.generate(image_data)
        preview_key = f"photos/{photo_id}/preview.jpg"
        await minio_client.upload(preview_key, preview_data)

        await db.save_analysis(
            photo_id=photo.id,
            faces_count=analysis.faces_count,
            eyes_closed_count=analysis.eyes_closed_count,
            is_blurred=analysis.is_blurred,
            blur_score=analysis.blur_score,
            perceptual_hash=phash or analysis.perceptual_hash,
            sha256_hash=sha256,
            dominant_color=analysis.dominant_color,
            tags=list(analysis.tags) if analysis.tags else None,
            model_version=analysis.model_version,
        )
        await db.update_photo_after_analysis(
            photo.id, PhotoStatuses.done, preview_key=preview_key,
        )

        logger.info("Photo %s processed successfully", photo_id)

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
        else:
            logger.info(
                "Photo %s will be retried (attempt %d/%d)",
                photo_id, attempts, MAX_RETRIES,
            )
            raise
