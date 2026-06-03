"""通用 schema。"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponseSchema(BaseModel, Generic[T]):
    success: bool = True
    code: str = "0"
    message: str = "success"
    traceId: str | None = None
    data: T | None = None
