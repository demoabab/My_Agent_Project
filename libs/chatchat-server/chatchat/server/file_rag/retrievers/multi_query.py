from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Set

from langchain_core.documents import Document
from langchain_core.language_models import BaseLanguageModel
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.prompts.prompt import PromptTemplate

logger = logging.getLogger(__name__)


class LineListOutputParser(BaseOutputParser[List[str]]):
    def parse(self, text: str) -> List[str]:
        return [line.strip() for line in text.strip().split("\n") if line.strip()]


MULTI_QUERY_PROMPT_ZH = PromptTemplate(
    input_variables=["question", "num_queries"],
    template=(
        "你是一个AI语言助手。你的任务是对给定的用户问题，生成 {num_queries} 个不同角度的改写版本，"
        "用于从知识库中检索相关文档。通过从不同角度表述用户问题，帮助克服基于距离的相似度搜索的局限性。\n"
        "要求：\n"
        "1. 每条改写保持原意但使用不同的表达方式和关键词\n"
        "2. 可以包含同义词替换、抽象概念具体化、具体概念泛化等技巧\n"
        "3. 每行一条改写，不要编号，不要添加额外说明\n"
        "原始问题：{question}\n"
        "改写结果："
    ),
)


def _unique_documents(documents: List[Document]) -> List[Document]:
    seen_ids: Set[str] = set()
    seen_contents: Set[str] = set()
    result: List[Document] = []
    for doc in documents:
        doc_id = doc.metadata.get("id", "")
        content = doc.page_content
        if doc_id and doc_id in seen_ids:
            continue
        if not doc_id and content in seen_contents:
            continue
        if doc_id:
            seen_ids.add(doc_id)
        seen_contents.add(content)
        result.append(doc)
    return result


def _generate_queries(
    llm: BaseLanguageModel,
    question: str,
    num_queries: int = 3,
) -> List[str]:
    output_parser = LineListOutputParser()
    chain = MULTI_QUERY_PROMPT_ZH | llm | output_parser
    queries = chain.invoke({"question": question, "num_queries": num_queries})
    logger.info(f"MultiQuery generated queries for '{question[:50]}...': {queries}")
    return queries


async def _agenerate_queries(
    llm: BaseLanguageModel,
    question: str,
    num_queries: int = 3,
) -> List[str]:
    output_parser = LineListOutputParser()
    chain = MULTI_QUERY_PROMPT_ZH | llm | output_parser
    queries = await chain.ainvoke({"question": question, "num_queries": num_queries})
    logger.info(f"MultiQuery generated queries for '{question[:50]}...': {queries}")
    return queries


def multi_query_search(
    query: str,
    kb,
    top_k: int,
    score_threshold: float,
    llm: BaseLanguageModel,
    num_queries: int = 3,
    include_original: bool = True,
) -> List[Dict]:
    queries = _generate_queries(llm, query, num_queries)
    all_queries = [query] + queries if include_original else queries

    all_docs: List[Document] = []
    for q in all_queries:
        try:
            docs = kb.search_docs(q, top_k, score_threshold)
            all_docs.extend(docs)
        except Exception as e:
            logger.warning(f"MultiQuery search failed for '{q[:50]}...': {e}")

    unique_docs = _unique_documents(all_docs)
    logger.info(f"MultiQuery: {len(all_docs)} raw docs -> {len(unique_docs)} unique, returning top {top_k}")
    return [doc.dict() for doc in unique_docs[:top_k]]


async def multi_query_search_async(
    query: str,
    kb,
    top_k: int,
    score_threshold: float,
    llm: BaseLanguageModel,
    num_queries: int = 3,
    include_original: bool = True,
) -> List[Dict]:
    queries = await _agenerate_queries(llm, query, num_queries)
    all_queries = [query] + queries if include_original else queries

    def _search_all():
        results = []
        for q in all_queries:
            results.append(kb.search_docs(q, top_k, score_threshold))
        return results

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _search_all)

    all_docs: List[Document] = []
    for docs in results:
        all_docs.extend(docs)

    unique_docs = _unique_documents(all_docs)
    logger.info(f"MultiQuery: {len(all_docs)} raw docs -> {len(unique_docs)} unique, returning top {top_k}")
    return [doc.dict() for doc in unique_docs[:top_k]]
