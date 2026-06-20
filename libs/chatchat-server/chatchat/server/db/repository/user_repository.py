import uuid
from typing import List, Optional

from chatchat.server.db.models.user_model import UserModel
from chatchat.server.db.models.user_tenant import UserTenantModel
from chatchat.server.db.models.tenant_model import TenantModel
from chatchat.server.db.models.role_model import PermissionModel, RoleModel
from chatchat.server.db.session import with_session


@with_session
def create_user(session, username: str, hashed_password: str, email: str = "", full_name: str = "", is_superuser: bool = False) -> str:
    user = UserModel(
        id=uuid.uuid4().hex,
        username=username,
        hashed_password=hashed_password,
        email=email,
        full_name=full_name,
        is_superuser=is_superuser,
    )
    session.add(user)
    session.commit()
    return user.id


@with_session
def get_user_by_username(session, username: str) -> Optional[dict]:
    user = session.query(UserModel).filter(UserModel.username == username).first()
    if user:
        return {
            "id": user.id,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
    return None


@with_session
def get_user_by_id(session, user_id: str) -> Optional[dict]:
    user = session.query(UserModel).filter(UserModel.id == user_id).first()
    if user:
        return {
            "id": user.id,
            "username": user.username,
            "hashed_password": user.hashed_password,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
        }
    return None


@with_session
def get_user_tenants(session, user_id: str) -> List[dict]:
    results = (
        session.query(UserTenantModel, TenantModel)
        .join(TenantModel, UserTenantModel.tenant_id == TenantModel.id)
        .filter(UserTenantModel.user_id == user_id)
        .all()
    )
    return [
        {
            "tenant_id": ut.tenant_id,
            "tenant_name": t.name,
            "role": ut.role,
        }
        for ut, t in results
    ]


@with_session
def add_user_to_tenant(session, user_id: str, tenant_id: str, role: str = "member") -> bool:
    existing = (
        session.query(UserTenantModel)
        .filter_by(user_id=user_id, tenant_id=tenant_id)
        .first()
    )
    if not existing:
        ut = UserTenantModel(user_id=user_id, tenant_id=tenant_id, role=role)
        session.add(ut)
        session.commit()
    return True


@with_session
def list_all_users(session, limit: int = 100, offset: int = 0) -> list[dict]:
    users = session.query(UserModel).order_by(UserModel.create_time.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": u.full_name,
            "is_active": u.is_active,
            "is_superuser": u.is_superuser,
            "create_time": u.create_time.isoformat() if u.create_time else None,
        }
        for u in users
    ]


@with_session
def count_all_users(session) -> int:
    return session.query(UserModel).count()


@with_session
def check_user_permission(session, user_id: str, tenant_id: str, resource: str, action: str) -> bool:
    ut = (
        session.query(UserTenantModel)
        .filter_by(user_id=user_id, tenant_id=tenant_id)
        .first()
    )
    if not ut:
        return False
    if ut.role == "admin":
        return True
    perm = (
        session.query(PermissionModel)
        .join(RoleModel, PermissionModel.role_id == RoleModel.id)
        .filter(
            RoleModel.name == ut.role,
            RoleModel.tenant_id == tenant_id,
            PermissionModel.resource == resource,
            PermissionModel.action == action,
        )
        .first()
    )
    return perm is not None
