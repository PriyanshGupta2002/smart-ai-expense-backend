from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session
from app.schemas.user import UserProfileUpdateResponse, UserProfileUpdateRequest
from app.core.dependencies import get_db, get_user_service, get_current_user

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/update-profile", response_model=UserProfileUpdateResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    user_service = get_user_service(db=db)
    user = user_service.update_user_details(
        user=user,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return UserProfileUpdateResponse.model_validate(user)


@router.post("/upload-profile-photo", response_model=UserProfileUpdateResponse)
def update_profile_photo(
    file: UploadFile,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    user_service = get_user_service(db=db)
    user = user_service.upload_profile_image(user=user, file=file)
    return UserProfileUpdateResponse.model_validate(user)
