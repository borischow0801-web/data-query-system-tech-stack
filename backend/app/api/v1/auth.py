"""认证：登录与当前用户信息。"""
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import DbSession, CurrentUser
from app.core.config import get_settings
from app.core.response import success_response
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.models.user import DqUser

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: DbSession):
    """用户名密码登录，返回 JWT。"""
    user: DqUser | None = (
        db.query(DqUser)
        .filter(DqUser.username == body.username, DqUser.deleted_flag == 0)
        .first()
    )
    if not user or user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误"
        )

    settings = get_settings()
    access_token_expires = timedelta(
        minutes=settings.access_token_expire_minutes
    )
    token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return LoginResponse(access_token=token)


@router.get("/me")
def me(current_user: CurrentUser):
    """当前登录用户信息。"""
    return success_response(
        data={
            "id": current_user.id,
            "username": current_user.username,
            "realName": current_user.real_name,
            "mobile": current_user.mobile,
            "email": current_user.email,
        }
    )
