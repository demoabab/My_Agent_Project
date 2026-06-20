"""phase1_multi_tenant

Revision ID: b2c3d4e5f678
Revises: a1da8c7934cd
Create Date: 2026-06-19

新增多租户权限体系:
- 新增 user, tenant, user_tenant, role, permission 表
- 所有现有业务表添加 tenant_id 列
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f678"
down_revision: Union[str, None] = "a1da8c7934cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建 user 表
    op.create_table(
        "user",
        sa.Column("id", sa.String(32), primary_key=True, comment="用户ID"),
        sa.Column("username", sa.String(100), unique=True, nullable=False, comment="用户名"),
        sa.Column("hashed_password", sa.String(255), nullable=False, comment="密码哈希"),
        sa.Column("email", sa.String(255), comment="邮箱"),
        sa.Column("full_name", sa.String(100), comment="姓名"),
        sa.Column("is_active", sa.Boolean(), default=True, comment="是否激活"),
        sa.Column("is_superuser", sa.Boolean(), default=False, comment="是否超级管理员"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
    )

    # 创建 tenant 表
    op.create_table(
        "tenant",
        sa.Column("id", sa.String(32), primary_key=True, comment="租户ID"),
        sa.Column("name", sa.String(100), unique=True, nullable=False, comment="租户名称"),
        sa.Column("status", sa.String(20), default="active", comment="状态"),
        sa.Column("config", sa.JSON(), default={}, comment="租户配置"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
    )

    # 创建 user_tenant 关联表
    op.create_table(
        "user_tenant",
        sa.Column("user_id", sa.String(32), sa.ForeignKey("user.id"), primary_key=True, comment="用户ID"),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenant.id"), primary_key=True, comment="租户ID"),
        sa.Column("role", sa.String(50), default="member", comment="角色"),
    )

    # 创建 role 表
    op.create_table(
        "role",
        sa.Column("id", sa.String(32), primary_key=True, comment="角色ID"),
        sa.Column("name", sa.String(50), nullable=False, comment="角色名称"),
        sa.Column("tenant_id", sa.String(32), sa.ForeignKey("tenant.id"), comment="所属租户ID"),
    )

    # 创建 permission 表
    op.create_table(
        "permission",
        sa.Column("id", sa.String(32), primary_key=True, comment="权限ID"),
        sa.Column("name", sa.String(100), nullable=False, comment="权限名称"),
        sa.Column("resource", sa.String(100), comment="资源"),
        sa.Column("action", sa.String(50), comment="操作"),
        sa.Column("role_id", sa.String(32), sa.ForeignKey("role.id"), comment="所属角色ID"),
    )

    # 现有业务表添加 tenant_id 列
    tables_with_tenant = [
        "knowledge_base",
        "knowledge_file",
        "file_doc",
        "summary_chunk",
        "conversation",
        "message",
        "human_message_event",
        "mcp_connection",
        "mcp_profile",
    ]
    for table in tables_with_tenant:
        op.add_column(table, sa.Column("tenant_id", sa.String(32), nullable=True, comment="租户ID"))
        op.create_index(f"idx_{table}_tenant_id", table, ["tenant_id"])


def downgrade() -> None:
    tables_with_tenant = [
        "knowledge_base",
        "knowledge_file",
        "file_doc",
        "summary_chunk",
        "conversation",
        "message",
        "human_message_event",
        "mcp_connection",
        "mcp_profile",
    ]
    for table in tables_with_tenant:
        op.drop_index(f"idx_{table}_tenant_id", table_name=table)
        op.drop_column(table, "tenant_id")

    op.drop_table("permission")
    op.drop_table("role")
    op.drop_table("user_tenant")
    op.drop_table("tenant")
    op.drop_table("user")
