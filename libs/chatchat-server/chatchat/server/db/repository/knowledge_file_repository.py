from typing import Dict, List, Optional

from chatchat.server.db.models.knowledge_base_model import KnowledgeBaseModel
from chatchat.server.db.models.knowledge_file_model import (
    FileDocModel,
    KnowledgeFileModel,
)
from chatchat.server.db.session import with_session
from chatchat.server.knowledge_base.utils import KnowledgeFile


def _apply_tenant_filter(query, model, tenant_id):
    if tenant_id is not None:
        return query.filter(model.tenant_id == tenant_id)
    return query


@with_session
def list_file_num_docs_id_by_kb_name_and_file_name(
    session,
    kb_name: str,
    file_name: str,
    tenant_id: Optional[str] = None,
) -> List[int]:
    query = session.query(FileDocModel.doc_id).filter_by(kb_name=kb_name, file_name=file_name)
    query = _apply_tenant_filter(query, FileDocModel, tenant_id)
    doc_ids = query.all()
    return [int(_id[0]) for _id in doc_ids]


@with_session
def list_docs_from_db(
    session,
    kb_name: str,
    file_name: str = None,
    metadata: Dict = {},
    tenant_id: Optional[str] = None,
) -> List[Dict]:
    docs = session.query(FileDocModel).filter(FileDocModel.kb_name.ilike(kb_name))
    docs = _apply_tenant_filter(docs, FileDocModel, tenant_id)
    if file_name:
        docs = docs.filter(FileDocModel.file_name.ilike(file_name))
    for k, v in metadata.items():
        docs = docs.filter(FileDocModel.meta_data[k].as_string() == str(v))

    return [{"id": x.doc_id, "metadata": x.metadata} for x in docs.all()]


@with_session
def delete_docs_from_db(
    session,
    kb_name: str,
    file_name: str = None,
    tenant_id: Optional[str] = None,
) -> List[Dict]:
    docs = list_docs_from_db(kb_name=kb_name, file_name=file_name, tenant_id=tenant_id)
    query = session.query(FileDocModel).filter(FileDocModel.kb_name.ilike(kb_name))
    query = _apply_tenant_filter(query, FileDocModel, tenant_id)
    if file_name:
        query = query.filter(FileDocModel.file_name.ilike(file_name))
    query.delete(synchronize_session=False)
    session.commit()
    return docs


@with_session
def add_docs_to_db(session, kb_name: str, file_name: str, doc_infos: List[Dict], tenant_id: Optional[str] = None):
    if doc_infos is None:
        print("输入的server.db.repository.knowledge_file_repository.add_docs_to_db的doc_infos参数为None")
        return False
    for d in doc_infos:
        obj = FileDocModel(
            kb_name=kb_name,
            file_name=file_name,
            doc_id=d["id"],
            meta_data=d["metadata"],
            tenant_id=tenant_id,
        )
        session.add(obj)
    return True


@with_session
def count_files_from_db(session, kb_name: str, tenant_id: Optional[str] = None) -> int:
    query = session.query(KnowledgeFileModel).filter(KnowledgeFileModel.kb_name.ilike(kb_name))
    query = _apply_tenant_filter(query, KnowledgeFileModel, tenant_id)
    return query.count()


@with_session
def list_files_from_db(session, kb_name, tenant_id: Optional[str] = None):
    query = session.query(KnowledgeFileModel).filter(KnowledgeFileModel.kb_name.ilike(kb_name))
    query = _apply_tenant_filter(query, KnowledgeFileModel, tenant_id)
    files = query.all()
    docs = [f.file_name for f in files]
    return docs


