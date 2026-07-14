from fastapi import APIRouter, Depends, status
from fastapi.responses import Response
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession


from app.database.database import get_session
from app.integrations.minio import storage
from app.integrations.postgreesql import PhotoDatabase
from app.schemas.photos import UploadPhotosResponse, GetPhotosListResponse
from app.services.photos_service import PhotoService


router = APIRouter(prefix='/api/v1/photos')

def get_photo_service(session: AsyncSession = Depends(get_session)) -> PhotoService:
    repository = PhotoDatabase(session)
    return PhotoService(repository, storage)

@router.post('', status_code=status.HTTP_202_ACCEPTED, response_model=UploadPhotosResponse)
async def upload_photo(file: UploadFile = File(...), service: PhotoService = Depends(get_photo_service)) -> UploadPhotosResponse:
    photo = await service.create_photo(file)
    return UploadPhotosResponse(photo_ids=[photo.id], status='pending')



