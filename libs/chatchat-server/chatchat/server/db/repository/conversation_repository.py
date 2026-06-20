import uuid
from typing import Optional

from chatchat.server.db.models.conversation_model import ConversationModel
from chatchat.server.db.session import with_session


@with_session
def add_conversation_to_db(session, chat_type, name="", conversation_id=None, tenant_id: Optional[str] = None):
    if not conversation_id:
        conversation_id = uuid.uuid4().hex
    c = ConversationModel(id=conversation_id, chat_type=chat_type, name=name, tenant_id=tenant_id)

    session.add(c)
    return c.id
