import uuid
from difflib import SequenceMatcher
from typing import List, Optional

from chatchat.server.db.models.memory_model import MemoryModel
from chatchat.server.db.session import with_session

SIMILARITY_THRESHOLD = 0.55


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


def _is_similar(a: str, b: str) -> bool:
    """快速判断两个字符串是否语义近似（基于字符级相似度）"""
    if a == b:
        return True
    # 归一化后比较
    na = a.lower().replace(" ", "").replace("_", "")
    nb = b.lower().replace(" ", "").replace("_", "")
    if na == nb:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= SIMILARITY_THRESHOLD


@with_session
def add_memory(
    session,
    user_id: str,
    memory_type: str,
    content: str,
    importance: float = 0.5,
    source_conversation_id: str = "",
    tenant_id: Optional[str] = None,
) -> str:
    existing_all = (
        session.query(MemoryModel)
        .filter(
            MemoryModel.user_id == user_id,
            MemoryModel.memory_type == memory_type,
        )
        .all()
    )
    for existing in existing_all:
        if _is_similar(content, existing.content):
            return existing.id
    memory = MemoryModel(
        id=uuid.uuid4().hex,
        user_id=user_id,
        memory_type=memory_type,
        content=content,
        importance=importance,
        source_conversation_id=source_conversation_id,
        tenant_id=tenant_id,
    )
    session.add(memory)
    return memory.id


@with_session
def list_memories(
    session,
    user_id: str,
    limit: int = 10,
    tenant_id: Optional[str] = None,
) -> List[dict]:
    query = session.query(MemoryModel).filter(MemoryModel.user_id == user_id)
    query = _apply_tenant_filter(query, MemoryModel, tenant_id)
    memories = (
        query.order_by(MemoryModel.importance.desc())
        .order_by(MemoryModel.create_time.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "user_id": m.user_id,
            "memory_type": m.memory_type,
            "content": m.content,
            "importance": m.importance,
            "source_conversation_id": m.source_conversation_id,
            "access_count": m.access_count,
            "create_time": m.create_time.isoformat() if m.create_time else None,
        }
        for m in memories
    ]


@with_session
def increment_memory_access(session, memory_id: str) -> None:
    memory = session.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
    if memory:
        memory.access_count = (memory.access_count or 0) + 1
        session.add(memory)


@with_session
def delete_memory(session, memory_id: str) -> None:
    session.query(MemoryModel).filter(MemoryModel.id == memory_id).delete()


@with_session
def delete_old_memories(session, user_id: str, keep_count: int = 50) -> int:
    subquery = (
        session.query(MemoryModel.id)
        .filter(MemoryModel.user_id == user_id)
        .order_by(MemoryModel.importance.desc(), MemoryModel.create_time.desc())
        .limit(keep_count)
        .subquery()
    )
    result = (
        session.query(MemoryModel)
        .filter(MemoryModel.user_id == user_id, ~MemoryModel.id.in_(session.query(subquery.c.id)))
        .delete(synchronize_session=False)
    )
    return result
