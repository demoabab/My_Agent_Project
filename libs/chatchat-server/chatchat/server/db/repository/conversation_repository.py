import uuid
from typing import List, Optional

from chatchat.server.db.models.conversation_model import ConversationModel
from chatchat.server.db.models.message_model import MessageModel
from chatchat.server.db.session import with_session


@with_session
def add_conversation_to_db(session, chat_type, name="", conversation_id=None, tenant_id: Optional[str] = None):
    if not conversation_id:
        conversation_id = uuid.uuid4().hex
    c = ConversationModel(id=conversation_id, chat_type=chat_type, name=name, tenant_id=tenant_id)
    session.add(c)
    return c.id


@with_session
def list_conversations_from_db(session, tenant_id: Optional[str] = None, limit: int = 50) -> List[dict]:
    query = session.query(ConversationModel)
    if tenant_id is not None:
        query = query.filter(ConversationModel.tenant_id == tenant_id)
    conversations = (
        query.order_by(ConversationModel.create_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": c.id,
            "name": c.name,
            "chat_type": c.chat_type,
            "create_time": c.create_time.isoformat() if c.create_time else "",
        }
        for c in conversations
    ]


@with_session
def get_conversation_from_db(session, conversation_id: str):
    c = session.query(ConversationModel).filter_by(id=conversation_id).first()
    if c is None:
        return None
    return {
        "id": c.id,
        "name": c.name,
        "chat_type": c.chat_type,
        "create_time": c.create_time.isoformat() if c.create_time else "",
    }


@with_session
def delete_conversation_from_db(session, conversation_id: str):
    session.query(ConversationModel).filter_by(id=conversation_id).delete()
    session.query(MessageModel).filter_by(conversation_id=conversation_id).delete()
    return conversation_id
