from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
)

from app.core.dependencies import get_auth_service
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==========================================
# Register
# ==========================================


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.register(payload)

    return user


# ==========================================
# Login
# ==========================================


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
def login(
    payload: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    auth_service.login(
        data=payload,
        response=response,
    )

    return {"message": "Login successful"}


# ==========================================
# Refresh
# ==========================================


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
)
def refresh(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):

    refresh_token = request.cookies.get("refresh_token")

    auth_service.refresh(
        refresh_token=refresh_token,
        response=response,
    )

    return {"message": "Token refreshed"}


# ==========================================
# Logout
# ==========================================


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):

    refresh_token = request.cookies.get("refresh_token")

    auth_service.logout(
        refresh_token=refresh_token,
        response=response,
    )

    return {"message": "Logged out"}