@with_session
def add_file_to_db(
    session,
    kb_file: KnowledgeFile,
    docs_count: int = 0,
    custom_docs: bool = False,
    doc_infos: List[Dict] = [],
    tenant_id: Optional[str] = None,
):
    query = session.query(KnowledgeBaseModel).filter_by(kb_name=kb_file.kb_name)
    query = _apply_tenant_filter(query, KnowledgeBaseModel, tenant_id)
    kb = query.first()
    if kb:
        file_query = session.query(KnowledgeFileModel).filter(
            KnowledgeFileModel.kb_name.ilike(kb_file.kb_name),
            KnowledgeFileModel.file_name.ilike(kb_file.filename),
        )
        file_query = _apply_tenant_filter(file_query, KnowledgeFileModel, tenant_id)
        existing_file: KnowledgeFileModel = file_query.first()
        mtime = kb_file.get_mtime()
        size = kb_file.get_size()

        if existing_file:
            existing_file.file_mtime = mtime
            existing_file.file_size = size
            existing_file.docs_count = docs_count
            existing_file.custom_docs = custom_docs
            existing_file.file_version += 1
        else:
            new_file = KnowledgeFileModel(
                file_name=kb_file.filename,
                file_ext=kb_file.ext,
                kb_name=kb_file.kb_name,
                document_loader_name=kb_file.document_loader_name,
                text_splitter_name=kb_file.text_splitter_name or "SpacyTextSplitter",
                file_mtime=mtime,
                file_size=size,
                docs_count=docs_count,
                custom_docs=custom_docs,
                tenant_id=tenant_id,
            )
            kb.file_count += 1
            session.add(new_file)
        add_docs_to_db(
            kb_name=kb_file.kb_name, file_name=kb_file.filename, doc_infos=doc_infos, tenant_id=tenant_id
        )
    return True


@with_session
def delete_file_from_db(session, kb_file: KnowledgeFile, tenant_id: Optional[str] = None):
    file_query = session.query(KnowledgeFileModel).filter(
        KnowledgeFileModel.file_name.ilike(kb_file.filename),
        KnowledgeFileModel.kb_name.ilike(kb_file.kb_name),
    )
    file_query = _apply_tenant_filter(file_query, KnowledgeFileModel, tenant_id)
    existing_file = file_query.first()
    if existing_file:
        session.delete(existing_file)
        delete_docs_from_db(kb_name=kb_file.kb_name, file_name=kb_file.filename, tenant_id=tenant_id)
        session.commit()

        kb_query = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(kb_file.kb_name))
        kb_query = _apply_tenant_filter(kb_query, KnowledgeBaseModel, tenant_id)
        kb = kb_query.first()
        if kb:
            kb.file_count -= 1
            session.commit()
    return True


@with_session
def delete_files_from_db(session, knowledge_base_name: str, tenant_id: Optional[str] = None):
    file_query = session.query(KnowledgeFileModel).filter(KnowledgeFileModel.kb_name.ilike(knowledge_base_name))
    file_query = _apply_tenant_filter(file_query, KnowledgeFileModel, tenant_id)
    file_query.delete(synchronize_session=False)

    doc_query = session.query(FileDocModel).filter(FileDocModel.kb_name.ilike(knowledge_base_name))
    doc_query = _apply_tenant_filter(doc_query, FileDocModel, tenant_id)
    doc_query.delete(synchronize_session=False)

    kb_query = session.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.kb_name.ilike(knowledge_base_name))
    kb_query = _apply_tenant_filter(kb_query, KnowledgeBaseModel, tenant_id)
    kb = kb_query.first()
    if kb:
        kb.file_count = 0

    session.commit()
    return True


@with_session
def file_exists_in_db(session, kb_file: KnowledgeFile, tenant_id: Optional[str] = None):
    file_query = session.query(KnowledgeFileModel).filter(
        KnowledgeFileModel.file_name.ilike(kb_file.filename),
        KnowledgeFileModel.kb_name.ilike(kb_file.kb_name),
    )
    file_query = _apply_tenant_filter(file_query, KnowledgeFileModel, tenant_id)
    existing_file = file_query.first()
    return True if existing_file else False


@with_session
def get_file_detail(session, kb_name: str, filename: str, tenant_id: Optional[str] = None) -> dict:
    file_query = session.query(KnowledgeFileModel).filter(
        KnowledgeFileModel.file_name.ilike(filename),
        KnowledgeFileModel.kb_name.ilike(kb_name),
    )
    file_query = _apply_tenant_filter(file_query, KnowledgeFileModel, tenant_id)
    file: KnowledgeFileModel = file_query.first()
    if file:
        return {
            "kb_name": file.kb_name,
            "file_name": file.file_name,
            "file_ext": file.file_ext,
            "file_version": file.file_version,
            "document_loader": file.document_loader_name,
            "text_splitter": file.text_splitter_name,
            "create_time": file.create_time,
            "file_mtime": file.file_mtime,
            "file_size": file.file_size,
            "custom_docs": file.custom_docs,
            "docs_count": file.docs_count,
        }
    else:
        return {}
