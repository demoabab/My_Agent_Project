from sqlalchemy import Column, ForeignKey, String

from chatchat.server.db.base import Base


class RoleModel(Base):
    __tablename__ = "role"

    id = Column(String(32), primary_key=True, comment="角色ID")
    name = Column(String(50), nullable=False, comment="角色名称")
    tenant_id = Column(String(32), ForeignKey("tenant.id"), comment="所属租户ID")

    def __repr__(self):
        return f"<Role(id='{self.id}', name='{self.name}', tenant_id='{self.tenant_id}')>"


class PermissionModel(Base):
    __tablename__ = "permission"

    id = Column(String(32), primary_key=True, comment="权限ID")
    name = Column(String(100), nullable=False, comment="权限名称")
    resource = Column(String(100), comment="资源: knowledge_base, chat, tenant 等")
    action = Column(String(50), comment="操作: read, write, delete, admin")
    role_id = Column(String(32), ForeignKey("role.id"), comment="所属角色ID")

    def __repr__(self):
        return f"<Permission(id='{self.id}', name='{self.name}', resource='{self.resource}', action='{self.action}')>"
