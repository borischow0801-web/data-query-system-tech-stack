"""开放 API 调用日志写入。"""
from __future__ import annotations

import json
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.open_api_call_log import DqOpenApiCallLog
from app.models.open_api_client import DqOpenApiClient
from app.utils.trace_util import generate_trace_id


def write_open_api_call_log(
    db: Session,
    *,
    request: Request | None,
    client: DqOpenApiClient,
    trace_id: str,
    interface_code: str,
    request_uri: str,
    request_method: str,
    request_params: dict[str, Any] | None,
    success_flag: int,
    duration_ms: int,
    http_status_code: int = 200,
    error_message: str | None = None,
    query_record_id: int | None = None,
    response_summary: dict[str, Any] | None = None,
) -> None:
    """写入 dq_open_api_call_log（简短摘要，避免大报文）。"""
    if not trace_id:
        trace_id = generate_trace_id()
    ip = None
    if request and request.client:
        ip = request.client.host
    params_text = None
    if request_params is not None:
        try:
            params_text = json.dumps(request_params, ensure_ascii=False)[:8000]
        except Exception:
            params_text = str(request_params)[:8000]
    resp_text = None
    if response_summary is not None:
        try:
            resp_text = json.dumps(response_summary, ensure_ascii=False)[:8000]
        except Exception:
            resp_text = str(response_summary)[:8000]

    row = DqOpenApiCallLog(
        trace_id=trace_id,
        client_id=client.id,
        client_code=client.client_code,
        interface_code=interface_code,
        request_uri=request_uri[:255] if request_uri else None,
        request_method=request_method[:16] if request_method else None,
        request_ip=ip,
        request_params_text=params_text,
        response_text=resp_text,
        http_status_code=http_status_code,
        success_flag=success_flag,
        duration_ms=duration_ms,
        error_message=(error_message or "")[:1000] if error_message else None,
        query_record_id=query_record_id,
    )
    db.add(row)
    db.commit()  # 开放 API 路由独立写日志，与 QueryExecutor 自管会话分离
