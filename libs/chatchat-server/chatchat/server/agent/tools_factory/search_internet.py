import logging
from typing import Dict, List

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.utilities.bing_search import BingSearchAPIWrapper
from langchain.utilities.searx_search import SearxSearchWrapper
from markdownify import markdownify
from strsimpy.normalized_levenshtein import NormalizedLevenshtein

from chatchat.settings import Settings
from chatchat.server.pydantic_v1 import Field
from chatchat.server.utils import get_tool_config

from .tools_registry import regist_tool, format_context

from langchain_chatchat.agent_toolkits.all_tools.tool import (
    BaseToolOutput,
)

logger = logging.getLogger(__name__)

def searx_search(text ,config, top_k: int):
    search = SearxSearchWrapper(
        searx_host=config["host"],
        engines=config["engines"],
        categories=config["categories"],
    )
    search.params["language"] = config.get("language", "zh-CN")
    try:
        return search.results(text, top_k)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"searx search failed at {config['host']}: {e}")
        return []


def bing_search(text, config, top_k:int):
    search = BingSearchAPIWrapper(
        bing_subscription_key=config["bing_key"],
        bing_search_url=config["bing_search_url"],
    )
    return search.results(text, top_k)


def duckduckgo_search(text, config, top_k:int):
    """DuckDuckGo 搜索，通过 requests + lite 端点，支持 HTTP_PROXY 代理（挂梯子时稳定）"""
    import os as _os
    import logging as _logging
    import requests as _requests
    from bs4 import BeautifulSoup as _BeautifulSoup

    _logger = _logging.getLogger(__name__)
    proxy = _os.environ.get("HTTPS_PROXY") or _os.environ.get("HTTP_PROXY") or None
    proxies = {"https": proxy, "http": proxy} if proxy else None

    try:
        resp = _requests.get(
            "https://lite.duckduckgo.com/lite/",
            params={"q": text},
            proxies=proxies,
            timeout=8,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        soup = _BeautifulSoup(resp.text, "html.parser")
        results = []
        for item in soup.select(".result")[:top_k]:
            link = item.select_one(".result__a")
            snippet = item.select_one(".result__snippet")
            if link and snippet:
                results.append({
                    "snippet": snippet.get_text(strip=True),
                    "link": link.get("href", ""),
                    "title": link.get_text(strip=True),
                })
        return results
    except Exception as e:
        _logger.warning(f"duckduckgo search failed: {e}")
        return []


def bing_web_search(text, config, top_k: int):
    """Bing 国内版网页爬虫搜索，cn.bing.com 国内可直接访问，无需 API Key。
    Agent 常追加"简介""业务介绍"等泛化词导致 cn.bing.com 误匹配到更泛化的内容
    （如"浙江大华 简介"→"浙江省"），因此先剥离尾部泛化词再搜索。"""
    import re as _re
    import requests as _requests
    from bs4 import BeautifulSoup as _BeautifulSoup

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    base_params = {"ense": "search"}
    all_results = []
    seen_links = set()

    # 剥离查询末尾的泛化修饰词，避免干扰 Bing 的关键词匹配
    tail_fillers = r'(\s*(?:简介|公司简介|业务介绍|主营业务|业务|介绍|官网|官方网站|股票代码|财报|年报|招聘|地址|电话|怎么样|如何|是什么|什么意思))+$'
    core_query = _re.sub(tail_fillers, '', text).strip()
    queries = [core_query] if core_query != text else [text]
    # 如果剥离后的核心词仍然较长（>10字），再尝试仅用核心实体名（取前6字）
    if len(core_query) > 10:
        short = _re.sub(r'[（(].*?[)）]', '', core_query).strip()[:12]
        if short != core_query:
            queries.append(short)

    for query in queries:
        try:
            resp = _requests.get(
                "https://cn.bing.com/search",
                params={**base_params, "q": f'"{query}"'},
                timeout=10,
                headers=headers,
            )
            resp.raise_for_status()
            soup = _BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("li.b_algo"):
                if len(all_results) >= top_k:
                    break
                title_el = item.select_one("h2 a") or item.select_one("h2")
                snippet_el = item.select_one(".b_caption p") or item.select_one(".b_lineclamp2") or item.select_one(".b_caption")
                if title_el and snippet_el:
                    link = title_el.get("href", "") if title_el.name == "a" else ""
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    all_results.append({
                        "snippet": snippet_el.get_text(strip=True),
                        "link": link,
                        "title": title_el.get_text(strip=True),
                    })
            if len(all_results) >= top_k:
                break
        except Exception:
            continue

    return all_results[:top_k]


def metaphor_search(
    text: str,
    config: dict,
    top_k:int
) -> List[Dict]:
    from metaphor_python import Metaphor

    client = Metaphor(config["metaphor_api_key"])
    search = client.search(text, num_results=top_k, use_autoprompt=True)
    contents = search.get_contents().contents
    for x in contents:
        x.extract = markdownify(x.extract)
    if config["split_result"]:
        docs = [
            Document(page_content=x.extract, metadata={"link": x.url, "title": x.title})
            for x in contents
        ]
        text_splitter = RecursiveCharacterTextSplitter(
            ["\n\n", "\n", ".", " "],
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
        )
        splitted_docs = text_splitter.split_documents(docs)
        if len(splitted_docs) > top_k:
            normal = NormalizedLevenshtein()
            for x in splitted_docs:
                x.metadata["score"] = normal.similarity(text, x.page_content)
            splitted_docs.sort(key=lambda x: x.metadata["score"], reverse=True)
            splitted_docs = splitted_docs[: top_k]

        docs = [
            {
                "snippet": x.page_content,
                "link": x.metadata["link"],
                "title": x.metadata["title"],
            }
            for x in splitted_docs
        ]
    else:
        docs = [
            {"snippet": x.extract, "link": x.url, "title": x.title} for x in contents
        ]

    return docs


SEARCH_ENGINES = {
    "bing": bing_search,
    "bing_web": bing_web_search,
    "duckduckgo": duckduckgo_search,
    "metaphor": metaphor_search,
    "searx": searx_search,
}


def search_result2docs(search_results) -> List[Document]:
    docs = []
    for result in search_results:
        doc = Document(
            page_content=result["snippet"] if "snippet" in result.keys() else "",
            metadata={
                "source": result["link"] if "link" in result.keys() else "",
                "filename": result["title"] if "title" in result.keys() else "",
            },
        )
        docs.append(doc)
    return docs


def search_engine(query: str, top_k:int=0, engine_name: str="", config: dict={}):
    config = config or get_tool_config("search_internet")
    if top_k <= 0:
        top_k = config.get("top_k", Settings.kb_settings.SEARCH_ENGINE_TOP_K)
    engine_name = engine_name or config.get("search_engine_name")
    logger.info(f"[search_engine] query='{query[:60]}' engine={engine_name} top_k={top_k}")
    search_engine_use = SEARCH_ENGINES[engine_name]
    results = search_engine_use(
        text=query, config=config["search_engine_config"][engine_name], top_k=top_k
    )
    docs = [x for x in search_result2docs(results) if x.page_content and x.page_content.strip()]
    logger.info(f"[search_engine] returned {len(docs)} docs, first title: {docs[0].metadata.get('filename', 'N/A')[:80] if docs else 'N/A'}")
    return {"docs": docs, "search_engine": engine_name}


@regist_tool(title="互联网搜索")
def search_internet(query: str = Field(description="query for Internet search")):
    """Use this tool to use bing search engine to search the internet and get information."""
    return BaseToolOutput(search_engine(query=query), format=format_context)
