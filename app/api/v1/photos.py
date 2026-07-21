from fastapi import APIRouter, Depends, status, Request
from fastapi import UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession


from app.database.database import get_session
from app.integrations.postgreesql import PhotoDatabase
from app.schemas.photos import UploadPhotosResponse, GetPhotosListResponse, GetPhotosByIDResponse, GetPhotoContentByIDResponse, PhotoItem
from app.services.photos_service import PhotoService
from app.api.depends import get_current_user


router = APIRouter(prefix='/api/v1/photos')


def get_photo_service(request: Request, session: AsyncSession = Depends(get_session)) -> PhotoService:
    database = PhotoDatabase(session)
    storage = request.app.state.storage
    kafka = request.app.state.kafka
    return PhotoService(database=database, storage=storage, kafka=kafka)

@router.post('/', status_code=status.HTTP_202_ACCEPTED, response_model=UploadPhotosResponse)
async def upload_photo(
    photo: UploadFile = File(...),
    service: PhotoService = Depends(get_photo_service),
    owner_token: str | None = Depends(get_current_user),
) -> UploadPhotosResponse:
    photo = await service.create_photo(photo, owner_data_token=owner_token)
    return UploadPhotosResponse(photo_id=photo.id_string, status='pending')



@router.get('/', status_code=status.HTTP_200_OK, response_model=GetPhotosListResponse)
async def list_photos(
    service: PhotoService = Depends(get_photo_service),
    owner_token: str | None = Depends(get_current_user),
) -> GetPhotosListResponse:
    photos = await service.list_photos(owner_data_token=owner_token)

    
    return GetPhotosListResponse(photos=photos)


@router.get('/{string_id}', status_code=status.HTTP_200_OK, response_model=GetPhotosByIDResponse)
async def get_photo_by_id(
    string_id: str,
    service: PhotoService = Depends(get_photo_service),
    owner_token: str | None = Depends(get_current_user),
) -> GetPhotosByIDResponse:
    photo = await service.get_photo_by_id(string_id=string_id, owner_data_token=owner_token)
    return GetPhotosByIDResponse(**photo)



@router.get('/{string_id}/content', status_code=status.HTTP_200_OK, response_model=GetPhotoContentByIDResponse)
async def get_photo_content_by_id(
    string_id: str,
    service: PhotoService = Depends(get_photo_service),
    owner_token: str | None = Depends(get_current_user),
) -> GetPhotoContentByIDResponse:
    photo = await service.get_photo_content_by_id(string_id=string_id, owner_data_token=owner_token)
    return GetPhotoContentByIDResponse(**photo)

