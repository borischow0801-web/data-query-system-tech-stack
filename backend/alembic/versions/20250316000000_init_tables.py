"""init_tables: dq_user, dq_role, dq_user_role, dq_interface_config, dq_interface_param_template, dq_query_record, dq_export_task, dq_open_api_client, dq_open_api_call_log, dq_audit_log

Revision ID: 20250316000000
Revises:
Create Date: 2025-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20250316000000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dq_user",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("username", sa.String(64), nullable=False, comment="登录账号"),
        sa.Column("password_hash", sa.String(255), nullable=False, comment="密码哈希"),
        sa.Column("real_name", sa.String(64), nullable=False, comment="真实姓名"),
        sa.Column("mobile", sa.String(32), nullable=True, comment="手机号"),
        sa.Column("email", sa.String(128), nullable=True, comment="邮箱"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1", comment="状态：1启用，0禁用"),
        sa.Column("last_login_at", sa.DateTime(), nullable=True, comment="最后登录时间"),
        sa.Column("remark", sa.String(500), nullable=True, comment="备注"),
        sa.Column("ext_json", sa.JSON(), nullable=True, comment="扩展字段"),
        sa.Column("deleted_flag", sa.SmallInteger(), nullable=False, server_default="0", comment="删除标记"),
        sa.Column("created_by", sa.BigInteger(), nullable=True, comment="创建人"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_by", sa.BigInteger(), nullable=True, comment="更新人"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="更新时间"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uk_dq_user_username"),
        comment="用户表",
    )
    op.create_index("idx_dq_user_status", "dq_user", ["status"], unique=False)
    op.create_index("idx_dq_user_deleted_flag", "dq_user", ["deleted_flag"], unique=False)

    op.create_table(
        "dq_role",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键"),
        sa.Column("role_code", sa.String(64), nullable=False, comment="角色编码"),
        sa.Column("role_name", sa.String(64), nullable=False, comment="角色名称"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1", comment="状态"),
        sa.Column("remark", sa.String(500), nullable=True, comment="备注"),
        sa.Column("ext_json", sa.JSON(), nullable=True, comment="扩展字段"),
        sa.Column("deleted_flag", sa.SmallInteger(), nullable=False, server_default="0", comment="删除标记"),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("role_code", name="uk_dq_role_code"),
        comment="角色表",
    )
    op.create_index("idx_dq_role_status", "dq_role", ["status"], unique=False)
    op.create_index("idx_dq_role_deleted_flag", "dq_role", ["deleted_flag"], unique=False)

    op.create_table(
        "dq_user_role",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False, comment="用户ID"),
        sa.Column("role_id", sa.BigInteger(), nullable=False, comment="角色ID"),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uk_dq_user_role"),
        comment="用户角色关联表",
    )
    op.create_index("idx_dq_user_role_user_id", "dq_user_role", ["user_id"], unique=False)
    op.create_index("idx_dq_user_role_role_id", "dq_user_role", ["role_id"], unique=False)

    op.create_table(
        "dq_interface_config",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("interface_code", sa.String(64), nullable=False),
        sa.Column("interface_name", sa.String(128), nullable=False),
        sa.Column("interface_category", sa.String(64), nullable=True),
        sa.Column("env_code", sa.String(32), nullable=False, server_default="prod"),
        sa.Column("base_url", sa.String(500), nullable=False),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("request_method", sa.String(16), nullable=False, server_default="POST"),
        sa.Column("content_type", sa.String(64), nullable=False, server_default="application/json"),
        sa.Column("timeout_ms", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("token_value", sa.String(512), nullable=True),
        sa.Column("token_header_name", sa.String(64), nullable=True, server_default="token"),
        sa.Column("auth_type", sa.String(32), nullable=False, server_default="TOKEN"),
        sa.Column("sm2_public_key", sa.Text(), nullable=True),
        sa.Column("encrypt_mode", sa.String(32), nullable=False, server_default="SM2_SM4"),
        sa.Column("sm2_cipher_mode", sa.String(32), nullable=True),
        sa.Column("sm4_mode", sa.String(32), nullable=True),
        sa.Column("sm4_padding", sa.String(32), nullable=True),
        sa.Column("cipher_encoding", sa.String(32), nullable=True),
        sa.Column("encrypt_key_header_name", sa.String(64), nullable=True, server_default="encryptKey"),
        sa.Column("request_data_field_name", sa.String(64), nullable=True, server_default="data"),
        sa.Column("response_data_field_name", sa.String(64), nullable=True, server_default="data"),
        sa.Column("response_code_field_name", sa.String(64), nullable=True, server_default="code"),
        sa.Column("response_msg_field_name", sa.String(64), nullable=True, server_default="message"),
        sa.Column("success_code_value", sa.String(64), nullable=True, server_default="0"),
        sa.Column("request_header_template", sa.Text(), nullable=True),
        sa.Column("request_body_template", sa.Text(), nullable=True),
        sa.Column("response_mapping_template", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("retry_interval_ms", sa.Integer(), nullable=False, server_default="1000"),
        sa.Column("cache_ttl_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rate_limit_qps", sa.Integer(), nullable=True),
        sa.Column("allow_open_api", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("sort_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(500), nullable=True),
        sa.Column("ext_json", sa.JSON(), nullable=True),
        sa.Column("deleted_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interface_code", "env_code", name="uk_dq_interface_code_env"),
        comment="接口配置表",
    )
    op.create_index("idx_dq_interface_status", "dq_interface_config", ["status"], unique=False)
    op.create_index("idx_dq_interface_category", "dq_interface_config", ["interface_category"], unique=False)
    op.create_index("idx_dq_interface_deleted_flag", "dq_interface_config", ["deleted_flag"], unique=False)

    op.create_table(
        "dq_interface_param_template",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("interface_id", sa.BigInteger(), nullable=False),
        sa.Column("param_code", sa.String(64), nullable=False),
        sa.Column("param_name", sa.String(128), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("data_type", sa.String(32), nullable=False),
        sa.Column("form_component", sa.String(32), nullable=False, server_default="input"),
        sa.Column("required_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("default_value", sa.String(500), nullable=True),
        sa.Column("example_value", sa.String(500), nullable=True),
        sa.Column("placeholder_text", sa.String(255), nullable=True),
        sa.Column("validation_rule", sa.String(500), nullable=True),
        sa.Column("request_path_expr", sa.String(255), nullable=True),
        sa.Column("sort_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("visible_flag", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("queryable_flag", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("analyzable_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("exportable_flag", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("remark", sa.String(500), nullable=True),
        sa.Column("ext_json", sa.JSON(), nullable=True),
        sa.Column("deleted_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("interface_id", "param_code", name="uk_dq_param_interface_code"),
        comment="接口参数模板表",
    )
    op.create_index("idx_dq_param_interface_id", "dq_interface_param_template", ["interface_id"], unique=False)
    op.create_index("idx_dq_param_sort_no", "dq_interface_param_template", ["sort_no"], unique=False)
    op.create_index("idx_dq_param_deleted_flag", "dq_interface_param_template", ["deleted_flag"], unique=False)

    op.create_table(
        "dq_query_record",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("interface_id", sa.BigInteger(), nullable=False),
        sa.Column("interface_code", sa.String(64), nullable=False),
        sa.Column("trigger_type", sa.String(32), nullable=False, server_default="WEB"),
        sa.Column("trigger_client_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_user_id", sa.BigInteger(), nullable=True),
        sa.Column("request_plain_text", sa.Text(), nullable=True),
        sa.Column("request_cipher_text", sa.Text(), nullable=True),
        sa.Column("request_headers_text", sa.Text(), nullable=True),
        sa.Column("response_plain_text", sa.Text(), nullable=True),
        sa.Column("response_cipher_text", sa.Text(), nullable=True),
        sa.Column("response_raw_text", sa.Text(), nullable=True),
        sa.Column("response_code", sa.String(64), nullable=True),
        sa.Column("response_message", sa.String(500), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("success_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("analysis_status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("export_status", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("ext_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        comment="查询执行记录表",
    )
    op.create_index("idx_dq_query_trace_id", "dq_query_record", ["trace_id"], unique=False)
    op.create_index("idx_dq_query_interface_id", "dq_query_record", ["interface_id"], unique=False)
    op.create_index("idx_dq_query_interface_code", "dq_query_record", ["interface_code"], unique=False)
    op.create_index("idx_dq_query_trigger_type", "dq_query_record", ["trigger_type"], unique=False)
    op.create_index("idx_dq_query_operator_user_id", "dq_query_record", ["operator_user_id"], unique=False)
    op.create_index("idx_dq_query_success_flag", "dq_query_record", ["success_flag"], unique=False)
    op.create_index("idx_dq_query_created_at", "dq_query_record", ["created_at"], unique=False)

    op.create_table(
        "dq_export_task",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("task_no", sa.String(64), nullable=False),
        sa.Column("interface_id", sa.BigInteger(), nullable=True),
        sa.Column("query_record_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_user_id", sa.BigInteger(), nullable=True),
        sa.Column("export_type", sa.String(32), nullable=False),
        sa.Column("export_scope", sa.String(32), nullable=False, server_default="RESULT"),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("task_status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("failure_reason", sa.String(1000), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("ext_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_no", name="uk_dq_export_task_no"),
        comment="导出任务表",
    )
    op.create_index("idx_dq_export_query_record_id", "dq_export_task", ["query_record_id"], unique=False)
    op.create_index("idx_dq_export_operator_user_id", "dq_export_task", ["operator_user_id"], unique=False)
    op.create_index("idx_dq_export_task_status", "dq_export_task", ["task_status"], unique=False)
    op.create_index("idx_dq_export_created_at", "dq_export_task", ["created_at"], unique=False)

    op.create_table(
        "dq_open_api_client",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("client_code", sa.String(64), nullable=False),
        sa.Column("client_name", sa.String(128), nullable=False),
        sa.Column("app_key", sa.String(128), nullable=False),
        sa.Column("app_secret_hash", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(64), nullable=True),
        sa.Column("contact_mobile", sa.String(32), nullable=True),
        sa.Column("ip_whitelist", sa.Text(), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("remark", sa.String(500), nullable=True),
        sa.Column("ext_json", sa.JSON(), nullable=True),
        sa.Column("deleted_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("client_code", name="uk_dq_open_api_client_code"),
        sa.UniqueConstraint("app_key", name="uk_dq_open_api_app_key"),
        comment="开放API客户端表",
    )
    op.create_index("idx_dq_open_api_status", "dq_open_api_client", ["status"], unique=False)
    op.create_index("idx_dq_open_api_deleted_flag", "dq_open_api_client", ["deleted_flag"], unique=False)

    op.create_table(
        "dq_open_api_call_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("trace_id", sa.String(64), nullable=False),
        sa.Column("client_id", sa.BigInteger(), nullable=False),
        sa.Column("client_code", sa.String(64), nullable=False),
        sa.Column("interface_code", sa.String(64), nullable=False),
        sa.Column("request_uri", sa.String(255), nullable=True),
        sa.Column("request_method", sa.String(16), nullable=True),
        sa.Column("request_ip", sa.String(64), nullable=True),
        sa.Column("request_params_text", sa.Text(), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("success_flag", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("query_record_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        comment="开放API调用日志表",
    )
    op.create_index("idx_dq_open_call_trace_id", "dq_open_api_call_log", ["trace_id"], unique=False)
    op.create_index("idx_dq_open_call_client_id", "dq_open_api_call_log", ["client_id"], unique=False)
    op.create_index("idx_dq_open_call_interface_code", "dq_open_api_call_log", ["interface_code"], unique=False)
    op.create_index("idx_dq_open_call_success_flag", "dq_open_api_call_log", ["success_flag"], unique=False)
    op.create_index("idx_dq_open_call_created_at", "dq_open_api_call_log", ["created_at"], unique=False)

    op.create_table(
        "dq_audit_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("operator_user_id", sa.BigInteger(), nullable=True),
        sa.Column("operator_name", sa.String(64), nullable=True),
        sa.Column("module_name", sa.String(64), nullable=False),
        sa.Column("operation_type", sa.String(32), nullable=False),
        sa.Column("target_type", sa.String(64), nullable=False),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("target_code", sa.String(128), nullable=True),
        sa.Column("operation_content", sa.Text(), nullable=True),
        sa.Column("request_ip", sa.String(64), nullable=True),
        sa.Column("success_flag", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("error_message", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        comment="审计日志表",
    )
    op.create_index("idx_dq_audit_operator_user_id", "dq_audit_log", ["operator_user_id"], unique=False)
    op.create_index("idx_dq_audit_module_name", "dq_audit_log", ["module_name"], unique=False)
    op.create_index("idx_dq_audit_operation_type", "dq_audit_log", ["operation_type"], unique=False)
    op.create_index("idx_dq_audit_target_type", "dq_audit_log", ["target_type"], unique=False)
    op.create_index("idx_dq_audit_created_at", "dq_audit_log", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_table("dq_audit_log")
    op.drop_table("dq_open_api_call_log")
    op.drop_table("dq_open_api_client")
    op.drop_table("dq_export_task")
    op.drop_table("dq_query_record")
    op.drop_table("dq_interface_param_template")
    op.drop_table("dq_interface_config")
    op.drop_table("dq_user_role")
    op.drop_table("dq_role")
    op.drop_table("dq_user")
