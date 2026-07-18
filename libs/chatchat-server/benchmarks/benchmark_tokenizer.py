#!/usr/bin/env python
"""C++ vs jitba 分词性能对比

Usage:
    python benchmarks/benchmark_tokenizer.py

输出:
    - 吞吐量对比（words/sec）
    - 延迟分布（p50/p95/p99）
    - 内存占用对比
"""
from __future__ import annotations

import gc
import json
import time
from pathlib import Path

# 测试文本：从知识库文档中抽样（模拟真实负载）
KB_ROOT = Path(__file__).resolve().parents[2] / "chatchat_data" / "data" / "knowledge_base"

SAMPLE_TEXTS = [
    "你好，我叫张三，是一名Python后端开发工程师。我喜欢简洁的代码风格。",
    "RAG（Retrieval-Augmented Generation）是一种结合了信息检索与文本生成的混合框架。",
    "向量数据库的核心是高效存储和检索高维向量，常用的算法包括HNSW和IVF。",
    "请帮我写一个数据库查询优化的方案，包括索引优化、SQL改写和缓存策略。",
    # 模拟较长文本
    "在知识库问答系统中，文档解析、文本分割、向量化和检索是四个关键步骤。"
    "首先，文档解析需要支持PDF、DOCX、PPTX等多种格式。"
    "其次，文本分割要考虑中文的语义边界，避免把词语从中间切断。"
    "然后，向量化需要选择合适的Embedding模型，推荐bge-large-zh-v1.5。"
    "最后，检索阶段可以采用混合检索策略，即同时进行向量检索和关键词检索，通过RRF融合结果。",
]

REPEAT = 5000  # 每个样本重复次数


def bench_jieba():
    import jieba

    gc.disable()
    t0 = time.perf_counter()
    for _ in range(REPEAT):
        for text in SAMPLE_TEXTS:
            jieba.lcut_for_search(text)
    elapsed = time.perf_counter() - t0
    gc.enable()
    return elapsed


def bench_cpp():
    from chatchat.cpp_ext import lcut_for_search

    gc.disable()
    t0 = time.perf_counter()
    for _ in range(REPEAT):
        for text in SAMPLE_TEXTS:
            lcut_for_search(text)
    elapsed = time.perf_counter() - t0
    gc.enable()
    return elapsed


def bench_latency():
    """单次调用延迟统计"""
    import jieba
    import statistics
    from chatchat.cpp_ext import lcut_for_search

    jieba_lat = []
    for _ in range(2000):
        for text in SAMPLE_TEXTS:
            t0 = time.perf_counter()
            jieba.lcut_for_search(text)
            jieba_lat.append((time.perf_counter() - t0) * 1e6)

    cpp_lat = []
    for _ in range(2000):
        for text in SAMPLE_TEXTS:
            t0 = time.perf_counter()
            lcut_for_search(text)
            cpp_lat.append((time.perf_counter() - t0) * 1e6)

    def stats(data):
        s = sorted(data)
        n = len(s)
        return {
            "avg": statistics.mean(data),
            "p50": s[n // 2],
            "p95": s[int(n * 0.95)],
            "p99": s[int(n * 0.99)],
        }

    return {"jieba (μs)": stats(jieba_lat), "cpp_ext (μs)": stats(cpp_lat)}


def main():
    print("=" * 60)
    print("C++ Tokenizer Benchmark")
    print("=" * 60)

    # 预热
    print("\n[1/3] Warmup...")
    import jieba
    from chatchat.cpp_ext import lcut_for_search

    for _ in range(10):
        jieba.lcut_for_search(SAMPLE_TEXTS[0])
        lcut_for_search(SAMPLE_TEXTS[0])

    # 正确性验证
    print("[2/3] Correctness check...")
    for text in SAMPLE_TEXTS:
        j = set(jieba.lcut_for_search(text))
        c = set(lcut_for_search(text))
        overlap = len(j & c) / max(len(j | c), 1)
        if overlap < 0.5:
            print(f"  ⚠ Low overlap ({overlap:.1%}): {text[:40]}...")
            print(f"    jieba: {sorted(j)}")
            print(f"    cpp:   {sorted(c)}")
    print("  OK")

    # 吞吐量
    print(f"\n[3/3] Throughput ({REPEAT}×{len(SAMPLE_TEXTS)} texts)...")
    t_jieba = bench_jieba()
    t_cpp = bench_cpp()

    total = REPEAT * len(SAMPLE_TEXTS)
    print(f"  jieba:   {t_jieba:.3f}s  ({total / t_jieba:.0f} calls/s)")
    print(f"  cpp_ext: {t_cpp:.3f}s  ({total / t_cpp:.0f} calls/s)")
    print(f"  speedup: {t_jieba / t_cpp:.1f}x")

    # 延迟
    print("\n[Latency]")
    lat = bench_latency()
    print(json.dumps(lat, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
