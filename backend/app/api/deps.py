"""API 依赖：DB、当前用户、trace_id、开放 API 客户端等。"""
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.utils.trace_util import generate_trace_id
from app.core.security import get_current_user, authenticate_openapi_client
from app.models.user import DqUser
from app.models.open_api_client import DqOpenApiClient

# 类型别名便于注入
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[DqUser, Depends(get_current_user)]


def _openapi_client_dep(
    db: DbSession,
    x_app_key: str = Header(..., alias="X-App-Key", description="开放客户端 AppKey"),
    x_app_secret: str = Header(..., alias="X-App-Secret", description="开放客户端 AppSecret"),
) -> DqOpenApiClient:
    return authenticate_openapi_client(db, x_app_key, x_app_secret)


OpenApiClient = Annotated[DqOpenApiClient, Depends(_openapi_client_dep)]


def get_trace_id(request: Request) -> str:
    """优先从 request.state 中获取 traceId。"""
    trace_id = getattr(request.state, "trace_id", None)
    return trace_id or generate_trace_id()

