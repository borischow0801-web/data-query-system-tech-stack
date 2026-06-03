"""
开放 API：供其他业务系统调用的统一查询/导出能力。
认证：请求头 X-App-Key、X-App-Secret（见 docs/open-api-doc.md）。
"""
from __future__ import annotations

import time
from typing import Any, Literal, Optional

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.api.deps import DbSession, OpenApiClient
from app.core.exceptions import NotFoundError, ValidationError
from app.core.response import success_response
from app.models.export_task import DqExportTask
from app.models.interface_config import DqInterfaceConfig
from app.models.query_record import DqQueryRecord
from app.services.export_task_service import create_export_task_from_record
from app.services.open_api_call_log_service import write_open_api_call_log
from app.services.query_executor_service import QueryExecutorService

router = APIRouter(tags=["开放API（业务系统对接）"])


def _wrap_open_api_query_response(exec_result: dict[str, Any]) -> dict[str, Any]:
    """对外查询：标准 envelope，业务数据在 data.result，不返回 rawData。"""
    inner = exec_result.get("data")
    data = {
        "interfaceCode": exec_result.get("interfaceCode"),
        "durationMs": exec_result.get("durationMs"),
        "queryRecordId": exec_result.get("queryRecordId"),
        "result": inner,
    }
    return {
        "success": exec_result["success"],
        "code": str(exec_result.get("code", "0")),
        "message": exec_result.get("message", "success"),
        "traceId": exec_result.get("traceId"),
        "data": data,
    }


class OpenApiQueryRequest(BaseModel):
    """开放查询请求体（调用方只需关心接口编码与业务参数）。"""

    interfaceCode: str = Field(..., description="已在平台配置且勾选「允许开放 API」的接口编码")
    params: dict[str, Any] = Field(default_factory=dict, description="业务查询参数键值，与参数模板一致")
    envCode: str = Field("prod", description="环境编码，与接口配置中 envCode 一致")


@router.get(
    "/interfaces",
    summary="获取可对外的接口清单",
    description="返回已启用且允许开放调用的接口编码与名称，供调用方选型。",
)
def open_api_list_interfaces(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
):
    trace_id = getattr(request.state, "trace_id", None)
    t0 = time.time()
    rows = (
        db.query(DqInterfaceConfig)
        .filter(
            DqInterfaceConfig.deleted_flag == 0,
            DqInterfaceConfig.status == 1,
            DqInterfaceConfig.allow_open_api == 1,
        )
        .order_by(DqInterfaceConfig.interface_code.asc())
        .all()
    )
    data = {
        "list": [
            {
                "interfaceCode": r.interface_code,
                "interfaceName": r.interface_name,
                "envCode": r.env_code,
                "interfaceCategory": r.interface_category,
            }
            for r in rows
        ]
    }
    duration_ms = int((time.time() - t0) * 1000)
    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=trace_id or "",
        interface_code="_list_",
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params=None,
        success_flag=1,
        duration_ms=duration_ms,
        response_summary={"count": len(rows)},
    )
    return success_response(data=data, trace_id=trace_id)


