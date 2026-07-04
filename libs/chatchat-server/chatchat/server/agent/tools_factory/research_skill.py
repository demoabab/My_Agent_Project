"""
深度调研 Skill —— 迷你 Agent 编排 search_internet + 百度百科 + url_reader
执行流程（确定性编排，每一步可追踪）:
  Step 1/4 — 并行搜索（互联网 + 百度百科）
  Step 2/4 — 提取高价值 URL
  Step 3/4 — 并行抓取网页内容
  Step 4/4 — LLM 归纳生成结构化调研报告
"""
import json
import logging
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from langchain_core.messages import HumanMessage, SystemMessage

from chatchat.server.pydantic_v1 import Field
from chatchat.server.utils import get_tool_config, get_ChatOpenAI, get_default_llm
from chatchat.server.agent.tools_factory.tools_registry import regist_tool
from langchain_chatchat.agent_toolkits.all_tools.tool import BaseToolOutput
from .search_internet import search_engine

logger = logging.getLogger(__name__)

MAX_URLS = 3
MAX_CONTENT_LENGTH = 3000
REPORT_PROMPT = """你是一个专业的调研分析师。请根据以下多源搜索材料，针对调研主题生成一份结构化的调研报告。

## 调研主题
{topic}

## 互联网搜索结果
{internet_results}

## 百科搜索结果
{wiki_results}

## 网页详细内容
{web_contents}

## 报告要求
请用中文生成一份完整的调研报告，包含以下结构：
1. **概述** - 2-3句话总结调研主题的核心发现
2. **关键信息** - 按要点列出最重要的信息（每条带来源标记）
3. **深度分析** - 对主题进行深入分析（2-3段）
4. **信息来源** - 列出所有引用的来源URL

报告应该专业、客观、信息密度高。"""


def _now_ms():
    return int(time.time() * 1000)


def _extract_urls(text):
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, text)
    seen = set()
    result = []
    for url in urls:
        if url not in seen and not url.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
            seen.add(url)
            result.append(url)
    return result[:MAX_URLS]


def _fetch_url_content(url, timeout=15):
    try:
        response = requests.get(f"https://r.jina.ai/{url}", timeout=timeout)
        if response.status_code == 200:
            return response.text[:MAX_CONTENT_LENGTH]
    except Exception:
        pass
    return ""


def _search_internet(query):
    """返回 (格式化结果, 结果数量, URL列表)"""
    try:
        tool_config = get_tool_config("search_internet")
        result = search_engine(query=query, top_k=5, config=tool_config)
        docs = result.get("docs", [])
        if not docs:
            return "（无搜索结果）", 0, []

        lines = []
        urls = []
        for i, doc in enumerate(docs[:5], 1):
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            source = metadata.get('source', metadata.get('link', ''))
            title = metadata.get('filename', metadata.get('title', ''))
            lines.append(f"[{i}] {title}\n    URL: {source}\n    {content[:300]}...")
            if source:
                urls.append(source)
        return "\n\n".join(lines), len(docs), urls
    except Exception as e:
        logger.error(f"Internet search failed: {e}")
        return f"（搜索失败: {e}）", 0, []


def _search_baidu_baike(query):
    """通过搜索引擎限定 site:baike.baidu.com 搜索百度百科，返回 (格式化结果, 结果字数)"""
    try:
        tool_config = get_tool_config("search_internet")
        result = search_engine(query=f"site:baike.baidu.com {query}", top_k=3, config=tool_config)
        docs = result.get("docs", [])
        if not docs:
            return "（未找到相关百度百科条目）", 0

        lines = []
        total_chars = 0
        for i, doc in enumerate(docs[:3], 1):
            content = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            metadata = doc.metadata if hasattr(doc, 'metadata') else {}
            title = metadata.get('filename', metadata.get('title', ''))
            lines.append(f"[百度百科 {i}] {title}\n{content[:500]}")
            total_chars += len(content)
        return "\n\n".join(lines), total_chars
    except Exception as e:
        logger.error(f"Baidu Baike search failed: {e}")
        return f"（百度百科搜索失败: {e}）", 0


def _generate_report(topic, internet, wiki, web_contents):
    """返回 (报告内容, 是否使用了LLM)"""
    try:
        llm = get_ChatOpenAI(
            model_name=get_default_llm(),
            temperature=0.3,
            max_tokens=2048,
            streaming=False,
        )
        messages = [
            SystemMessage(content="你是一个专业、严谨的调研分析师，擅长从多源信息中提炼关键洞察。"),
            HumanMessage(content=REPORT_PROMPT.format(
                topic=topic, internet_results=internet,
                wiki_results=wiki, web_contents=web_contents,
            )),
        ]
        response = llm.invoke(messages)
        return (response.content if hasattr(response, 'content') else str(response)), True
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        fallback = f"""## 调研主题: {topic}

### 互联网搜索结果
{internet}

### 百科搜索结果
{wiki}

### 网页详细内容
{web_contents}

（LLM 摘要生成失败，以上为原始搜索数据）"""
        return fallback, False


