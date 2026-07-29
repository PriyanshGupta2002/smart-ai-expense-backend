from fastapi import Response

from app.core.config import settings


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
        path="/",
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=(settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),
        path="/auth",
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie(
        "access_token",
        path="/",
    )

    response.delete_cookie(
        "refresh_token",
        path="/auth",
    )
