"""开放API客户端表 dq_open_api_client"""
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.base import AuditMixin, SoftDeleteMixin, TimestampMixin


class DqOpenApiClient(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "dq_open_api_client"
    __table_args__ = {"comment": "开放API客户端表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    client_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="客户端编码")
    client_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="客户端名称")
    app_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="应用Key")
    app_secret_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="应用Secret哈希")
    contact_name: Mapped[str | None] = mapped_column(String(64), default=None, comment="联系人")
    contact_mobile: Mapped[str | None] = mapped_column(String(32), default=None, comment="联系电话")
    ip_whitelist: Mapped[str | None] = mapped_column(Text, default=None, comment="IP白名单")
    status: Mapped[int] = mapped_column(default=1, nullable=False, comment="状态")
    remark: Mapped[str | None] = mapped_column(String(500), default=None, comment="备注")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