@router.post(
    "/query",
    summary="执行统一查询",
    description="按 interfaceCode 与业务参数发起查询；加密、远程报文格式由平台在内部完成。",
)
def open_api_query(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
    body: OpenApiQueryRequest,
):
    trace_id = getattr(request.state, "trace_id", None)
    iface = (
        db.query(DqInterfaceConfig)
        .filter(
            DqInterfaceConfig.interface_code == body.interfaceCode,
            DqInterfaceConfig.env_code == body.envCode,
            DqInterfaceConfig.deleted_flag == 0,
            DqInterfaceConfig.status == 1,
        )
        .first()
    )
    if not iface:
        raise NotFoundError(f"接口不存在或未启用: {body.interfaceCode}/{body.envCode}")
    if iface.allow_open_api != 1:
        raise ValidationError("该接口未对开放 API 启用，请联系管理员")

    t0 = time.time()
    svc = QueryExecutorService()
    result = svc.execute(
        interface_code=body.interfaceCode,
        params=body.params,
        env_code=body.envCode,
        trigger_type="OPEN_API",
        trigger_client_id=client.id,
        trace_id=trace_id,
    )
    duration_ms = int((time.time() - t0) * 1000)

    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=result.get("traceId") or trace_id or "",
        interface_code=body.interfaceCode,
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params={"interfaceCode": body.interfaceCode, "params": body.params, "envCode": body.envCode},
        success_flag=1 if result.get("success") else 0,
        duration_ms=duration_ms,
        query_record_id=result.get("queryRecordId"),
        error_message=None if result.get("success") else result.get("message"),
        response_summary={"success": result.get("success"), "code": result.get("code")},
    )
    return _wrap_open_api_query_response(result)


@router.get(
    "/query/history",
    summary="查询历史（当前客户端）",
    description="仅返回本 AppKey 通过开放 API 产生的查询记录摘要。",
)
def open_api_query_history(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    interface_code: Optional[str] = Query(None, alias="interfaceCode"),
    success_flag: Optional[int] = Query(None, alias="successFlag"),
):
    trace_id = getattr(request.state, "trace_id", None)
    t0 = time.time()
    q = db.query(DqQueryRecord, DqInterfaceConfig).join(
        DqInterfaceConfig, DqInterfaceConfig.id == DqQueryRecord.interface_id, isouter=True
    ).filter(
        DqQueryRecord.trigger_type == "OPEN_API",
        DqQueryRecord.trigger_client_id == client.id,
    )
    if interface_code:
        q = q.filter(DqQueryRecord.interface_code == interface_code)
    if success_flag is not None:
        q = q.filter(DqQueryRecord.success_flag == success_flag)

    total = q.count()
    rows = (
        q.order_by(DqQueryRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = {
        "list": [
            {
                "id": r.id,
                "traceId": r.trace_id,
                "interfaceCode": r.interface_code,
                "interfaceName": (i.interface_name if i else None),
                "successFlag": r.success_flag,
                "durationMs": r.duration_ms,
                "responseCode": r.response_code,
                "responseMessage": r.response_message,
                "errorMessage": r.error_message,
                "createdAt": r.created_at.isoformat() if r.created_at else None,
            }
            for (r, i) in rows
        ],
        "total": total,
        "page": page,
        "pageSize": page_size,
    }
    duration_ms = int((time.time() - t0) * 1000)
    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=trace_id or "",
        interface_code="_history_",
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params={"page": page, "pageSize": page_size},
        success_flag=1,
        duration_ms=duration_ms,
        response_summary={"total": total},
    )
    return success_response(data=data, trace_id=trace_id)


@router.get(
    "/query/history/{history_id}",
    summary="单条查询记录详情（当前客户端）",
    description="不包含加解密中间报文，仅摘要字段，便于对账与排错。",
)
def open_api_query_history_detail(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
    history_id: int = Path(..., description="查询历史记录主键 id"),
):
    trace_id = getattr(request.state, "trace_id", None)
    t0 = time.time()
    r = (
        db.query(DqQueryRecord)
        .filter(
            DqQueryRecord.id == history_id,
            DqQueryRecord.trigger_type == "OPEN_API",
            DqQueryRecord.trigger_client_id == client.id,
        )
        .first()
    )
    if not r:
        raise NotFoundError("记录不存在或无权访问")
    data = {
        "id": r.id,
        "traceId": r.trace_id,
        "interfaceCode": r.interface_code,
        "successFlag": r.success_flag,
        "durationMs": r.duration_ms,
        "createdAt": r.created_at.isoformat() if r.created_at else None,
        "responseCode": r.response_code,
        "responseMessage": r.response_message,
        "errorMessage": r.error_message,
        "httpStatusCode": r.http_status_code,
    }
    duration_ms = int((time.time() - t0) * 1000)
    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=trace_id or "",
        interface_code="_history_detail_",
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params={"historyId": history_id},
        success_flag=1,
        duration_ms=duration_ms,
    )
    return success_response(data=data, trace_id=trace_id)


