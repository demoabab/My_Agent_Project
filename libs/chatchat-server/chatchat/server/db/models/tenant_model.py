from sqlalchemy import JSON, Column, DateTime, String, func

from chatchat.server.db.base import Base


class TenantModel(Base):
    __tablename__ = "tenant"

    id = Column(String(32), primary_key=True, comment="租户ID")
    name = Column(String(100), unique=True, nullable=False, comment="租户名称")
    status = Column(String(20), default="active", comment="状态: active/suspended")
    config = Column(JSON, default={}, comment="租户配置")
    create_time = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<Tenant(id='{self.id}', name='{self.name}', status='{self.status}')>"