@regist_tool(title="深度调研", description="对任意主题进行深度调研。自动编排搜索->抓取->分析流程，生成结构化调研报告（含概述/关键信息/深度分析/来源）。每步执行状态透明可追踪。")
def research_skill(
    topic: str = Field(description="需要调研的主题或问题，越具体越好"),
):
    """
    深度调研迷你 Agent —— 确定性编排 4 步调研流程，每一步状态透明可追踪。

    执行步骤:
      Step 1/4: 并行搜索（互联网 + 百度百科）
      Step 2/4: 提取高价值 URL
      Step 3/4: 并行抓取网页内容
      Step 4/4: LLM 归纳生成结构化报告
    """
    steps = []
    t_start = _now_ms()
    logger.info(f"[research_skill] ========== 开始深度调研: {topic} ==========")

    # ── Step 1/4: 并行搜索 ──
    step1_start = _now_ms()
    logger.info(f"[research_skill] [Step 1/4] 并行搜索: 互联网 + 百度百科...")
    internet_result, baike_result = "", ""
    internet_count, baike_chars = 0, 0
    internet_urls = []

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_net = pool.submit(_search_internet, topic)
        f_baike = pool.submit(_search_baidu_baike, topic)
        try:
            internet_result, internet_count, internet_urls = f_net.result(timeout=30)
        except Exception as e:
            internet_result = f"（超时: {e}）"
        try:
            baike_result, baike_chars = f_baike.result(timeout=30)
        except Exception as e:
            baike_result = f"（超时: {e}）"

    step1_ms = _now_ms() - step1_start
    internet_ok = "（搜索失败" not in internet_result and "超时" not in internet_result and "无搜索结果" not in internet_result
    baike_ok = "未找到" not in baike_result and "超时" not in baike_result
    logger.info(f"[research_skill] [Step 1/4] 完成 ({step1_ms}ms) | 互联网: {'OK' if internet_ok else 'FAIL'} ({internet_count}条) | 百度百科: {'OK' if baike_ok else 'NONE'} ({baike_chars}字)")
    steps.append({
        "step": 1, "name": "并行搜索",
        "actions": [
            {"tool": "search_internet", "status": "success" if internet_ok else "failed", "result_count": internet_count, "duration_ms": step1_ms},
            {"tool": "baidu_baike_search", "status": "success" if baike_ok else "not_found", "result_chars": baike_chars, "duration_ms": step1_ms},
        ],
        "duration_ms": step1_ms,
    })

    # ── Step 2/4: 提取 URL ──
    step2_start = _now_ms()
    logger.info(f"[research_skill] [Step 2/4] 提取高价值 URL...")
    urls = _extract_urls(internet_result)
    step2_ms = _now_ms() - step2_start
    logger.info(f"[research_skill] [Step 2/4] 完成 ({step2_ms}ms) | 提取到 {len(urls)} 个 URL: {urls}")
    steps.append({
        "step": 2, "name": "提取URL",
        "urls_found": len(urls),
        "urls": urls,
        "duration_ms": step2_ms,
    })

    # ── Step 3/4: 并行抓取网页 ──
    step3_start = _now_ms()
    logger.info(f"[research_skill] [Step 3/4] 并行抓取 {len(urls)} 个网页内容...")
    web_parts = []
    if urls:
        with ThreadPoolExecutor(max_workers=min(len(urls), 3)) as pool:
            futures = {pool.submit(_fetch_url_content, u): u for u in urls}
            for future in as_completed(futures, timeout=20):
                url = futures[future]
                try:
                    content = future.result(timeout=15)
                    if content:
                        web_parts.append(f"--- 来源: {url} ---\n{content}")
                        logger.info(f"[research_skill] [Step 3/4]   已抓取: {url} ({len(content)}字)")
                except Exception:
                    pass

    web_contents = "\n\n".join(web_parts) if web_parts else "（未抓取网页详细内容）"
    step3_ms = _now_ms() - step3_start
    logger.info(f"[research_skill] [Step 3/4] 完成 ({step3_ms}ms) | 成功抓取 {len(web_parts)}/{len(urls)} 个页面")
    steps.append({
        "step": 3, "name": "抓取网页",
        "pages_attempted": len(urls),
        "pages_fetched": len(web_parts),
        "duration_ms": step3_ms,
    })

    # ── Step 4/4: LLM 生成报告 ──
    step4_start = _now_ms()
    logger.info(f"[research_skill] [Step 4/4] LLM 归纳生成调研报告...")
    report, llm_used = _generate_report(topic, internet_result, baike_result, web_contents)
    step4_ms = _now_ms() - step4_start
    logger.info(f"[research_skill] [Step 4/4] 完成 ({step4_ms}ms) | LLM: {'used' if llm_used else 'fallback'} | 报告长度: {len(report)}字")

    steps.append({
        "step": 4, "name": "生成报告",
        "llm_used": llm_used,
        "report_length": len(report),
        "duration_ms": step4_ms,
    })

    total_ms = _now_ms() - t_start
    logger.info(f"[research_skill] ========== 调研完成 ({total_ms}ms) | 4/4 步骤 | 主题: {topic} ==========")

    return BaseToolOutput({
        "topic": topic,
        "report": report,
        "sources": urls,
        "execution_trace": {
            "total_steps": 4,
            "total_duration_ms": total_ms,
            "steps": steps,
        },
        "search_details": {
            "internet_search_status": "success" if internet_ok else "failed",
            "baidu_baike_search_status": "success" if baike_ok else "not_found",
            "web_pages_fetched": len(web_parts),
        }
    }, format="json")
