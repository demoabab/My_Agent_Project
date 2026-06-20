from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from chatchat.server.auth.auth import verify_token
from chatchat.server.context import set_current_tenant_context
from chatchat.server.db.repository.user_repository import (
    get_user_by_id,
    get_user_tenants,
)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = get_user_by_id(user_id)
    if user is None or not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    tenant_id = payload.get("tenant_id")
    set_current_tenant_context(tenant_id=tenant_id, user_id=user_id)

    return {
        "user_id": user_id,
        "username": user["username"],
        "tenant_id": tenant_id,
        "is_superuser": user["is_superuser"],
    }


def require_permission(resource: str, action: str):
    async def permission_checker(current_user: dict = Depends(get_current_user)):
        if current_user["is_superuser"]:
            return current_user

        from chatchat.server.db.repository.user_repository import check_user_permission
        if not check_user_permission(
            current_user["user_id"],
            current_user["tenant_id"],
            resource,
            action,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {resource}",
            )

        return current_user

    return permission_checker
