from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, status

from chatchat.server.auth.dependencies import get_current_user, require_permission
from chatchat.server.db.repository.tenant_repository import (
    create_tenant as repo_create_tenant,
    list_tenant_members,
    remove_user_from_tenant,
)
from chatchat.server.db.repository.user_repository import add_user_to_tenant, get_user_tenants

tenant_router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])


@tenant_router.get("")
def list_tenants(current_user: dict = Depends(get_current_user)):
    return get_user_tenants(current_user["user_id"])


@tenant_router.post("")
def create_tenant(
    name: str = Form(),
    current_user: dict = Depends(require_permission("tenant", "write")),
):
    tenant_id = repo_create_tenant(name=name)
    add_user_to_tenant(current_user["user_id"], tenant_id, role="admin")
    return {"tenant_id": tenant_id, "name": name}


@tenant_router.get("/{tenant_id}/members")
def get_members(
    tenant_id: str,
    current_user: dict = Depends(get_current_user),
):
    return list_tenant_members(tenant_id)


@tenant_router.post("/{tenant_id}/members")
def add_member(
    tenant_id: str,
    user_id: str = Form(),
    role: str = Form("member"),
    current_user: dict = Depends(require_permission("tenant", "write")),
):
    add_user_to_tenant(user_id, tenant_id, role=role)
    return {"message": "Member added"}


@tenant_router.delete("/{tenant_id}/members/{user_id}")
def remove_member(
    tenant_id: str,
    user_id: str,
    current_user: dict = Depends(require_permission("tenant", "write")),
):
    if not remove_user_from_tenant(tenant_id, user_id):
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Member removed"}
