import hashlib
import io
import logging

from PIL import Image

logger = logging.getLogger(__name__)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def perceptual(data: bytes) -> str | None:
    try:
        img = Image.open(io.BytesIO(data))
        img = img.convert("L").resize((8, 8), Image.LANCZOS)

        pixels = list(img.getdata())
        avg = sum(pixels) / len(pixels)

        bits = "".join("1" if p > avg else "0" for p in pixels)
        phash = hex(int(bits, 2))[2:].zfill(16)
        logger.info("Perceptual hash: %s", phash)
        return phash
    except Exception as e:
        logger.warning("Perceptual hash failed: %s", e)
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    return (int(hash1, 16) ^ int(hash2, 16)).bit_count()
