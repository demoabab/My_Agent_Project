"""Database base configuration. No engines created at import time."""
import json

from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker

Base: DeclarativeMeta = declarative_base()


def get_engine():
    """Lazy accessor for the sync engine. Replaces old module-level `engine`."""
    from chatchat.server.db.manager import db_manager
    return db_manager.sync_engine


def get_session_local():
    """Lazy accessor for session factory. Replaces old module-level `SessionLocal`."""
    from chatchat.server.db.manager import db_manager
    return db_manager.sync_session_factory()


def __getattr__(name):
    if name == "engine":
        return get_engine()
    if name == "SessionLocal":
        return get_session_local()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
