"""SQLAlchemy 2.x 声明式 Base 与通用字段。"""
from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Integer, SmallInteger, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """声明式基类"""

    type_annotation_map = {
        int: BigInteger,
    }


class TimestampMixin:
    """创建/更新时间混入"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class AuditMixin:
    """审计字段混入"""

    created_by: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="创建人")
    updated_by: Mapped[int | None] = mapped_column(BigInteger, default=None, comment="更新人")


class SoftDeleteMixin:
    """逻辑删除混入"""

    deleted_flag: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        nullable=False,
        comment="删除标记：0否，1是",
    )
