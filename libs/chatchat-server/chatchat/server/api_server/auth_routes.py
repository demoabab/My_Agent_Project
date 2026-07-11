from fastapi import APIRouter, Depends, Form, HTTPException, status

from chatchat.server.auth.auth import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from chatchat.server.auth.dependencies import get_current_user
from chatchat.server.db.repository.user_repository import (
    add_user_to_tenant,
    create_user,
    get_user_by_username,
    get_user_tenants,
    list_all_users,
    count_all_users,
)
from chatchat.server.db.repository.tenant_repository import create_tenant

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@auth_router.post("/login")
def login(username: str = Form(), password: str = Form()):
    user = get_user_by_username(username)
    if not user or not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    tenants = get_user_tenants(user["id"])
    tenant_id = tenants[0]["tenant_id"] if tenants else None

    token = create_access_token(
        data={"sub": user["id"], "tenant_id": tenant_id}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "username": user["username"],
        "tenants": tenants,
    }


@auth_router.post("/register")
def register(
    username: str = Form(),
    password: str = Form(),
    email: str = Form(""),
    full_name: str = Form(""),
):
    existing = get_user_by_username(username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    user_id = create_user(
        username=username,
        hashed_password=get_password_hash(password),
        email=email,
        full_name=full_name,
    )

    tenant_id = create_tenant(name=f"{username}_default")
    add_user_to_tenant(user_id, tenant_id, role="admin")

    token = create_access_token(
        data={"sub": user_id, "tenant_id": tenant_id}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "username": username,
        "tenant_id": tenant_id,
    }


@auth_router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    tenants = get_user_tenants(current_user["user_id"])
    return {
        **current_user,
        "tenants": tenants,
    }


@auth_router.post("/switch-tenant")
def switch_tenant(
    tenant_id: str = Form(),
    current_user: dict = Depends(get_current_user),
):
    tenants = get_user_tenants(current_user["user_id"])
    if not any(t["tenant_id"] == tenant_id for t in tenants):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this tenant",
        )

    token = create_access_token(
        data={"sub": current_user["user_id"], "tenant_id": tenant_id}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_id": tenant_id,
    }


@auth_router.get("/users")
def list_users(
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
):
    if not current_user["is_superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can list users",
        )
    users = list_all_users(limit=limit, offset=offset)
    total = count_all_users()
    return {"users": users, "total": total}


@auth_router.put("/users/{user_id}/status")
def update_user_status(
    user_id: str,
    is_active: bool = True,
    current_user: dict = Depends(get_current_user),
):
    if not current_user["is_superuser"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superuser can update user status",
        )
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Update user status
    from chatchat.server.db.session import session_scope
    from chatchat.server.db.models.user_model import UserModel

    with session_scope() as session:
        u = session.query(UserModel).filter(UserModel.id == user_id).first()
        if u:
            u.is_active = is_active
            session.commit()
    return {"message": f"User {user_id} status updated to {is_active}"}
