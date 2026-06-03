"""导出任务创建：管理端与开放 API 共用。"""
from __future__ import annotations

import os
import uuid
from datetime import datetime
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationError
from app.models.export_task import DqExportTask
from app.models.interface_config import DqInterfaceConfig
from app.models.query_record import DqQueryRecord
from app.services.result_parser_service import ResultParserService


def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _parse_record_to_list(
    db: Session, record: DqQueryRecord
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    iface = (
        db.query(DqInterfaceConfig)
        .filter(DqInterfaceConfig.id == record.interface_id, DqInterfaceConfig.deleted_flag == 0)
        .first()
    )
    if not iface:
        raise NotFoundError("接口配置不存在")
    try:
        import json

        decrypted_json = json.loads(record.response_plain_text) if record.response_plain_text else {}
    except Exception:
        decrypted_json = record.response_plain_text or {}
    parsed = ResultParserService().parse(iface, decrypted_json, request_params={})
    rows = parsed.list
    if not rows:
        return [], {"total": parsed.total, "summary": parsed.summary}
    if isinstance(rows[0], dict):
        return rows, {"total": parsed.total, "summary": parsed.summary}
    return [{"value": x} for x in rows], {"total": parsed.total, "summary": parsed.summary}


def create_export_task_from_record(
    db: Session,
    record: DqQueryRecord,
    export_type: Literal["csv", "xlsx"],
    *,
    operator_user_id: int | None = None,
    ext_json: dict[str, Any] | None = None,
) -> DqExportTask:
    """根据查询记录生成导出文件并落库任务（同步完成，状态 DONE）。"""
    if record.success_flag != 1:
        raise ValidationError("仅支持导出成功的查询记录")

    rows, meta = _parse_record_to_list(db, record)

    settings = get_settings()
    base_dir = os.path.abspath(settings.export_storage_path)
    _ensure_dir(base_dir)
    task_no = uuid.uuid4().hex
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"export_{record.interface_code}_{record.id}_{ts}.{export_type}"
    file_path = os.path.join(base_dir, file_name)

    if export_type == "csv":
        import csv

        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            else:
                f.write("")
    elif export_type == "xlsx":
        import pandas as pd

        df = pd.DataFrame(rows)
        df.to_excel(file_path, index=False)
    else:
        raise ValidationError("exportType 仅支持 csv/xlsx")

    st = os.stat(file_path)
    merged_ext = {"meta": meta}
    if ext_json:
        merged_ext.update(ext_json)

    task = DqExportTask(
        task_no=task_no,
        interface_id=record.interface_id,
        query_record_id=record.id,
        operator_user_id=operator_user_id,
        export_type=export_type.upper(),
        export_scope="RESULT",
        file_name=file_name,
        file_path=file_path,
        file_size=st.st_size,
        task_status="DONE",
        ext_json=merged_ext,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
