"""查询执行与历史：POST /api/query/execute, GET /api/query/history, GET /api/query/history/{id}"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Request, Query, Path
from pydantic import BaseModel

from app.api.deps import DbSession, CurrentUser
from app.core.exceptions import NotFoundError
from app.core.response import success_response
from app.services.query_executor_service import QueryExecutorService
from app.services.result_parser_service import ResultParserService
from app.services.analysis_service import ResultAnalysisService
from app.services.payload_store_service import PayloadStoreService

router = APIRouter()


class ExecuteQueryRequest(BaseModel):
    interfaceCode: str
    params: dict = {}
    envCode: str = "prod"


@router.post("/execute")
def execute_query(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    body: ExecuteQueryRequest,
):
    svc = QueryExecutorService()
    trace_id = getattr(request.state, "trace_id", None)
    result = svc.execute(
        interface_code=body.interfaceCode,
        params=body.params,
        env_code=body.envCode,
        trigger_type="WEB",
        operator_user_id=current_user.id,
        trace_id=trace_id,
    )
    return result


@router.get("/history")
def query_history(
    db: DbSession,
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    interface_code: Optional[str] = Query(None),
    success_flag: Optional[int] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
):
    from app.models.query_record import DqQueryRecord
    from app.models.interface_config import DqInterfaceConfig

    q = db.query(DqQueryRecord, DqInterfaceConfig).join(
        DqInterfaceConfig, DqInterfaceConfig.id == DqQueryRecord.interface_id, isouter=True
    )
    if interface_code:
        q = q.filter(DqQueryRecord.interface_code == interface_code)
    if success_flag is not None:
        q = q.filter(DqQueryRecord.success_flag == success_flag)
    if start_time:
        dt = datetime.fromisoformat(start_time)
        q = q.filter(DqQueryRecord.created_at >= dt)
    if end_time:
        dt = datetime.fromisoformat(end_time)
        q = q.filter(DqQueryRecord.created_at <= dt)

    total = q.count()
    rows = (
        q.order_by(DqQueryRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return success_response(
        data={
            "list": [
                {
                    "id": r.id,
                    "traceId": r.trace_id,
                    "interfaceCode": r.interface_code,
                    "interfaceName": (i.interface_name if i else None),
                    "triggerType": r.trigger_type,
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
    )


@router.get("/history/{id}")
def query_history_detail(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    from app.models.query_record import DqQueryRecord

    r = db.query(DqQueryRecord).filter(DqQueryRecord.id == id).first()
    if not r:
        return success_response(data=None, message="记录不存在")
    return success_response(
        data={
            "id": r.id,
            "traceId": r.trace_id,
            "interfaceCode": r.interface_code,
            "triggerType": r.trigger_type,
            "successFlag": r.success_flag,
            "durationMs": r.duration_ms,
            "createdAt": r.created_at.isoformat() if r.created_at else None,
            "requestPlain": r.request_plain_text,
            "requestCipher": r.request_cipher_text,
            "requestHeaders": r.request_headers_text,
            "responsePlain": r.response_plain_text,
            "responsePlainPreview": getattr(r, "response_plain_preview", None),
            "responseRaw": r.response_raw_text,
            "responseRawPreview": getattr(r, "response_raw_preview", None),
            "responseRawSize": getattr(r, "response_raw_size", None),
            "responsePlainSize": getattr(r, "response_plain_size", None),
            "payloadStoreMode": getattr(r, "payload_store_mode", None),
            "payloadStorePath": getattr(r, "payload_store_path", None),
            "responseCode": r.response_code,
            "responseMessage": r.response_message,
            "errorMessage": r.error_message,
            "httpStatusCode": r.http_status_code,
            "startedAt": r.started_at.isoformat() if r.started_at else None,
            "finishedAt": r.finished_at.isoformat() if r.finished_at else None,
            "extJson": r.ext_json,
        }
    )


@router.get("/history/{id}/payload", include_in_schema=False)
def query_history_payload(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
    kind: str = Query("response_raw"),  # response_raw / response_plain / request_plain / request_cipher
):
    from app.models.query_record import DqQueryRecord

    r = db.query(DqQueryRecord).filter(DqQueryRecord.id == id).first()
    if not r:
        return success_response(data=None, message="记录不存在")

    payload = PayloadStoreService().load_record_text(r, kind)
    data = {"kind": kind, "source": payload.source, "text": payload.text}
    if payload.path:
        data["path"] = payload.path
    return success_response(data=data)


@router.get("/history/{id}/structured-view")
def query_history_structured_view(
    db: DbSession,
    current_user: CurrentUser,
    id: int = Path(...),
):
    """
    基于历史记录中已保存的解密结果，重新套用当前接口的「结果展示配置」与自动统计，
    供查询历史详情页表格化/图表化展示（不再次调用远程接口）。
    """
    from app.models.query_record import DqQueryRecord
    from app.models.interface_config import DqInterfaceConfig

    r = db.query(DqQueryRecord).filter(DqQueryRecord.id == id).first()
    if not r:
        raise NotFoundError("记录不存在")
    iface = (
        db.query(DqInterfaceConfig)
        .filter(DqInterfaceConfig.id == r.interface_id, DqInterfaceConfig.deleted_flag == 0)
        .first()
    )
    if not iface:
        raise NotFoundError("接口配置不存在")

    decrypted = PayloadStoreService().load_record_json(r)

    parsed = ResultParserService().parse(iface, decrypted, {})
    analysis = ResultAnalysisService().analyze(
        parsed.list,
        parsed.stats_config,
        duration_ms=r.duration_ms or 0,
        success=r.success_flag == 1,
        page=parsed.page,
        page_size=parsed.page_size,
        total=parsed.total,
    )
    return success_response(
        data={
            "recordId": r.id,
            "traceId": r.trace_id,
            "interfaceCode": r.interface_code,
            "successFlag": r.success_flag,
            "resultMode": parsed.result_mode,
            "display": {
                "resultMode": parsed.result_mode,
                "columns": parsed.columns,
                "detailSections": parsed.detail_sections,
            },
            "list": parsed.list,
            "total": parsed.total,
            "analysis": analysis,
        }
    )
