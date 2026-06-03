"""接口参数模板表 dq_interface_param_template"""
from sqlalchemy import BigInteger, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.base import AuditMixin, SoftDeleteMixin, TimestampMixin


class DqInterfaceParamTemplate(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "dq_interface_param_template"
    __table_args__ = {"comment": "接口参数模板表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    interface_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="接口配置ID")
    param_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="参数编码")
    param_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="参数名称")
    display_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="显示名称")
    data_type: Mapped[str] = mapped_column(String(32), nullable=False, comment="数据类型")
    form_component: Mapped[str] = mapped_column(String(32), default="input", nullable=False, comment="表单组件类型")
    required_flag: Mapped[int] = mapped_column(default=0, nullable=False, comment="是否必填")
    default_value: Mapped[str | None] = mapped_column(String(500), default=None, comment="默认值")
    example_value: Mapped[str | None] = mapped_column(String(500), default=None, comment="示例值")
    placeholder_text: Mapped[str | None] = mapped_column(String(255), default=None, comment="占位提示")
    validation_rule: Mapped[str | None] = mapped_column(String(500), default=None, comment="校验规则描述")
    request_path_expr: Mapped[str | None] = mapped_column(String(255), default=None, comment="写入请求报文的路径表达式")
    sort_no: Mapped[int] = mapped_column(default=0, nullable=False, comment="排序号")
    visible_flag: Mapped[int] = mapped_column(default=1, nullable=False, comment="是否可见")
    queryable_flag: Mapped[int] = mapped_column(default=1, nullable=False, comment="是否参与查询")
    analyzable_flag: Mapped[int] = mapped_column(default=0, nullable=False, comment="是否参与分析条件")
    exportable_flag: Mapped[int] = mapped_column(default=1, nullable=False, comment="是否允许导出")
    remark: Mapped[str | None] = mapped_column(String(500), default=None, comment="备注")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
