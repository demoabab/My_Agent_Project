"""Database connection manager.

Replaces module-level singleton engine with a configurable factory.
Supports both sync and async engines with lazy initialization.
"""
from typing import Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from chatchat.settings import Settings


class DatabaseManager:
    """Manages database connections throughout the application lifecycle.

    Engines are created lazily on first access, not at import time.
    """

    def __init__(self, database_uri: Optional[str] = None):
        self._database_uri = database_uri or Settings.basic_settings.SQLALCHEMY_DATABASE_URI
        self._sync_engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._sync_session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None

    @property
    def database_uri(self) -> str:
        return self._database_uri

    @property
    def sync_engine(self) -> Engine:
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self._database_uri,
                pool_pre_ping=True,
                pool_size=10 if not self._database_uri.startswith("sqlite") else 1,
                max_overflow=20,
                json_serializer=lambda obj: __import__("json").dumps(obj, ensure_ascii=False),
            )
        return self._sync_engine

    @property
    def async_engine(self) -> AsyncEngine:
        if self._async_engine is None:
            async_uri = self._to_async_uri(self._database_uri)
            self._async_engine = create_async_engine(
                async_uri,
                pool_pre_ping=True,
                pool_size=10 if not self._database_uri.startswith("sqlite") else 1,
                max_overflow=20,
            )
        return self._async_engine

    def sync_session_factory(self) -> sessionmaker:
        if self._sync_session_factory is None:
            self._sync_session_factory = sessionmaker(
                autocommit=False, autoflush=False, bind=self.sync_engine
            )
        return self._sync_session_factory

    def async_session_factory(self) -> async_sessionmaker:
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine, expire_on_commit=False
            )
        return self._async_session_factory

    def create_all_tables(self):
        """Create all tables. Used for initialization / fallback when Alembic not available."""
        from chatchat.server.db.base import Base
        Base.metadata.create_all(bind=self.sync_engine)

    def dispose(self):
        """Release all connection pools."""
        if self._sync_engine:
            self._sync_engine.dispose()
        if self._async_engine:
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_engine.dispose())
            except RuntimeError:
                asyncio.run(self._async_engine.dispose())

    @staticmethod
    def _to_async_uri(sync_uri: str) -> str:
        if sync_uri.startswith("sqlite"):
            return sync_uri.replace("sqlite:///", "sqlite+aiosqlite:///")
        elif sync_uri.startswith("postgresql"):
            return sync_uri.replace("postgresql://", "postgresql+asyncpg://")
        return sync_uri


# Global manager instance
db_manager = DatabaseManager()
