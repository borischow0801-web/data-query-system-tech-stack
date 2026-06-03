"""query record payload store fields

Revision ID: 20260318000100
Revises: 20250316000000
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260318000100"
down_revision = "20250316000000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 扩大大字段为 LONGTEXT（避免中等响应写入失败）
    op.alter_column("dq_query_record", "request_plain_text", type_=mysql.LONGTEXT(), existing_type=sa.Text(), nullable=True)
    op.alter_column("dq_query_record", "request_cipher_text", type_=mysql.LONGTEXT(), existing_type=sa.Text(), nullable=True)
    op.alter_column("dq_query_record", "response_raw_text", type_=mysql.LONGTEXT(), existing_type=sa.Text(), nullable=True)
    op.alter_column("dq_query_record", "response_plain_text", type_=mysql.LONGTEXT(), existing_type=sa.Text(), nullable=True)

    # 新增 preview/size/store 字段
    op.add_column("dq_query_record", sa.Column("response_raw_preview", sa.Text(), nullable=True, comment="原始响应预览"))
    op.add_column("dq_query_record", sa.Column("response_plain_preview", sa.Text(), nullable=True, comment="解密响应预览"))
    op.add_column("dq_query_record", sa.Column("response_raw_size", sa.BigInteger(), nullable=True, comment="原始响应字节数"))
    op.add_column("dq_query_record", sa.Column("response_plain_size", sa.BigInteger(), nullable=True, comment="解密响应字节数"))
    op.add_column("dq_query_record", sa.Column("payload_store_mode", sa.String(length=32), nullable=True, server_default="DB", comment="payload 存储模式：DB/FILE"))
    op.add_column("dq_query_record", sa.Column("payload_store_path", sa.String(length=500), nullable=True, comment="payload 文件存储路径/目录"))


def downgrade() -> None:
    op.drop_column("dq_query_record", "payload_store_path")
    op.drop_column("dq_query_record", "payload_store_mode")
    op.drop_column("dq_query_record", "response_plain_size")
    op.drop_column("dq_query_record", "response_raw_size")
    op.drop_column("dq_query_record", "response_plain_preview")
    op.drop_column("dq_query_record", "response_raw_preview")

    op.alter_column("dq_query_record", "response_plain_text", type_=sa.Text(), existing_type=mysql.LONGTEXT(), nullable=True)
    op.alter_column("dq_query_record", "response_raw_text", type_=sa.Text(), existing_type=mysql.LONGTEXT(), nullable=True)
    op.alter_column("dq_query_record", "request_cipher_text", type_=sa.Text(), existing_type=mysql.LONGTEXT(), nullable=True)
    op.alter_column("dq_query_record", "request_plain_text", type_=sa.Text(), existing_type=mysql.LONGTEXT(), nullable=True)

