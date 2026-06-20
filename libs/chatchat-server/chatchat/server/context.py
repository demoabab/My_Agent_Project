import contextvars
from typing import Optional

_current_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)
_current_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "current_user_id", default=None
)


def get_current_tenant_id() -> Optional[str]:
    return _current_tenant_id.get()


def get_current_user_id() -> Optional[str]:
    return _current_user_id.get()


def set_current_tenant_context(tenant_id: Optional[str], user_id: Optional[str]):
    _current_tenant_id.set(tenant_id)
    _current_user_id.set(user_id)


def clear_tenant_context():
    _current_tenant_id.set(None)
    _current_user_id.set(None)
