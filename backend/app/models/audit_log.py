"""审计日志表 dq_audit_log"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DqAuditLog(Base):
    __tablename__ = "dq_audit_log"
    __table_args__ = {"comment": "审计日志表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    operator_user_id: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="操作用户ID")
    operator_name: Mapped[str | None] = mapped_column(String(64), default=None, comment="操作人姓名")
    module_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="模块名称")
    operation_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="操作类型")
    target_type: Mapped[str] = mapped_column(String(64), nullable=False, comment="目标类型")
    target_id: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="目标ID")
    target_code: Mapped[str | None] = mapped_column(String(128), default=None, comment="目标编码")
    operation_content: Mapped[str | None] = mapped_column(Text, default=None, comment="操作内容")
    request_ip: Mapped[str | None] = mapped_column(String(64), default=None, comment="请求IP")
    success_flag: Mapped[int] = mapped_column(default=1, nullable=False, comment="是否成功")
    error_message: Mapped[str | None] = mapped_column(String(1000), default=None, comment="失败原因")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, comment="创建时间")
