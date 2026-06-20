"""Async session utilities for future use in async route handlers."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from chatchat.server.db.manager import db_manager


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 异步依赖注入: 获取异步数据库会话"""
    async_session_factory = db_manager.async_session_factory()
    async with async_session_factory() as session:
        yield session
