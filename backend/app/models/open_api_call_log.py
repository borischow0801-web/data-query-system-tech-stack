"""开放API调用日志表 dq_open_api_call_log"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DqOpenApiCallLog(Base):
    __tablename__ = "dq_open_api_call_log"
    __table_args__ = {"comment": "开放API调用日志表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="链路追踪ID")
    client_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True, comment="开放客户端ID")
    client_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="客户端编码冗余")
    interface_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="调用的接口编码")
    request_uri: Mapped[str | None] = mapped_column(String(255), default=None, comment="请求URI")
    request_method: Mapped[str | None] = mapped_column(String(16), default=None, comment="请求方法")
    request_ip: Mapped[str | None] = mapped_column(String(64), default=None, comment="请求IP")
    request_params_text: Mapped[str | None] = mapped_column(Text, default=None, comment="请求参数")
    response_text: Mapped[str | None] = mapped_column(Text, default=None, comment="响应内容")
    http_status_code: Mapped[int | None] = mapped_column(default=None, comment="HTTP状态码")
    success_flag: Mapped[int] = mapped_column(default=0, nullable=False, comment="是否成功")
    duration_ms: Mapped[int | None] = mapped_column(default=None, comment="耗时毫秒")
    error_message: Mapped[str | None] = mapped_column(String(1000), default=None, comment="错误信息")
    query_record_id: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="关联查询记录ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, comment="创建时间")
