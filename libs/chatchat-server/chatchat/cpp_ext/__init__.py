"""C++ 中文分词加速模块

基于 pybind11 + Trie/FMM 算法的高性能分词器，jitba.lcut_for_search 的直接替代。

Usage:
    from chatchat.cpp_ext import lcut_for_search
    tokens = lcut_for_search("北京天气怎么样")
"""
from __future__ import annotations

import os
from pathlib import Path

# Singleton — 全局共享一个 Tokenizer 实例，避免重复初始化
_tokenizer = None


def _get_tokenizer():
    """延迟初始化全局 Tokenizer"""
    global _tokenizer
    if _tokenizer is not None:
        return _tokenizer

    from chatchat.cpp_ext._tokenizer import Tokenizer

    _tokenizer = Tokenizer()

    # 尝试加载 jieba 完整词典
    dict_paths = [
        os.environ.get("CHAT_DICT_PATH", ""),
        Path(__file__).parent / "dict.txt",
    ]
    # 自动探测 jieba 词典
    try:
        import jieba
        dict_paths.append(Path(jieba.__file__).parent / "dict.txt")
    except ImportError:
        pass
    for p in dict_paths:
        if p and Path(p).exists():
            loaded = _tokenizer.load_dict(str(p))
            break
    else:
        loaded = 0

    if loaded:
        import sys
        print(f"[cpp_tokenizer] +{loaded} words from dict.txt, "
              f"total={_tokenizer.dict_size}", file=sys.stderr)
    return _tokenizer


def lcut_for_search(text: str) -> list[str]:
    """搜索引擎模式分词 — jieba.lcut_for_search 的 C++ 替代"""
    return _get_tokenizer().lcut_for_search(text)


def lcut(text: str) -> list[str]:
    """精确模式分词 — jieba.lcut 的 C++ 替代"""
    return _get_tokenizer().lcut(text)


def cut(text: str) -> list[str]:
    """精确模式分词（生成器语义的 list 版本）"""
    return _get_tokenizer().cut(text)


def load_dict(path: str) -> int:
    """运行时加载额外词典"""
    return _get_tokenizer().load_dict(path)
