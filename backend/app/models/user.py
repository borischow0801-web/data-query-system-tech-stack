"""用户表 dq_user"""
from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.base import AuditMixin, SoftDeleteMixin, TimestampMixin


class DqUser(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "dq_user"
    __table_args__ = {"comment": "用户表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, comment="登录账号")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="密码哈希")
    real_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="真实姓名")
    mobile: Mapped[str | None] = mapped_column(String(32), default=None, comment="手机号")
    email: Mapped[str | None] = mapped_column(String(128), default=None, comment="邮箱")
    status: Mapped[int] = mapped_column(default=1, nullable=False, comment="状态：1启用，0禁用")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, default=None, comment="最后登录时间")
    remark: Mapped[str | None] = mapped_column(String(500), default=None, comment="备注")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
