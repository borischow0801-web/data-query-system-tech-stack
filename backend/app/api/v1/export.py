"""导出：结构化列表导出（CSV / Excel），基于查询记录 dq_query_record。"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter, Path
from fastapi.responses import FileResponse

from app.api.deps import DbSession, CurrentUser
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.response import success_response
from app.models.export_task import DqExportTask
from app.models.query_record import DqQueryRecord
from app.services.export_task_service import create_export_task_from_record

router = APIRouter()


@router.post("")
def create_export_task(
    db: DbSession,
    current_user: CurrentUser,
    body: dict,
):
    """
    请求：
    - queryRecordId: 必填
    - exportType: csv / xlsx
    """
    record_id = body.get("queryRecordId")
    export_type: Literal["csv", "xlsx"] = body.get("exportType", "csv")
    if not record_id:
        from app.core.exceptions import ValidationError

        raise ValidationError("queryRecordId 不能为空")
    record = db.query(DqQueryRecord).filter(DqQueryRecord.id == int(record_id)).first()
    if not record:
        raise NotFoundError("查询记录不存在")

    task = create_export_task_from_record(
        db,
        record,
        export_type,
        operator_user_id=current_user.id,
    )

    return success_response(
        data={
            "taskId": task.task_no,
            "status": "DONE",
            "fileName": task.file_name,
            "fileUrl": f"/api/export/files/{task.file_name}",
        }
    )


@router.get("/files/{file_name}")
def download_export_file(
    current_user: CurrentUser,
    file_name: str = Path(...),
):
    settings = get_settings()
    base_dir = os.path.abspath(settings.export_storage_path)
    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        raise NotFoundError("文件不存在")
    return FileResponse(path=file_path, filename=file_name)


@router.get("/{task_id}")
def get_export_task(
    db: DbSession,
    current_user: CurrentUser,
    task_id: str = Path(..., alias="taskId"),
):
    row = db.query(DqExportTask).filter(DqExportTask.task_no == task_id).first()
    if not row:
        raise NotFoundError("导出任务不存在")
    return success_response(
        data={
            "taskId": row.task_no,
            "status": row.task_status,
            "fileName": row.file_name,
            "fileUrl": f"/api/export/files/{row.file_name}" if row.file_name else None,
            "failureReason": row.failure_reason,
            "fileSize": row.file_size,
        }
    )
