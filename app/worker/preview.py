import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)

PREVIEW_MAX_WIDTH = 800
PREVIEW_QUALITY = 75


def generate(image_data: bytes) -> bytes:
    img = Image.open(io.BytesIO(image_data))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    if img.width > PREVIEW_MAX_WIDTH:
        ratio = PREVIEW_MAX_WIDTH / img.width
        new_height = int(img.height * ratio)
        img = img.resize((PREVIEW_MAX_WIDTH, new_height), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=PREVIEW_QUALITY, optimize=True)
    preview_data = buf.getvalue()

    logger.info("Preview generated: %dx%d -> %d bytes", img.width, img.height, len(preview_data))
    return preview_data
