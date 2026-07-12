from sqlalchemy import JSON, Column, DateTime, String, func
from chatchat.server.db.base import Base


class UserProfileModel(Base):
    __tablename__ = "user_profile"

    user_id = Column(String(32), primary_key=True, comment="用户ID")
    preferred_model = Column(String(50), comment="偏好的LLM模型")
    language = Column(String(10), default="zh", comment="语言偏好: zh/en")
    response_style = Column(String(20), default="balanced", comment="回答风格: concise/detailed/balanced")
    expertise_domain = Column(String(100), comment="专业领域")
    key_facts = Column(JSON, default=[], comment="关键事实列表")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
