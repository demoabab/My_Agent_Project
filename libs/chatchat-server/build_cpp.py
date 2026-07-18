#!/usr/bin/env python
"""C++ 分词扩展编译脚本

Usage:
    python build_cpp.py              # 编译 Release
    python build_cpp.py --debug      # 编译 Debug（含符号，便于调试）
    python build_cpp.py --clean      # 清理 build 目录
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_DIR = HERE / "chatchat" / "cpp_ext"
BUILD_DIR = SRC_DIR / "build"


def get_pybind11_cmake_dir():
    import pybind11
    return pybind11.get_cmake_dir()


def _find_mingw():
    """查找可用的 MinGW 工具链，返回 (bin_dir, cmake_generator)。
    优先级: winlibs > MSYS2 > conda m2w64"""
    import os
    candidates = [
        (r"D:\mingw64\mingw64\bin", "MinGW Makefiles"),   # winlibs zip 解压嵌套
        (r"D:\mingw64\bin", "MinGW Makefiles"),           # winlibs 直接解压
        (r"C:\msys64\mingw64\bin", "MinGW Makefiles"),     # MSYS2
        (r"C:\mingw64\bin", "MinGW Makefiles"),            # 其他
    ]
    for path, gen in candidates:
        gxx = os.path.join(path, "g++.exe")
        if os.path.isfile(gxx):
            return path, gen
    # conda m2w64
    conda_prefix = os.environ.get("CONDA_PREFIX", os.path.dirname(os.path.dirname(sys.executable)))
    if conda_prefix:
        path = os.path.join(conda_prefix, "Library", "mingw-w64", "bin")
        if os.path.isfile(os.path.join(path, "g++.exe")):
            return path, "MinGW Makefiles"
    return None, None


def _setup_env():
    """确保 MinGW 工具链在 PATH 中，返回 (mingw_bin, generator) 或 (None, None)"""
    if sys.platform != "win32":
        return None, None
    import os
    mingw_bin, gen = _find_mingw()
    if mingw_bin and mingw_bin not in os.environ["PATH"]:
        os.environ["PATH"] = mingw_bin + os.pathsep + os.environ["PATH"]
    return mingw_bin, gen


def main():
    mingw_bin, mingw_gen = _setup_env()
    parser = argparse.ArgumentParser(description="Build C++ tokenizer")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--generator", "-G", default="", help="CMake generator (e.g. 'MinGW Makefiles')")
    args = parser.parse_args()

    if args.clean:
        if BUILD_DIR.exists():
            shutil.rmtree(BUILD_DIR)
            print(f"[build] Removed {BUILD_DIR}")
        return

    BUILD_DIR.mkdir(exist_ok=True)

    # 检测可用的生成器
    gen = args.generator
    if not gen:
        if mingw_gen:
            gen = mingw_gen
        elif sys.platform == "win32":
            if shutil.which("nmake") or shutil.which("cl"):
                gen = "NMake Makefiles"
            else:
                sys.exit("[build] No compiler found. Install Visual Studio Build Tools or MinGW-w64.")
        else:
            gen = "Unix Makefiles"

    cmake_args = [
        "cmake",
        "-G", gen,
        str(SRC_DIR),
        f"-Dpybind11_DIR={get_pybind11_cmake_dir()}",
    ]

    # MinGW 需要显式指定编译器路径和 Python 库
    if mingw_bin:
        cmake_args += [
            f"-DCMAKE_MAKE_PROGRAM={mingw_bin}/mingw32-make.exe",
            f"-DCMAKE_CXX_COMPILER={mingw_bin}/g++.exe",
        ]

    import os, sysconfig
    python_dll = os.path.join(sysconfig.get_config_var("BINDIR"), f"python{sys.version_info.major}{sys.version_info.minor}.dll")
    if not os.path.exists(python_dll):
        python_dll = os.path.join(os.path.dirname(sys.executable), f"python{sys.version_info.major}{sys.version_info.minor}.dll")
    # 使用正斜杠避免 CMake 转义问题
    python_dll = python_dll.replace("\\", "/")
    include_dir = sysconfig.get_config_var("INCLUDEPY").replace("\\", "/")
    cmake_args += [
        f"-DPYTHON_EXECUTABLE={sys.executable.replace(chr(92), '/')}",
        f"-DPYTHON_INCLUDE_DIR={include_dir}",
        f"-DPYTHON_LIBRARY={python_dll}",
    ]

    if args.debug:
        cmake_args.append("-DCMAKE_BUILD_TYPE=Debug")
    else:
        cmake_args.append("-DCMAKE_BUILD_TYPE=Release")

    # Configure
    print(f"[build] Configuring: {' '.join(cmake_args)}")
    result = subprocess.run(cmake_args, cwd=str(BUILD_DIR))
    if result.returncode != 0:
        sys.exit(result.returncode)

    # Build
    build_args = [
        "cmake",
        "--build", str(BUILD_DIR),
        "--config", "Debug" if args.debug else "Release",
    ]
    print(f"[build] Building: {' '.join(build_args)}")
    result = subprocess.run(build_args)
    if result.returncode != 0:
        sys.exit(result.returncode)

    # Copy .pyd to package directory
    pyd_pattern = "_tokenizer*.pyd" if sys.platform == "win32" else "_tokenizer*.so"
    for pyd in BUILD_DIR.rglob(pyd_pattern):
        target = SRC_DIR / pyd.name
        shutil.copy2(pyd, target)
        print(f"[build] Copied {pyd.name} → {target}")

    # Copy MinGW runtime DLLs if needed
    if mingw_bin:
        for dll in ("libgcc_s_seh-1.dll", "libstdc++-6.dll", "libwinpthread-1.dll"):
            src = os.path.join(mingw_bin, dll)
            dst = SRC_DIR / dll
            if os.path.isfile(src):
                shutil.copy2(src, dst)

    print("[build] Done. Import with: from chatchat.cpp_ext import lcut_for_search")


if __name__ == "__main__":
    main()
