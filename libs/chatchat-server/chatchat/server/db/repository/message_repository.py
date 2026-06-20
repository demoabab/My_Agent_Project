import uuid
from typing import Dict, List, Optional

from chatchat.server.db.models.message_model import MessageModel
from chatchat.server.db.session import with_session


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


@with_session
def add_message_to_db(
    session,
    conversation_id: str,
    chat_type,
    query,
    response="",
    message_id=None,
    metadata: Dict = {},
    tenant_id: Optional[str] = None,
):
    if not message_id:
        message_id = uuid.uuid4().hex
    m = MessageModel(
        id=message_id,
        chat_type=chat_type,
        query=query,
        response=response,
        conversation_id=conversation_id,
        meta_data=metadata,
        tenant_id=tenant_id,
    )
    session.add(m)
    session.commit()
    return m.id


@with_session
def update_message(session, message_id, response: str = None, metadata: Dict = None):
    m = get_message_by_id(message_id)
    if m is not None:
        if response is not None:
            m.response = response
        if isinstance(metadata, dict):
            m.meta_data = metadata
        session.add(m)
        session.commit()
        return m.id


@with_session
def get_message_by_id(session, message_id) -> MessageModel:
    m = session.query(MessageModel).filter_by(id=message_id).first()
    return m


@with_session
def feedback_message_to_db(session, message_id, feedback_score, feedback_reason):
    m = session.query(MessageModel).filter_by(id=message_id).first()
    if m:
        m.feedback_score = feedback_score
        m.feedback_reason = feedback_reason
    session.commit()
    return m.id


@with_session
def filter_message(session, conversation_id: str, limit: int = 10, tenant_id: Optional[str] = None):
    query = session.query(MessageModel).filter_by(conversation_id=conversation_id)
    query = _apply_tenant_filter(query, MessageModel, tenant_id)
    messages = (
        query.filter(MessageModel.response != "")
        .order_by(MessageModel.create_time.desc())
        .limit(limit)
        .all()
    )
    data = []
    for m in messages:
        data.append({"query": m.query, "response": m.response, "metadata": m.meta_data})
    return data
