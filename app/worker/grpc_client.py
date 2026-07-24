import logging

import grpc

from app.core.config import settings
from app.worker.gen import analyzer_pb2
from app.worker.gen import analyzer_pb2_grpc

logger = logging.getLogger(__name__)


async def analyze(photo_id: str, object_key: str, image_bytes: bytes) -> analyzer_pb2.AnalyzePhotoResponse:
    timeout = settings.SERVICE_TIMEOUT
    target = settings.ANALYSIS_GRPC_URL

    if not target:
        raise RuntimeError("ANALYSIS_GRPC_URL is not configured")

    logger.info("Calling gRPC AnalyzePhoto: photo_id=%s, object_key=%s", photo_id, object_key)

    async with grpc.aio.insecure_channel(target) as channel:
        stub = analyzer_pb2_grpc.PhotoAnalyzerStub(channel)
        request = analyzer_pb2.AnalyzePhotoRequest(
            photo_id=photo_id,
            object_key=object_key,
            image_bytes=image_bytes,
        )

        try:
            response = await stub.AnalyzePhoto(request, timeout=timeout)
            logger.info(
                "gRPC response: faces=%d, blurred=%s",
                response.faces_count, response.is_blurred,
            )
            return response
        except grpc.aio.AioRpcError as e:
            logger.error("gRPC call failed: %s", e, exc_info=True)
            raise
