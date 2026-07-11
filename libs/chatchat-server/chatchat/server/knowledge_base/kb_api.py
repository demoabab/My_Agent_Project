import urllib

from fastapi import Body, Depends, Form

from chatchat.settings import Settings
from chatchat.server.auth.dependencies import get_current_user, require_permission
from chatchat.server.db.repository.knowledge_base_repository import list_kbs_from_db
from chatchat.server.knowledge_base.kb_service.base import KBServiceFactory
from chatchat.server.knowledge_base.utils import validate_kb_name
from chatchat.server.utils import BaseResponse, ListResponse, get_default_embedding
from chatchat.utils import build_logger


logger = build_logger()


def list_kbs(
    current_user: dict = Depends(get_current_user),
):
    # Get List of Knowledge Base
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else None
    return ListResponse(data=list_kbs_from_db(tenant_id=tenant_id))


def create_kb(
    knowledge_base_name: str = Form(..., examples=["samples"]),
    vector_store_type: str = Form(Settings.kb_settings.DEFAULT_VS_TYPE),
    kb_info: str = Form("", description="知识库内容简介，用于Agent选择知识库。"),
    embed_model: str = Form(get_default_embedding()),
    current_user: dict = Depends(require_permission("knowledge_base", "write")),
) -> BaseResponse:
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    if knowledge_base_name is None or knowledge_base_name.strip() == "":
        return BaseResponse(code=404, msg="知识库名称不能为空，请重新填写知识库名称")

    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else None
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, tenant_id=tenant_id)
    if kb is not None:
        return BaseResponse(code=404, msg=f"已存在同名知识库 {knowledge_base_name}")

    kb = KBServiceFactory.get_service(
        knowledge_base_name, vector_store_type, embed_model, kb_info=kb_info,
        tenant_id=tenant_id,
    )
    try:
        kb.create_kb()
    except Exception as e:
        msg = f"创建知识库出错： {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=200, msg=f"已新增知识库 {knowledge_base_name}")


def delete_kb(
    knowledge_base_name: str = Form(..., examples=["samples"]),
    current_user: dict = Depends(require_permission("knowledge_base", "delete")),
) -> BaseResponse:
    # Delete selected knowledge base
    if not validate_kb_name(knowledge_base_name):
        return BaseResponse(code=403, msg="Don't attack me")
    knowledge_base_name = urllib.parse.unquote(knowledge_base_name)

    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else None
    kb = KBServiceFactory.get_service_by_name(knowledge_base_name, tenant_id=tenant_id)

    if kb is None:
        return BaseResponse(code=404, msg=f"未找到知识库 {knowledge_base_name}")

    try:
        status = kb.clear_vs()
        status = kb.drop_kb()
        if status:
            return BaseResponse(code=200, msg=f"成功删除知识库 {knowledge_base_name}")
    except Exception as e:
        msg = f"删除知识库时出现意外： {e}"
        logger.error(f"{e.__class__.__name__}: {msg}")
        return BaseResponse(code=500, msg=msg)

    return BaseResponse(code=500, msg=f"删除知识库失败 {knowledge_base_name}")
