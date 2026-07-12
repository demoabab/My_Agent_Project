"""
MultiQuery 检索效果对比测试脚本

用法:
  cd libs/chatchat-server
  python test_multi_query.py

前提: 服务端已启动，且有可用的知识库 (默认 "samples")
"""
from __future__ import annotations

import json
import time
import requests

BASE_URL = "http://localhost:7861"
KB_NAME = "samples"

TEST_QUERIES = [
    "如何处理中文文本",
    "向量数据库的选型建议",
    "RAG系统架构设计",
]


def search(query: str, multi_query: bool = False) -> dict:
    """调用 kb_chat 接口，return_direct=True 只返回检索结果不入 LLM"""
    payload = {
        "query": query,
        "mode": "local_kb",
        "kb_name": KB_NAME,
        "multi_query": multi_query,
        "return_direct": True,
        "stream": False,
    }
    t0 = time.perf_counter()
    resp = requests.post(f"{BASE_URL}/chat/kb_chat", json=payload)
    elapsed = time.perf_counter() - t0
    data = resp.json()
    return {
        "query": query,
        "multi_query": multi_query,
        "elapsed": round(elapsed, 2),
        "doc_count": len(data.get("docs", [])),
        "docs": data.get("docs", []),
    }


def main():
    print("=" * 70)
    print("MultiQuery 检索效果对比测试")
    print("=" * 70)

    for q in TEST_QUERIES:
        print(f"\n{'─' * 70}")
        print(f"查询: {q}")

        # 普通检索
        baseline = search(q, multi_query=False)
        # 多查询检索
        enhanced = search(q, multi_query=True)

        print(f"\n{'指标':<20} {'普通检索':>20} {'多查询检索':>20}")
        print(f"{'─' * 60}")
        print(f"{'耗时 (秒)':<20} {baseline['elapsed']:>20.2f} {enhanced['elapsed']:>20.2f}")
        print(f"{'返回文档数':<20} {baseline['doc_count']:>20} {enhanced['doc_count']:>20}")

        # 对比去重后是否有增量文档
        baseline_contents = {d.get("page_content", "") for d in baseline["docs"]}
        enhanced_contents = {d.get("page_content", "") for d in enhanced["docs"]}
        new_docs = enhanced_contents - baseline_contents
        missing_docs = baseline_contents - enhanced_contents

        if new_docs:
            print(f"\n多查询检索独有的文档片段:")
            for i, doc in enumerate(new_docs, 1):
                preview = doc[:120].replace("\n", " ")
                print(f"  [{i}] {preview}...")

        if missing_docs:
            print(f"\n普通检索独有但多查询丢失的文档: {len(missing_docs)} 条")

        if not new_docs and not missing_docs:
            print(f"\n两次检索结果完全一致 (可能知识库文档数较少)")

    print(f"\n{'=' * 70}")
    print("测试完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
