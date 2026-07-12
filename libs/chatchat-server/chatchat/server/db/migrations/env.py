"""Alembic migration environment.

Uses the synchronous SQLAlchemy engine for migrations.
The alembic.ini sqlalchemy.url is overridden at runtime from Settings.
"""
from alembic import context
from sqlalchemy import engine_from_config, pool

from chatchat.settings import Settings
from chatchat.server.db.base import Base

# Import all models to ensure they are registered on Base.metadata
from chatchat.server.db.models.conversation_model import ConversationModel
from chatchat.server.db.models.human_message_event import HumanMessageEvent  # noqa: F401
from chatchat.server.db.models.knowledge_base_model import KnowledgeBaseModel
from chatchat.server.db.models.knowledge_file_model import KnowledgeFileModel, FileDocModel
from chatchat.server.db.models.knowledge_metadata_model import SummaryChunkModel
from chatchat.server.db.models.mcp_connection_model import MCPConnectionModel, MCPProfileModel
from chatchat.server.db.models.message_model import MessageModel
from chatchat.server.db.models.user_model import UserModel
from chatchat.server.db.models.tenant_model import TenantModel
from chatchat.server.db.models.user_tenant import UserTenantModel
from chatchat.server.db.models.role_model import RoleModel, PermissionModel
from chatchat.server.db.models.user_profile_model import UserProfileModel  # noqa: F401
from chatchat.server.db.models.memory_model import MemoryModel  # noqa: F401
from chatchat.server.db.models.conversation_summary_model import ConversationSummaryModel  # noqa: F401

target_metadata = Base.metadata


def run_migrations_offline():
    url = Settings.basic_settings.SQLALCHEMY_DATABASE_URI
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = context.config
    configuration.set_main_option(
        "sqlalchemy.url", Settings.basic_settings.SQLALCHEMY_DATABASE_URI
    )
    connectable = engine_from_config(
        configuration.get_section(configuration.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
