from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, func
from chatchat.server.db.base import Base


class ConversationSummaryModel(Base):
    __tablename__ = "conversation_summary"

    conversation_id = Column(String(32), primary_key=True, comment="会话ID")
    summary = Column(Text, comment="会话摘要")
    key_points = Column(JSON, default=[], comment="关键要点列表")
    original_token_count = Column(Integer, default=0, comment="原始对话token估算")
    summary_token_count = Column(Integer, default=0, comment="摘要token估算")
    tenant_id = Column(String(32), index=True, comment="租户ID")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
