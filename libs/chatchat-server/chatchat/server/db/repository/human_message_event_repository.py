import uuid
from typing import Dict, List, Optional

from chatchat.server.db.models.human_message_event import HumanMessageEvent
from chatchat.server.db.session import with_session


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


@with_session
def add_human_message_event_to_db(
    session,
    call_id: str,
    conversation_id: str,
    function_name: str,
    kwargs: str,
    comment: str,
    action: str,
    tenant_id: Optional[str] = None,
):
    m = HumanMessageEvent(
        call_id=call_id,
        conversation_id=conversation_id,
        function_name=function_name,
        kwargs=kwargs,
        comment=comment,
        action=action,
        tenant_id=tenant_id,
    )
    session.add(m)
    session.commit()
    return m.id


@with_session
def get_human_message_event_by_id(session, call_id) -> HumanMessageEvent:
    m = session.query(HumanMessageEvent).filter_by(call_id=call_id).first()
    return m


@with_session
def list_human_message_event(session, conversation_id: str, tenant_id: Optional[str] = None) -> List[HumanMessageEvent]:
    query = session.query(HumanMessageEvent).filter_by(conversation_id=conversation_id)
    query = _apply_tenant_filter(query, HumanMessageEvent, tenant_id)
    m = query.all()
    return m


@with_session
def update_human_message_event(session, call_id, comment: str = None, action: str = None):
    m = get_human_message_event_by_id(call_id)
    if m is not None:
        if comment is not None:
            m.comment = comment
        if action is not None:
            m.action = action
        session.add(m)
        session.commit()
        return m.id
