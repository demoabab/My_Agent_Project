"""种子数据：创建默认管理员用户、默认租户和基础角色权限。

幂等执行——重复调用不会创建重复数据。
"""
import uuid
from typing import Optional

from chatchat.server.auth.auth import get_password_hash
from chatchat.server.db.models.user_model import UserModel
from chatchat.server.db.models.tenant_model import TenantModel
from chatchat.server.db.models.user_tenant import UserTenantModel
from chatchat.server.db.models.role_model import RoleModel, PermissionModel
from chatchat.server.db.session import session_scope
from chatchat.utils import build_logger

logger = build_logger()

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_TENANT = "default"

DEFAULT_PERMISSIONS = [
    ("knowledge_base", "read"),
    ("knowledge_base", "write"),
    ("knowledge_base", "delete"),
    ("chat", "read"),
    ("chat", "write"),
    ("tenant", "read"),
    ("tenant", "write"),
    ("mcp", "read"),
    ("mcp", "write"),
    ("mcp", "delete"),
]


def _ensure_user(session, username: str, password: str, is_superuser: bool = False) -> str:
    user = session.query(UserModel).filter(UserModel.username == username).first()
    if user:
        return user.id
    user = UserModel(
        id=uuid.uuid4().hex,
        username=username,
        hashed_password=get_password_hash(password),
        is_superuser=is_superuser,
        is_active=True,
    )
    session.add(user)
    session.flush()
    logger.success(f"Created user: {username}")
    return user.id


def _ensure_tenant(session, name: str) -> str:
    tenant = session.query(TenantModel).filter(TenantModel.name == name).first()
    if tenant:
        return tenant.id
    tenant = TenantModel(
        id=uuid.uuid4().hex,
        name=name,
        status="active",
    )
    session.add(tenant)
    session.flush()
    logger.success(f"Created tenant: {name}")
    return tenant.id


def _ensure_user_tenant(session, user_id: str, tenant_id: str, role: str = "admin"):
    existing = (
        session.query(UserTenantModel)
        .filter_by(user_id=user_id, tenant_id=tenant_id)
        .first()
    )
    if existing:
        return
    ut = UserTenantModel(user_id=user_id, tenant_id=tenant_id, role=role)
    session.add(ut)
    logger.success(f"Linked user to tenant as {role}")


def _ensure_role_and_permissions(session, tenant_id: str):
    # 为每个角色创建默认权限
    roles_with_perms = {
        "admin": DEFAULT_PERMISSIONS,  # admin 拥有所有权限
        "member": [
            ("knowledge_base", "read"),
            ("knowledge_base", "write"),
            ("chat", "read"),
            ("chat", "write"),
        ],
        "viewer": [
            ("knowledge_base", "read"),
            ("chat", "read"),
        ],
    }

    for role_name, perms in roles_with_perms.items():
        role = (
            session.query(RoleModel)
            .filter(RoleModel.name == role_name, RoleModel.tenant_id == tenant_id)
            .first()
        )
        if not role:
            role = RoleModel(
                id=uuid.uuid4().hex,
                name=role_name,
                tenant_id=tenant_id,
            )
            session.add(role)
            session.flush()
            logger.success(f"Created role: {role_name}")

        for resource, action in perms:
            existing_perm = (
                session.query(PermissionModel)
                .filter(
                    PermissionModel.role_id == role.id,
                    PermissionModel.resource == resource,
                    PermissionModel.action == action,
                )
                .first()
            )
            if not existing_perm:
                perm = PermissionModel(
                    id=uuid.uuid4().hex,
                    name=f"{role_name}_{resource}_{action}",
                    resource=resource,
                    action=action,
                    role_id=role.id,
                )
                session.add(perm)
    session.commit()


def seed_all():
    """幂等执行所有种子数据初始化。"""
    with session_scope() as session:
        user_id = _ensure_user(session, DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASSWORD, is_superuser=True)
        tenant_id = _ensure_tenant(session, DEFAULT_TENANT)
        _ensure_user_tenant(session, user_id, tenant_id, role="admin")
        _ensure_role_and_permissions(session, tenant_id)
        logger.success("Seed data initialization completed")
