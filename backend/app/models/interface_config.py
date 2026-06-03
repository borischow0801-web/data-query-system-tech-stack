"""接口配置表 dq_interface_config"""
from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.base import AuditMixin, SoftDeleteMixin, TimestampMixin


class DqInterfaceConfig(Base, TimestampMixin, AuditMixin, SoftDeleteMixin):
    __tablename__ = "dq_interface_config"
    __table_args__ = {"comment": "接口配置表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    interface_code: Mapped[str] = mapped_column(String(64), nullable=False, comment="接口编码")
    interface_name: Mapped[str] = mapped_column(String(128), nullable=False, comment="接口名称")
    interface_category: Mapped[str | None] = mapped_column(String(64), default=None, comment="接口分类")
    env_code: Mapped[str] = mapped_column(String(32), default="prod", nullable=False, comment="环境编码")
    base_url: Mapped[str] = mapped_column(String(500), nullable=False, comment="基础地址")
    request_path: Mapped[str | None] = mapped_column(String(500), default=None, comment="请求路径")
    request_method: Mapped[str] = mapped_column(String(16), default="POST", nullable=False, comment="请求方式")
    content_type: Mapped[str] = mapped_column(String(64), default="application/json", nullable=False, comment="内容类型")
    timeout_ms: Mapped[int] = mapped_column(default=10000, nullable=False, comment="超时时间毫秒")

    token_value: Mapped[str | None] = mapped_column(String(512), default=None, comment="Token值")
    token_header_name: Mapped[str | None] = mapped_column(String(64), default="token", comment="Token头名称")
    auth_type: Mapped[str] = mapped_column(String(32), default="TOKEN", nullable=False, comment="鉴权方式")
    sm2_public_key: Mapped[str | None] = mapped_column(Text, default=None, comment="SM2公钥")
    encrypt_mode: Mapped[str] = mapped_column(String(32), default="SM2_SM4", nullable=False, comment="加密模式")
    sm2_cipher_mode: Mapped[str | None] = mapped_column(String(32), default=None, comment="SM2密文模式")
    sm4_mode: Mapped[str | None] = mapped_column(String(32), default=None, comment="SM4模式")
    sm4_padding: Mapped[str | None] = mapped_column(String(32), default=None, comment="SM4填充方式")
    cipher_encoding: Mapped[str | None] = mapped_column(String(32), default=None, comment="密文编码")
    encrypt_key_header_name: Mapped[str | None] = mapped_column(String(64), default="secret", comment="加密密钥header字段名")
    request_data_field_name: Mapped[str | None] = mapped_column(String(64), default="data", comment="请求密文字段名")
    response_data_field_name: Mapped[str | None] = mapped_column(String(64), default="data", comment="响应密文字段名")
    response_code_field_name: Mapped[str | None] = mapped_column(String(64), default="code", comment="响应状态码字段名")
    response_msg_field_name: Mapped[str | None] = mapped_column(String(64), default="msg", comment="响应消息字段名")
    success_code_value: Mapped[str | None] = mapped_column(String(64), default="200", comment="成功状态码值")
    request_header_template: Mapped[str | None] = mapped_column(Text, default=None, comment="请求头模板JSON")
    request_body_template: Mapped[str | None] = mapped_column(Text, default=None, comment="请求体模板JSON")
    response_mapping_template: Mapped[str | None] = mapped_column(Text, default=None, comment="响应映射模板JSON")

    retry_count: Mapped[int] = mapped_column(default=0, nullable=False, comment="失败重试次数")
    retry_interval_ms: Mapped[int] = mapped_column(default=1000, nullable=False, comment="重试间隔毫秒")
    cache_ttl_seconds: Mapped[int] = mapped_column(default=0, nullable=False, comment="缓存秒数")
    rate_limit_qps: Mapped[int | None] = mapped_column(default=None, comment="接口级限流QPS")
    allow_open_api: Mapped[int] = mapped_column(default=1, nullable=False, comment="是否允许开放API")
    status: Mapped[int] = mapped_column(default=1, nullable=False, comment="状态：1启用，0停用")
    sort_no: Mapped[int] = mapped_column(default=0, nullable=False, comment="排序号")
    remark: Mapped[str | None] = mapped_column(String(500), default=None, comment="备注")
    ext_json: Mapped[dict | None] = mapped_column(JSON, default=None, comment="扩展字段")