class OpenApiExportBody(BaseModel):
    queryRecordId: int = Field(..., description="开放 API 查询产生的记录 ID")
    exportType: Literal["csv", "xlsx"] = "csv"


@router.post(
    "/export",
    summary="创建导出任务",
    description="仅允许导出属于当前客户端、且执行成功的查询记录。",
)
def open_api_create_export(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
    body: OpenApiExportBody,
):
    trace_id = getattr(request.state, "trace_id", None)
    t0 = time.time()
    record = db.query(DqQueryRecord).filter(DqQueryRecord.id == body.queryRecordId).first()
    if not record or record.trigger_client_id != client.id or record.trigger_type != "OPEN_API":
        raise NotFoundError("查询记录不存在或无权导出")
    task = create_export_task_from_record(
        db,
        record,
        body.exportType,
        operator_user_id=None,
        ext_json={"openApiClientId": client.id},
    )
    duration_ms = int((time.time() - t0) * 1000)
    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=trace_id or "",
        interface_code="_export_",
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params={"queryRecordId": body.queryRecordId, "exportType": body.exportType},
        success_flag=1,
        duration_ms=duration_ms,
        query_record_id=record.id,
        response_summary={"taskId": task.task_no},
    )
    return success_response(
        data={
            "taskId": task.task_no,
            "status": task.task_status,
            "fileName": task.file_name,
            "downloadPath": f"/open-api/export/files/{task.file_name}",
        },
        trace_id=trace_id,
    )


@router.get(
    "/export/files/{file_name}",
    summary="下载导出文件",
    description="需携带与创建任务相同的 X-App-Key / X-App-Secret。",
)
def open_api_export_download(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
    file_name: str = Path(...),
):
    from app.core.config import get_settings
    import os

    trace_id = getattr(request.state, "trace_id", None)
    candidates = db.query(DqExportTask).filter(DqExportTask.file_name == file_name).all()
    row = next(
        (
            r
            for r in candidates
            if r.ext_json and r.ext_json.get("openApiClientId") == client.id
        ),
        None,
    )
    if not row:
        raise NotFoundError("文件不存在或无权下载")

    settings = get_settings()
    base_dir = os.path.abspath(settings.export_storage_path)
    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        raise NotFoundError("文件不存在")

    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=trace_id or "",
        interface_code="_export_file_",
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params={"fileName": file_name},
        success_flag=1,
        duration_ms=0,
    )
    return FileResponse(path=file_path, filename=file_name)


@router.get(
    "/export/{task_id}",
    summary="查询导出任务状态",
)
def open_api_export_status(
    request: Request,
    db: DbSession,
    client: OpenApiClient,
    task_id: str = Path(..., description="创建导出时返回的 taskId"),
):
    trace_id = getattr(request.state, "trace_id", None)
    row = db.query(DqExportTask).filter(DqExportTask.task_no == task_id).first()
    if not row or not row.ext_json or row.ext_json.get("openApiClientId") != client.id:
        raise NotFoundError("导出任务不存在或无权访问")
    duration_ms = 0
    write_open_api_call_log(
        db,
        request=request,
        client=client,
        trace_id=trace_id or "",
        interface_code="_export_status_",
        request_uri=str(request.url.path),
        request_method=request.method,
        request_params={"taskId": task_id},
        success_flag=1,
        duration_ms=duration_ms,
    )
    return success_response(
        data={
            "taskId": row.task_no,
            "status": row.task_status,
            "fileName": row.file_name,
            "downloadPath": f"/open-api/export/files/{row.file_name}" if row.file_name else None,
            "failureReason": row.failure_reason,
            "fileSize": row.file_size,
        },
        trace_id=trace_id,
    )
