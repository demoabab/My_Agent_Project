"""长期记忆服务：记忆提取、加载、注入"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts.prompt import PromptTemplate

from chatchat.server.db.repository.memory_repository import (
    add_memory,
    delete_old_memories,
    increment_memory_access,
    list_memories,
)
from chatchat.server.db.repository.user_profile_repository import (
    append_key_facts,
    get_user_profile,
    upsert_user_profile,
)

logger = logging.getLogger(__name__)

MEMORY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["query", "response"],
    template=(
        "你是一个信息提取助手。请从以下用户与AI之间的对话中，提取值得长期记住的信息。\n"
        "\n"
        "提取规则：\n"
        "1. facts: 用户明确表述的事实信息（职业、技能、角色、正在做的工作等）\n"
        "2. preferences: 用户表达的偏好，必须使用以下中文键名：\n"
        "   - \"代码风格\": 用户喜欢的代码风格\n"
        "   - \"回答方式\": 用户期望的回答方式（如提供代码示例、简洁回答、详细解释等）\n"
        "   - \"专业领域\": 用户的专业领域\n"
        "   - \"语言偏好\": 用户的语言偏好\n"
        "3. decisions: 用户做出的决策或计划\n"
        "4. 只提取用户表达的信息，不要提取AI回答中的信息\n"
        "5. 如果没有值得记住的信息，返回空数组\n"
        "\n"
        "用户问题: {query}\n"
        "AI回答: {response}\n"
        "\n"
        "请以JSON格式输出，不要添加任何额外文字：\n"
        '{{"facts": ["事实1", "事实2"], "preferences": {{"代码风格": "简洁", "回答方式": "提供代码示例"}}, "decisions": ["决策1"]}}'
    ),
)

MEMORY_CONTEXT_TEMPLATE = """<user_memory>
{profile_section}
{memory_section}
</user_memory>

You MUST follow these rules:
1. Address the user by their name if you know it
2. Match the user's stated preferences (code examples, response style, etc.)
3. Reference the user's expertise domain when relevant"""


def _extract_memory(
    llm: BaseLanguageModel,
    query: str,
    response: str,
    user_id: str,
    conversation_id: str = "",
    tenant_id: Optional[str] = None,
) -> dict:
    """从本轮对话中提取记忆并持久化。返回提取到的信息。"""
    if not query or not response:
        return {"facts": [], "preferences": {}, "decisions": []}

    try:
        parser = JsonOutputParser()
        chain = MEMORY_EXTRACTION_PROMPT | llm | parser
        result = chain.invoke({"query": query, "response": response})
    except Exception as e:
        logger.warning(f"Memory extraction failed: {e}")
        return {"facts": [], "preferences": {}, "decisions": []}

    if not isinstance(result, dict):
        return {"facts": [], "preferences": {}, "decisions": []}

    facts = result.get("facts", [])
    preferences = result.get("preferences", {})
    decisions = result.get("decisions", [])

    # 写入 user_profile
    if facts:
        try:
            append_key_facts(user_id=user_id, facts=facts)
        except Exception as e:
            logger.warning(f"Failed to save facts: {e}")

    if preferences:
        try:
            pref_fields = {}
            if "response_style" in preferences:
                pref_fields["response_style"] = preferences["response_style"]
            if "language" in preferences:
                pref_fields["language"] = preferences["language"]
            if "expertise_domain" in preferences:
                pref_fields["expertise_domain"] = preferences["expertise_domain"]
            if "preferred_model" in preferences:
                pref_fields["preferred_model"] = preferences["preferred_model"]
            if pref_fields:
                upsert_user_profile(user_id=user_id, **pref_fields)
        except Exception as e:
            logger.warning(f"Failed to save preferences: {e}")

    # 写入 conversation_memory
    all_items = []
    for f in facts:
        all_items.append(("fact", f, 0.7))
    for d in decisions:
        all_items.append(("decision", d, 0.8))
    for k, v in preferences.items():
        all_items.append(("preference", f"{k}: {v}", 0.6))

    for mem_type, content, importance in all_items:
        try:
            add_memory(
                user_id=user_id,
                memory_type=mem_type,
                content=content,
                importance=importance,
                source_conversation_id=conversation_id,
                tenant_id=tenant_id,
            )
        except Exception as e:
            logger.warning(f"Failed to save memory: {e}")

    # 清理旧记忆，每人最多保留 100 条
    try:
        deleted = delete_old_memories(user_id=user_id, keep_count=100)
        if deleted:
            logger.info(f"Cleaned up {deleted} old memories for user {user_id}")
    except Exception as e:
        logger.warning(f"Failed to cleanup old memories: {e}")

    logger.info(f"Memory extracted for user {user_id}: {len(facts)} facts, {len(preferences)} prefs, {len(decisions)} decisions")
    return result


def load_user_memory(user_id: str, limit: int = 5) -> str:
    """加载用户画像和最近记忆，返回格式化的上下文字符串。若无记忆返回空字符串。"""
    profile = None
    memories = []

    try:
        profile = get_user_profile(user_id=user_id)
    except Exception as e:
        logger.warning(f"Failed to load profile: {e}")

    try:
        memories = list_memories(user_id=user_id, limit=limit)
    except Exception as e:
        logger.warning(f"Failed to load memories: {e}")

    if not profile and not memories:
        return ""

    # 构建画像段落
    profile_section = ""
    if profile:
        parts = []
        if profile.get("expertise_domain"):
            parts.append(f"- 专业领域: {profile['expertise_domain']}")
        if profile.get("key_facts"):
            for fact in profile["key_facts"][:5]:
                parts.append(f"- {fact}")
        if profile.get("response_style"):
            parts.append(f"- 回答风格偏好: {profile['response_style']}")
        if parts:
            profile_section = "<用户画像>\n" + "\n".join(parts) + "\n</用户画像>"

    # 构建记忆段落
    memory_section = ""
    if memories:
        mem_lines = []
        for m in memories:
            mem_lines.append(f"- [{m['memory_type']}] {m['content']}")
            try:
                increment_memory_access(memory_id=m["id"])
            except Exception:
                pass
        memory_section = "<历史记忆>\n" + "\n".join(mem_lines) + "\n</历史记忆>"

    context = MEMORY_CONTEXT_TEMPLATE.format(
        profile_section=profile_section,
        memory_section=memory_section,
    )
    logger.info(f"Loaded memory for user {user_id}: {len(memories)} recent items")
    return context
