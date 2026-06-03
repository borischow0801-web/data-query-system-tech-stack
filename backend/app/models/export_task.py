"""导出任务表 dq_export_task"""
from datetime import datetime

from sqlalchemy import BigInteger, JSON, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DqExportTask(Base):
    __tablename__ = "dq_export_task"
    __table_args__ = {"comment": "导出任务表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    task_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="任务编号")
    interface_id: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="接口配置ID")
    query_record_id: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="关联查询记录ID")
    operator_user_id: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="操作用户ID")
    export_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="导出类型")
    export_scope: Mapped[str] = mapped_column(String(32), default="RESULT", nullable=False, comment="导出范围")
    file_name: Mapped[str | None] = mapped_column(String(255), default=None, comment="文件名")
    file_path: Mapped[str | None] = mapped_column(String(500), default=None, comment="文件路径")
    file_size: Mapped[int | None] = mapped_column(default=None, comment="文件大小字节")
    task_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, comment="任务状态")
    failure_reason: Mapped[str | None] = mapped_column(String(1000), default=None, comment="失败原因")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="结束时间")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, comment="创建时间")
