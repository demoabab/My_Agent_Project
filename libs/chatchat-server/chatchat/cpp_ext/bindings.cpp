#include <pybind11/pybind11.h>

#include "tokenizer.hpp"

namespace py = pybind11;

namespace {

py::str to_pystr(const std::string& s) {
    return py::str(s.c_str(), s.size());
}

py::list to_pylist(const std::vector<std::string>& v) {
    py::list lst(v.size());
    for (std::size_t i = 0; i < v.size(); ++i) {
        lst[i] = to_pystr(v[i]);
    }
    return lst;
}

} // namespace

PYBIND11_MODULE(_tokenizer, m) {
    m.doc() = "C++ Chinese tokenizer — Trie/FMM with SIMD-ready layout";

    py::class_<cht::Tokenizer>(m, "Tokenizer")
        .def(py::init<>())
        .def("load_dict",
             &cht::Tokenizer::loadDict,
             py::arg("path"),
             "Load external dictionary file (jieba dict.txt format)")
        .def("cut",
             [](cht::Tokenizer& t, const char* text) {
                 std::string input(text);  // 复制 — 释放 GIL 前需要安全拷贝
                 std::vector<std::string> result;
                 {
                     py::gil_scoped_release release;
                     result = t.cut(input);
                 }
                 return to_pylist(result);
             },
             py::arg("text"),
             "Exact mode segmentation")
        .def("lcut",
             [](cht::Tokenizer& t, const char* text) {
                 std::string input(text);
                 std::vector<std::string> result;
                 {
                     py::gil_scoped_release release;
                     result = t.cut(input);
                 }
                 return to_pylist(result);
             },
             py::arg("text"),
             "Exact mode, returns list (alias for cut)")
        .def("cut_for_search",
             [](cht::Tokenizer& t, const char* text) {
                 std::string input(text);
                 std::vector<std::string> result;
                 {
                     py::gil_scoped_release release;
                     result = t.cutForSearch(input);
                 }
                 return to_pylist(result);
             },
             py::arg("text"),
             "Search mode - adds 2-char subwords from long tokens")
        .def("lcut_for_search",
             [](cht::Tokenizer& t, const char* text) {
                 std::string input(text);
                 std::vector<std::string> result;
                 {
                     py::gil_scoped_release release;
                     result = t.cutForSearch(input);
                 }
                 return to_pylist(result);
             },
             py::arg("text"),
             "Search mode, returns list (alias for cut_for_search)")
        .def_property_readonly("dict_size",
                               &cht::Tokenizer::dictSize,
                               "Number of words in dictionary");

    m.attr("__version__") = "0.1.0";
    m.attr("__author__") = "chatchat";
}
