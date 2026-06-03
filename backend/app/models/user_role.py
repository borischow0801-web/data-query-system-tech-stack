"""用户角色关联表 dq_user_role"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DqUserRole(Base):
    __tablename__ = "dq_user_role"
    __table_args__ = {"comment": "用户角色关联表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="用户ID")
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="角色ID")
    created_by: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="创建人")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False, comment="创建时间")
