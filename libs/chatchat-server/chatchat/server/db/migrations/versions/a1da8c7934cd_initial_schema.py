"""initial_schema

Revision ID: a1da8c7934cd
Revises:
Create Date: 2026-06-19 18:27:09.981822
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1da8c7934cd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from chatchat.server.db.base import Base
    # Import all models so their tables register on Base.metadata
    from chatchat.server.db.models.conversation_model import ConversationModel  # noqa: F401
    from chatchat.server.db.models.human_message_event import HumanMessageEvent  # noqa: F401
    from chatchat.server.db.models.knowledge_base_model import KnowledgeBaseModel  # noqa: F401
    from chatchat.server.db.models.knowledge_file_model import KnowledgeFileModel, FileDocModel  # noqa: F401
    from chatchat.server.db.models.knowledge_metadata_model import SummaryChunkModel  # noqa: F401
    from chatchat.server.db.models.mcp_connection_model import MCPConnectionModel, MCPProfileModel  # noqa: F401
    from chatchat.server.db.models.message_model import MessageModel  # noqa: F401

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from chatchat.server.db.base import Base
    from chatchat.server.db.models.conversation_model import ConversationModel  # noqa: F401
    from chatchat.server.db.models.human_message_event import HumanMessageEvent  # noqa: F401
    from chatchat.server.db.models.knowledge_base_model import KnowledgeBaseModel  # noqa: F401
    from chatchat.server.db.models.knowledge_file_model import KnowledgeFileModel, FileDocModel  # noqa: F401
    from chatchat.server.db.models.knowledge_metadata_model import SummaryChunkModel  # noqa: F401
    from chatchat.server.db.models.mcp_connection_model import MCPConnectionModel, MCPProfileModel  # noqa: F401
    from chatchat.server.db.models.message_model import MessageModel  # noqa: F401

    Base.metadata.drop_all(bind=op.get_bind())
