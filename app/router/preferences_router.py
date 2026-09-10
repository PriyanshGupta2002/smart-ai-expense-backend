from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.core.dependencies import (
    get_user_preferences_service,
)
from app.schemas.user_preferences import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
)
from app.services.user_preferences_service import (
    UserPreferencesService,
)

router = APIRouter(
    prefix="/preferences",
    tags=["Preferences"],
)


@router.get(
    "",
    response_model=UserPreferencesResponse,
)
def get_preferences(
    user=Depends(get_current_user),
    service: UserPreferencesService = Depends(get_user_preferences_service),
):
    return service.get_or_create(user.id)


@router.put(
    "",
    response_model=UserPreferencesResponse,
)
def update_preferences(
    data: UserPreferencesUpdate,
    user=Depends(get_current_user),
    service: UserPreferencesService = Depends(get_user_preferences_service),
):
    return service.update(
        user_id=user.id,
        data=data,
    )
