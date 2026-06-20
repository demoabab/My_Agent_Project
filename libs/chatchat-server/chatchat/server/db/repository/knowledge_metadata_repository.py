from typing import Dict, List, Optional

from chatchat.server.db.models.knowledge_metadata_model import SummaryChunkModel
from chatchat.server.db.session import with_session


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


@with_session
def list_summary_from_db(
    session,
    kb_name: str,
    metadata: Dict = {},
    tenant_id: Optional[str] = None,
) -> List[Dict]:
    docs = session.query(SummaryChunkModel).filter(SummaryChunkModel.kb_name.ilike(kb_name))
    docs = _apply_tenant_filter(docs, SummaryChunkModel, tenant_id)

    for k, v in metadata.items():
        docs = docs.filter(SummaryChunkModel.meta_data[k].as_string() == str(v))

    return [
        {
            "id": x.id,
            "summary_context": x.summary_context,
            "summary_id": x.summary_id,
            "doc_ids": x.doc_ids,
            "metadata": x.metadata,
        }
        for x in docs.all()
    ]


@with_session
def delete_summary_from_db(session, kb_name: str, tenant_id: Optional[str] = None) -> List[Dict]:
    docs = list_summary_from_db(kb_name=kb_name, tenant_id=tenant_id)
    query = session.query(SummaryChunkModel).filter(SummaryChunkModel.kb_name.ilike(kb_name))
    query = _apply_tenant_filter(query, SummaryChunkModel, tenant_id)
    query.delete(synchronize_session=False)
    session.commit()
    return docs


@with_session
def add_summary_to_db(session, kb_name: str, summary_infos: List[Dict], tenant_id: Optional[str] = None):
    for summary in summary_infos:
        obj = SummaryChunkModel(
            kb_name=kb_name,
            summary_context=summary["summary_context"],
            summary_id=summary["summary_id"],
            doc_ids=summary["doc_ids"],
            meta_data=summary["metadata"],
            tenant_id=tenant_id,
        )
        session.add(obj)

    session.commit()
    return True


@with_session
def count_summary_from_db(session, kb_name: str, tenant_id: Optional[str] = None) -> int:
    query = session.query(SummaryChunkModel).filter(SummaryChunkModel.kb_name.ilike(kb_name))
    query = _apply_tenant_filter(query, SummaryChunkModel, tenant_id)
    return query.count()
