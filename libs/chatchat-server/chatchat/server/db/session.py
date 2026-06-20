from contextlib import asynccontextmanager, contextmanager
from functools import wraps
from typing import Generator

from sqlalchemy.orm import Session

from chatchat.server.db.base import get_session_local


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """上下文管理器用于自动获取 Session, 避免错误"""
    session = get_session_local()()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def with_session(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        with session_scope() as session:
            try:
                result = f(session, *args, **kwargs)
                session.commit()
                return result
            except:
                session.rollback()
                raise

    return wrapper


def with_tenant(f):
    """类似 with_session，但自动从 contextvars 读取当前 tenant_id 并注入 kwargs。
    仓库函数可通过 kwargs.get('tenant_id') 获取当前租户上下文。
    当未设置上下文时 tenant_id 为 None，仓库层应处理此情况（通常直接跳过过滤）。
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        from chatchat.server.context import get_current_tenant_id

        tenant_id = get_current_tenant_id()
        kwargs["tenant_id"] = tenant_id
        with session_scope() as session:
            try:
                result = f(session, *args, **kwargs)
                session.commit()
                return result
            except:
                session.rollback()
                raise

    return wrapper


def get_db() -> Generator[Session, None, None]:
    """FastAPI 依赖注入: 获取数据库会话"""
    session = get_session_local()()
    try:
        yield session
    finally:
        session.close()


def get_db0() -> Session:
    """直接获取数据库会话（调用者负责关闭）"""
    return get_session_local()()
