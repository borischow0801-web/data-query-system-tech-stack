"""统一响应结构。"""
from typing import Any, Optional
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """统一 API 响应格式"""

    success: bool = True
    code: str = "0"
    message: str = "success"
    trace_id: Optional[str] = Field(None, alias="traceId")
    data: Optional[Any] = None

    class Config:
        populate_by_name = True


def success_response(
    data: Any = None,
    message: str = "success",
    trace_id: Optional[str] = None,
) -> dict:
    return {
        "success": True,
        "code": "0",
        "message": message,
        "traceId": trace_id,
        "data": data,
    }


def error_response(
    message: str = "error",
    code: str = "1",
    trace_id: Optional[str] = None,
    data: Any = None,
) -> dict:
    return {
        "success": False,
        "code": code,
        "message": message,
        "traceId": trace_id,
        "data": data,
    }
