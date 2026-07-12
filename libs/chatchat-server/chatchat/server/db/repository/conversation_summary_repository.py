from typing import List, Optional

from sqlalchemy import text

from chatchat.server.db.models.conversation_summary_model import ConversationSummaryModel
from chatchat.server.db.session import with_session


@with_session
def add_summary(
    session,
    conversation_id: str,
    summary: str,
    key_points: list = None,
    original_token_count: int = 0,
    summary_token_count: int = 0,
    tenant_id: Optional[str] = None,
) -> None:
    existing = session.query(ConversationSummaryModel).filter(
        ConversationSummaryModel.conversation_id == conversation_id
    ).first()
    if existing:
        existing.summary = summary
        existing.key_points = key_points or []
        existing.original_token_count = original_token_count
        existing.summary_token_count = summary_token_count
        session.add(existing)
    else:
        session.add(ConversationSummaryModel(
            conversation_id=conversation_id,
            summary=summary,
            key_points=key_points or [],
            original_token_count=original_token_count,
            summary_token_count=summary_token_count,
            tenant_id=tenant_id,
        ))


@with_session
def get_summary(session, conversation_id: str) -> Optional[dict]:
    s = session.query(ConversationSummaryModel).filter(
        ConversationSummaryModel.conversation_id == conversation_id
    ).first()
    if not s:
        return None
    return {
        "conversation_id": s.conversation_id,
        "summary": s.summary,
        "key_points": s.key_points or [],
        "original_token_count": s.original_token_count,
        "summary_token_count": s.summary_token_count,
    }


@with_session
def list_summaries(session, user_id: str, limit: int = 5) -> List[dict]:
    sql = text("""
        SELECT cs.conversation_id, cs.summary, cs.key_points, cs.create_time
        FROM conversation_summary cs
        INNER JOIN conversation c ON cs.conversation_id = c.id
        WHERE c.tenant_id IN (
            SELECT ut.tenant_id FROM user_tenant ut WHERE ut.user_id = :user_id
        )
        ORDER BY cs.create_time DESC
        LIMIT :limit
    """)
    rows = session.execute(sql, {"user_id": user_id, "limit": limit}).fetchall()
    return [
        {
            "conversation_id": r.conversation_id,
            "summary": r.summary,
            "key_points": r.key_points or [],
            "create_time": r.create_time.isoformat() if r.create_time else None,
        }
        for r in rows
    ]
