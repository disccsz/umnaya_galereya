import time
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import AppException, ErrorResponse, ErrorDetail
from app.core.log import setup_logging
from app.api.v1.photos import router


logger = logging.getLogger(__name__)

setup_logging()

app = FastAPI(title="Photo Service", version="0.1.0")

app.include_router(router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or "-"
    start = time.time()

    response = await call_next(request)

    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "%s %s → %s (%sms)",
        request.method, request.url.path, response.status_code, duration_ms,
        extra={"request_id": request_id},
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID")
    logger.warning(
        "%s: %s", exc.error_code, exc.error_message,
        extra={"request_id": request_id or "-"},
    )
    error_response = exc.to_error_response(request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = request.headers.get("X-Request-ID")
    logger.critical(
        "Unhandled exception", exc_info=exc,
        extra={"request_id": request_id or "-"},
    )
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )
