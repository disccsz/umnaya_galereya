from app.core.errors import AppException, ErrorResponse, ErrorDetail

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.photos import router



app = FastAPI(title="Photo Service", version="0.1.0")

app.include_router(router)



@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Перехватывает все AppException и возвращает единый JSON."""
    error_response = exc.to_error_response(
        request_id=request.headers.get("X-Request-ID")
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Глобальный fallback для непредвиденных ошибок."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
        ),
        request_id=request.headers.get("X-Request-ID"),
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )