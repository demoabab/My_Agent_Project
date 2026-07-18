cmake_minimum_required(VERSION 3.18)
project(chatchat_tokenizer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(pybind11 REQUIRED)

# SIMD optimization flags
if(MSVC)
    add_compile_options(/arch:AVX2 /O2 /GL)
    add_link_options(/LTCG)
else()
    add_compile_options(-O3 -march=native)
endif()

pybind11_add_module(_tokenizer SHARED
    tokenizer.cpp
    bindings.cpp
)

target_include_directories(_tokenizer PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(_tokenizer PRIVATE CHT_BUILDING)
