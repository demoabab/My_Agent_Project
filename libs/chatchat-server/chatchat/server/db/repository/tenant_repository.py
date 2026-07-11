import uuid
from typing import List, Optional

from chatchat.server.db.models.tenant_model import TenantModel
from chatchat.server.db.models.user_model import UserModel
from chatchat.server.db.models.user_tenant import UserTenantModel
from chatchat.server.db.session import with_session


@with_session
def create_tenant(session, name: str, config: dict = None, tenant_id: str = None) -> str:
    if tenant_id is None:
        tenant_id = uuid.uuid4().hex
    tenant = TenantModel(
        id=tenant_id,
        name=name,
        config=config or {},
    )
    session.add(tenant)
    session.commit()
    return tenant.id


@with_session
def get_tenant_by_id(session, tenant_id: str) -> Optional[TenantModel]:
    return session.query(TenantModel).filter(TenantModel.id == tenant_id).first()


@with_session
def get_tenant_by_name(session, name: str) -> Optional[TenantModel]:
    return session.query(TenantModel).filter(TenantModel.name == name).first()


@with_session
def list_tenants(session) -> List[TenantModel]:
    return session.query(TenantModel).filter(TenantModel.status == "active").all()


@with_session
def list_tenant_members(session, tenant_id: str) -> List[dict]:
    results = (
        session.query(UserTenantModel, UserModel.username)
        .join(UserModel, UserTenantModel.user_id == UserModel.id)
        .filter(UserTenantModel.tenant_id == tenant_id)
        .all()
    )
    return [{"user_id": ut.user_id, "username": username or "", "role": ut.role} for ut, username in results]


@with_session
def remove_user_from_tenant(session, tenant_id: str, user_id: str) -> bool:
    ut = (
        session.query(UserTenantModel)
        .filter_by(tenant_id=tenant_id, user_id=user_id)
        .first()
    )
    if ut:
        session.delete(ut)
        session.commit()
        return True
    return False
