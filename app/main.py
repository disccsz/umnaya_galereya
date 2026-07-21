import time
import uuid
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.errors import AppException, ErrorResponse, ErrorDetail
from app.core.log import setup_logging
from app.core.context import request_id_var
from app.api.v1.photos import router
from app.api.v1.groups import router as groups_router

from contextlib import asynccontextmanager
from app.integrations.minio import MinIOStorage
from app.integrations.kafka import KafkaProducer

@asynccontextmanager
async def lifespan(app: FastAPI):
    storage = MinIOStorage()
    kafka = KafkaProducer()

    await storage.startup()
    await kafka.startup()

    app.state.storage = storage
    app.state.kafka = kafka
    
    yield
    await storage.shutdown()
    await kafka.shutdown() 


logger = logging.getLogger(__name__)

setup_logging()

app = FastAPI(title="Photo Service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.readyz import router as ready_router
from app.api.v1.healthz import router as health_router

app.include_router(ready_router) 
app.include_router(health_router)    # без префикса — ручка будет /healthz

app.include_router(router)
app.include_router(groups_router)

@app.middleware("http")
async def cors_pna(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = uuid.uuid4().hex[:12]
    request_id_var.set(request_id)

    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)

    logger.info("%s %s → %s (%sms)", request.method, request.url.path, response.status_code, duration_ms)
    response.headers["X-Request-ID"] = request_id
    return response

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = request_id_var.get()
    logger.warning("%s: %s", exc.error_code, exc.error_message)
    error_response = exc.to_error_response(request_id=request_id)
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = request_id_var.get()
    logger.critical("Unhandled exception", exc_info=exc)
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