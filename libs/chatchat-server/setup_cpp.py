"""C++ 分词扩展 — setuptools 编译脚本

用法:
    pip install pybind11 setuptools
    python setup_cpp.py build_ext --inplace

或者通过 pip 安装可编辑模式:
    pip install -e ".[cpp]"  (未来支持)

编译成功后产物为 chatchat/cpp_ext/_tokenizer.cp39-win_amd64.pyd
"""
from __future__ import annotations

import sys
from pathlib import Path

from setuptools import Extension, setup
from pybind11.setup_helpers import Pybind11Extension, build_ext

HERE = Path(__file__).resolve().parent
SRC_DIR = HERE / "chatchat" / "cpp_ext"

# 编译器优化参数
if sys.platform == "win32":
    EXTRA_FLAGS = ["/O2", "/arch:AVX2", "/GL"]
    LINK_FLAGS = ["/LTCG"]
else:
    EXTRA_FLAGS = ["-O3", "-march=native", "-flto"]
    LINK_FLAGS = ["-flto"]

ext_modules = [
    Pybind11Extension(
        "chatchat.cpp_ext._tokenizer",
        sources=[
            str(SRC_DIR / "tokenizer.cpp"),
            str(SRC_DIR / "bindings.cpp"),
        ],
        include_dirs=[str(SRC_DIR)],
        cxx_std=14,
        extra_compile_args=EXTRA_FLAGS,
        extra_link_args=LINK_FLAGS,
        define_macros=[("CHT_BUILDING", "1")],
    ),
]

setup(
    name="chatchat-tokenizer",
    version="0.1.0",
    author="chatchat",
    description="C++ Chinese tokenizer extension for langchain-chatchat",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
