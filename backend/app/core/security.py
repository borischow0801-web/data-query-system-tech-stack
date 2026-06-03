"""安全与认证相关工具：密码哈希、JWT、当前用户/客户端依赖。"""
from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.db.session import get_db
from app.models.user import DqUser
from app.models.open_api_client import DqOpenApiClient


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """生成 JWT access token。"""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.algorithm
    )
    return encoded_jwt


def _get_user_by_username(db: Session, username: str) -> Optional[DqUser]:
    return (
        db.query(DqUser)
        .filter(DqUser.username == username, DqUser.deleted_flag == 0)
        .first()
    )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> DqUser:
    """从 Authorization Bearer token 中解析当前用户。"""
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = _get_user_by_username(db, username)
    if user is None or user.status != 1:
        raise credentials_exception
    return user


async def get_optional_current_user(
    token: Annotated[Optional[str], Depends(oauth2_scheme)] = None,
    db: Annotated[Session, Depends(get_db)] = None,
) -> Optional[DqUser]:
    if not token or not db:
        return None
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


def authenticate_openapi_client(db: Session, app_key: str, app_secret: str) -> DqOpenApiClient:
    """开放 API 客户端鉴权：请求头 X-App-Key + X-App-Secret（当前为明文比对，与库中 app_secret_hash 字段存储值一致）。"""
    client = (
        db.query(DqOpenApiClient)
        .filter(
            DqOpenApiClient.app_key == app_key,
            DqOpenApiClient.deleted_flag == 0,
        )
        .first()
    )
    if not client or client.status != 1:
        raise UnauthorizedError("开放客户端不可用")
    if client.app_secret_hash != app_secret:
        raise UnauthorizedError("开放客户端凭证错误")
    return client

