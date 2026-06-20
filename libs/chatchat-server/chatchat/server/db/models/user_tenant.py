from sqlalchemy import Column, ForeignKey, String

from chatchat.server.db.base import Base


class UserTenantModel(Base):
    __tablename__ = "user_tenant"

    user_id = Column(String(32), ForeignKey("user.id"), primary_key=True, comment="用户ID")
    tenant_id = Column(String(32), ForeignKey("tenant.id"), primary_key=True, comment="租户ID")
    role = Column(String(50), default="member", comment="角色: admin/member/viewer")

    def __repr__(self):
        return f"<UserTenant(user_id='{self.user_id}', tenant_id='{self.tenant_id}', role='{self.role}')>"
