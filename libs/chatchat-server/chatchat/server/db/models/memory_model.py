from sqlalchemy import Column, DateTime, Float, Integer, String, Text, func
from chatchat.server.db.base import Base


class MemoryModel(Base):
    __tablename__ = "conversation_memory"

    id = Column(String(32), primary_key=True, comment="记忆ID")
    user_id = Column(String(32), index=True, nullable=False, comment="用户ID")
    memory_type = Column(String(20), default="fact", comment="类型: preference/fact/decision/event")
    content = Column(Text, nullable=False, comment="记忆内容")
    importance = Column(Float, default=0.5, comment="重要性权重 0-1")
    source_conversation_id = Column(String(32), comment="来源会话ID")
    access_count = Column(Integer, default=0, comment="被引用次数")
    tenant_id = Column(String(32), index=True, comment="租户ID")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
