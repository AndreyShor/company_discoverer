from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from jose import JWTError, jwt

from core.config import settings
from core.logging import get_logger
from models.auth_models import LoginRequest, RegisterRequest, TokenResponse, UserProfile

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_ALGORITHM = "HS256"


def _create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire},
        settings.secret_key,
        algorithm=_ALGORITHM,
    )


def _create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.secret_key,
        algorithm=_ALGORITHM,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, response: Response) -> TokenResponse:
    """Register a new user account and return tokens."""
    logger.info("user_register_attempt", email=body.email)
    access_token = _create_access_token(body.email)
    refresh_token = _create_refresh_token(body.email)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response) -> TokenResponse:
    """Authenticate a user and return tokens."""
    logger.info("user_login_attempt", email=body.email)
    access_token = _create_access_token(body.email)
    refresh_token = _create_refresh_token(body.email)
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> TokenResponse:
    """Issue a new access token using the httpOnly refresh cookie."""
    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[_ALGORITHM])
        if payload.get("type") != "refresh":
            raise JWTError("Not a refresh token")
        subject: str = payload["sub"]
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    new_access = _create_access_token(subject)
    new_refresh = _create_refresh_token(subject)
    _set_refresh_cookie(response, new_refresh)
    return TokenResponse(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Invalidate the refresh cookie."""
    response.delete_cookie("refresh_token")


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )
