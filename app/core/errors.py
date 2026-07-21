from typing import Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    details: Optional[dict[str, Any]] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
    request_id: Optional[str] = None

class ErrorCodes:

    # 400
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"

    # 404
    PHOTO_NOT_FOUND = "PHOTO_NOT_FOUND"

    # 409
    DUPLICATE_ENTITY = "DUPLICATE_ENTITY"
    CONFLICT_STATE = "CONFLICT_STATE"

    # 500
    INTERNAL_ERROR = "INTERNAL_ERROR"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    STORAGE_TIMEOUT = "STORAGE_TIMEOUT"
    BUCKET_ERROR = "BUCKET_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    DATABASE_CANT_CREATE = "DATABASE_CANT_CREATE" 
    DATABASE_CANT_EXECUTE = "DATABASE_CANT_EXECUTE" 
    DATABASE_CANT_GET = "DATABASE_CANT_GET" 
    PHOTO_NOT_ADD_TO_STORAGE = "PHOTO_NOT_ADD_TO_STORAGE"
    PHOTO_NOT_TAKEN_FROM_STORAGE = "PHOTO_NOT_TAKEN_FROM_STORAGE"
    PHOTO_URL_NOT_TAKEN = "PHOTO_URL_NOT_TAKEN"

class AppException(HTTPException):

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        field: Optional[str] = None,
        details: Optional[dict] = None,
        headers: Optional[dict] = None,
    ):
        self.error_code = code
        self.error_message = message
        self.error_field = field
        self.error_details = details
        super().__init__(status_code=status_code, detail=message, headers=headers)

    def to_error_response(self, request_id: Optional[str] = None) -> ErrorResponse:
        return ErrorResponse(
            error=ErrorDetail(
                code=self.error_code,
                message=self.error_message,
                field=self.error_field,
                details=self.error_details,
            ),
            request_id=request_id,
        )

class PhotoNotFoundError(AppException):
    def __init__(self, photo_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=ErrorCodes.PHOTO_NOT_FOUND,
            message=f"Photo '{photo_id}' not found",
            details={"photo_id": photo_id},
        )

class InvalidFile(AppException):
    def __init__(self, content_type: str):
        super().__init__(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            code=ErrorCodes.INVALID_FILE_TYPE,
            message=f"Unsupported file type: {content_type}",
            details={'content_type must be in': ["image/jpeg", "image/png", "image/jpg"]},
        )

class FileTooLarge(AppException):
    def __init__(self, size: int):
        super().__init__(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            code=ErrorCodes.FILE_TOO_LARGE,
            message=f"File size is too large: {size}",
            details={'content size must be under': '3 mb'},
        )

class DatabaseError(AppException):
    def __init__(self, cause: str, code: ErrorCodes = ErrorCodes.DATABASE_ERROR):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=code,
            message=f"Database error: {cause}",
            details={"cause": cause},
        )

class StorageError(AppException):
    def __init__(self, cause: str, code: ErrorCodes):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            code=code,
            message=f"Minio error: {cause}",
            details={"cause": cause},
        )
    