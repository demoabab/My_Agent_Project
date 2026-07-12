"""memory_tables

Revision ID: c3d4e5f678a9
Revises: b2c3d4e5f678
Create Date: 2026-07-12

新增长期记忆相关表:
- user_profile: 用户画像（偏好、关键事实）
- conversation_memory: 跨会话记忆条目
- conversation_summary: 会话摘要
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f678a9"
down_revision: Union[str, None] = "b2c3d4e5f678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_profile",
        sa.Column("user_id", sa.String(32), primary_key=True, comment="用户ID"),
        sa.Column("preferred_model", sa.String(50), comment="偏好的LLM模型"),
        sa.Column("language", sa.String(10), server_default="zh", comment="语言偏好: zh/en"),
        sa.Column("response_style", sa.String(20), server_default="balanced", comment="回答风格: concise/detailed/balanced"),
        sa.Column("expertise_domain", sa.String(100), comment="专业领域"),
        sa.Column("key_facts", sa.JSON(), comment="关键事实列表"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
        sa.Column("update_time", sa.DateTime(), server_default=sa.func.now(), comment="更新时间"),
    )

    op.create_table(
        "conversation_memory",
        sa.Column("id", sa.String(32), primary_key=True, comment="记忆ID"),
        sa.Column("user_id", sa.String(32), nullable=False, index=True, comment="用户ID"),
        sa.Column("memory_type", sa.String(20), server_default="fact", comment="类型: preference/fact/decision/event"),
        sa.Column("content", sa.Text(), nullable=False, comment="记忆内容"),
        sa.Column("importance", sa.Float(), server_default="0.5", comment="重要性权重 0-1"),
        sa.Column("source_conversation_id", sa.String(32), comment="来源会话ID"),
        sa.Column("access_count", sa.Integer(), server_default="0", comment="被引用次数"),
        sa.Column("tenant_id", sa.String(32), index=True, comment="租户ID"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
    )

    op.create_table(
        "conversation_summary",
        sa.Column("conversation_id", sa.String(32), primary_key=True, comment="会话ID"),
        sa.Column("summary", sa.Text(), comment="会话摘要"),
        sa.Column("key_points", sa.JSON(), comment="关键要点列表"),
        sa.Column("original_token_count", sa.Integer(), server_default="0", comment="原始对话token估算"),
        sa.Column("summary_token_count", sa.Integer(), server_default="0", comment="摘要token估算"),
        sa.Column("tenant_id", sa.String(32), index=True, comment="租户ID"),
        sa.Column("create_time", sa.DateTime(), server_default=sa.func.now(), comment="创建时间"),
    )


def downgrade() -> None:
    op.drop_table("conversation_summary")
    op.drop_table("conversation_memory")
    op.drop_table("user_profile")
