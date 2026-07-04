"""快速验证 search_internet + 百度百科搜索能力，不依赖 Agent 框架"""
import sys
sys.path.insert(0, "D:/Langchain_Chatchat_master/libs/chatchat-server")

# 模拟一次最小启动：加载 Settings 和 logging
from chatchat.settings import Settings
from chatchat.utils import get_config_dict, get_log_file, get_timestamp_ms
import logging.config

logging_conf = get_config_dict(
    "INFO",
    get_log_file(log_path=Settings.basic_settings.LOG_PATH, sub_dir=f"test_search_{get_timestamp_ms()}"),
    1024 * 1024 * 1024 * 3,
    1024 * 1024 * 1024 * 3,
)
logging.config.dictConfig(logging_conf)

from chatchat.server.agent.tools_factory.search_internet import search_engine
from chatchat.server.utils import get_tool_config

QUERY = "Python 3.12 新特性"

print(f"\n{'='*60}")
print(f"测试搜索: {QUERY}")
print(f"{'='*60}")

# ── 1. 互联网搜索 ──
print("\n[1/2] 互联网搜索 (searx)...")
try:
    tool_config = get_tool_config("search_internet")
    print(f"  引擎: {tool_config.get('search_engine_name')}")
    print(f"  searx host: {tool_config.get('search_engine_config', {}).get('searx', {}).get('host')}")

    result = search_engine(query=QUERY, top_k=3, config=tool_config)
    docs = result.get("docs", [])
    print(f"  结果数: {len(docs)}")
    for i, doc in enumerate(docs, 1):
        content = doc.page_content[:150] if hasattr(doc, 'page_content') else str(doc)[:150]
        source = doc.metadata.get('source', 'N/A') if hasattr(doc, 'metadata') else 'N/A'
        print(f"  [{i}] {source}")
        print(f"      {content}...")
except Exception as e:
    print(f"  失败: {e}")

# ── 2. 百度百科搜索 ──
print("\n[2/2] 百度百科搜索 (site:baike.baidu.com)...")
try:
    tool_config = get_tool_config("search_internet")
    result = search_engine(query=f"site:baike.baidu.com {QUERY}", top_k=3, config=tool_config)
    docs = result.get("docs", [])
    print(f"  结果数: {len(docs)}")
    for i, doc in enumerate(docs, 1):
        content = doc.page_content[:150] if hasattr(doc, 'page_content') else str(doc)[:150]
        source = doc.metadata.get('source', 'N/A') if hasattr(doc, 'metadata') else 'N/A'
        print(f"  [{i}] {source}")
        print(f"      {content}...")
except Exception as e:
    print(f"  失败: {e}")

print(f"\n{'='*60}")
print("测试完成")
print(f"{'='*60}\n")
