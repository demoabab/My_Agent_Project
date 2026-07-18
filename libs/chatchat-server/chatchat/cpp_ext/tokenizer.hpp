#pragma once
#include <cstddef>
#include <memory>
#include <string>
#include <vector>

namespace cht {

// ============================================================
// Public API — 与 jieba 完全兼容的接口
// ============================================================
class Tokenizer {
public:
    Tokenizer();
    ~Tokenizer();
    Tokenizer(Tokenizer&&) noexcept;
    Tokenizer& operator=(Tokenizer&&) noexcept;

    // 不可拷贝
    Tokenizer(const Tokenizer&) = delete;
    Tokenizer& operator=(const Tokenizer&) = delete;

    // 加载外部词典文件（jieba dict.txt 格式: word freq pos）
    // 返回加载的词条数
    std::size_t loadDict(const char* path);

    // 分词（精确模式），等价于 jieba.cut(text)
    std::vector<std::string> cut(const std::string& text);

    // 搜索引擎模式分词，等价于 jieba.cut_for_search(text)
    // 在精确模式基础上对长词做二元切分
    std::vector<std::string> cutForSearch(const std::string& text);

    // 返回当前词典大小
    std::size_t dictSize() const noexcept;

private:
    struct Trie;
    std::unique_ptr<Trie> trie_;
};

} // namespace cht
