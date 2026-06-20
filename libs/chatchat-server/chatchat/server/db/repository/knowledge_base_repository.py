from typing import Optional

from chatchat.server.db.models.knowledge_base_model import (
    KnowledgeBaseModel,
    KnowledgeBaseSchema,
)
from chatchat.server.db.session import with_session


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


def _add_tenant_id(kwargs, tenant_id):
    """向写入操作的 kwargs 注入 tenant_id"""
    pass  # 各函数自行处理


@with_session
def add_kb_to_db(session, kb_name, kb_info, vs_type, embed_model, tenant_id: Optional[str] = None):
    query = _apply_tenant_filter(
        session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)),
        KnowledgeBaseModel, tenant_id,
    )
    kb = query.first()
    if not kb:
        kb = KnowledgeBaseModel(
            kb_name=kb_name, kb_info=kb_info, vs_type=vs_type, embed_model=embed_model,
            tenant_id=tenant_id,
        )
        session.add(kb)
    else:
        kb.kb_info = kb_info
        kb.vs_type = vs_type
        kb.embed_model = embed_model
    return True


@with_session
def list_kbs_from_db(session, min_file_count: int = -1, tenant_id: Optional[str] = None):
    query = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.file_count > min_file_count)
    query = _apply_tenant_filter(query, KnowledgeBaseModel, tenant_id)
    kbs = query.all()
    kbs = [KnowledgeBaseSchema.model_validate(kb) for kb in kbs]
    return kbs


@with_session
def kb_exists(session, kb_name, tenant_id: Optional[str] = None):
    query = _apply_tenant_filter(
        session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)),
        KnowledgeBaseModel, tenant_id,
    )
    kb = query.first()
    status = True if kb else False
    return status


@with_session
def load_kb_from_db(session, kb_name, tenant_id: Optional[str] = None):
    query = _apply_tenant_filter(
        session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)),
        KnowledgeBaseModel, tenant_id,
    )
    kb = query.first()
    if kb:
        kb_name, vs_type, embed_model = kb.kb_name, kb.vs_type, kb.embed_model
    else:
        kb_name, vs_type, embed_model = None, None, None
    return kb_name, vs_type, embed_model


@with_session
def delete_kb_from_db(session, kb_name, tenant_id: Optional[str] = None):
    query = _apply_tenant_filter(
        session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)),
        KnowledgeBaseModel, tenant_id,
    )
    kb = query.first()
    if kb:
        session.delete(kb)
    return True


@with_session
def get_kb_detail(session, kb_name: str, tenant_id: Optional[str] = None) -> dict:
    query = _apply_tenant_filter(
        session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_name)),
        KnowledgeBaseModel, tenant_id,
    )
    kb = query.first()
    if kb:
        return {
            "kb_name": kb.kb_name,
            "kb_info": kb.kb_info,
            "vs_type": kb.vs_type,
            "embed_model": kb.embed_model,
            "file_count": kb.file_count,
            "create_time": kb.create_time,
        }
    else:
        return {}
