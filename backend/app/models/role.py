"""角色表 dq_role"""
from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.base import AuditMixin, SoftDeleteMixin, TimestampMixin


class DqRole(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "dq_role"
    __table_args__ = {"comment": "角色表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    role_code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="角色编码")
    role_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="角色名称")
    status: Mapped[int] = mapped_column(default=1, nullable=False, comment="状态：1启用，0禁用")
    remark: Mapped[str | None] = mapped_column(String(500), default=None, comment="备注")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
