"""查询执行记录表 dq_query_record"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT, BIGINT
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DqQueryRecord(Base):
    __tablename__ = "dq_query_record"
    __table_args__ = {"comment": "查询执行记录表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="链路追踪ID")
    interface_id: Mapped[int] = mapped_column(nullable=False, index=True, comment="接口配置ID")
    interface_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="接口编码冗余")
    trigger_type: Mapped[str] = mapped_column(String(32), default="WEB", nullable=False, comment="触发来源")
    trigger_client_id: Mapped[int | None] = mapped_column(default=None, comment="开放客户端ID")
    operator_user_id: Mapped[int | None] = mapped_column(default=None, comment="操作用户ID")
    request_plain_text: Mapped[str | None] = mapped_column(LONGTEXT, default=None, comment="请求明文")
    request_cipher_text: Mapped[str | None] = mapped_column(LONGTEXT, default=None, comment="请求密文")
    request_headers_text: Mapped[str | None] = mapped_column(Text, default=None, comment="请求头摘要")
    response_plain_text: Mapped[str | None] = mapped_column(LONGTEXT, default=None, comment="响应解密后明文")
    response_cipher_text: Mapped[str | None] = mapped_column(Text, default=None, comment="响应密文")
    response_raw_text: Mapped[str | None] = mapped_column(LONGTEXT, default=None, comment="原始响应文本")
    response_raw_preview: Mapped[str | None] = mapped_column(Text, default=None, comment="原始响应预览")
    response_plain_preview: Mapped[str | None] = mapped_column(Text, default=None, comment="解密响应预览")
    response_raw_size: Mapped[int | None] = mapped_column(BIGINT, default=None, comment="原始响应字节数")
    response_plain_size: Mapped[int | None] = mapped_column(BIGINT, default=None, comment="解密响应字节数")
    payload_store_mode: Mapped[str | None] = mapped_column(String(32), default="DB", comment="payload 存储模式：DB/FILE")
    payload_store_path: Mapped[str | None] = mapped_column(String(500), default=None, comment="payload 文件存储路径/目录")
    response_code: Mapped[str | None] = mapped_column(String(64), default=None, comment="外部接口响应码")
    response_message: Mapped[str | None] = mapped_column(String(500), default=None, comment="外部接口响应消息")
    http_status_code: Mapped[int | None] = mapped_column(default=None, comment="HTTP状态码")
    success_flag: Mapped[int] = mapped_column(default=0, nullable=False, comment="是否成功")
    duration_ms: Mapped[int | None] = mapped_column(default=None, comment="耗时毫秒")
    error_code: Mapped[str | None] = mapped_column(String(64), default=None, comment="系统错误码")
    error_message: Mapped[str | None] = mapped_column(String(1000), default=None, comment="错误信息")
    analysis_status: Mapped[int] = mapped_column(default=0, nullable=False, comment="分析状态")
    export_status: Mapped[int] = mapped_column(default=0, nullable=False, comment="导出状态")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="结束时间")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, comment="创建时间")
