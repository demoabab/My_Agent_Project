#include "tokenizer.hpp"

#include <fstream>
#include <map>
#include <memory>

namespace cht {

// UTF-8 字符字节数: 首字节高位连续 1 的个数
static std::size_t utf8CharLen(unsigned char c) {
    if ((c & 0xE0) == 0xC0) return 2;
    if ((c & 0xF0) == 0xE0) return 3;
    if ((c & 0xF8) == 0xF0) return 4;
    return 1;
}

// 统计 UTF-8 字符串中的字符数（而非字节数）
static std::size_t utf8CharCount(const std::string& s) {
    std::size_t n = 0;
    for (std::size_t i = 0; i < s.size(); i += utf8CharLen(static_cast<unsigned char>(s[i])))
        ++n;
    return n;
}

// ============================================================
// Trie 节点 — 前缀匹配的核心数据结构
// ============================================================
struct Tokenizer::Trie {
    struct Node {
        bool isWord = false;
        std::map<char, std::unique_ptr<Node>> children;
    };

    Node root;
    std::size_t wordCount = 0;
    std::size_t maxWordLen = 0; // 最长词长度，用于 FMM 剪枝

    void insert(const std::string& word) {
        Node* cur = &root;
        for (char c : word) {
            auto& next = cur->children[c];
            if (!next) {
                next = std::make_unique<Node>();
            }
            cur = next.get();
        }
        cur->isWord = true;
        ++wordCount;
        if (word.size() > maxWordLen) {
            maxWordLen = word.size();
        }
    }

    // 在位置 pos 查找最长匹配词，返回长度（0 = 无匹配）
    std::size_t longestMatch(const std::string& text, std::size_t pos) const {
        const Node* cur = &root;
        std::size_t lastMatch = 0;
        std::size_t remaining = text.size() - pos;
        std::size_t maxLen = maxWordLen < remaining ? maxWordLen : remaining;

        for (std::size_t i = 0; i < maxLen; ++i) {
            auto it = cur->children.find(text[pos + i]);
            if (it == cur->children.end()) {
                break;
            }
            cur = it->second.get();
            if (cur->isWord) {
                lastMatch = i + 1;
            }
        }
        return lastMatch;
    }
};

// ============================================================
// 内嵌最小词典（约 500 常用中文词，确保无文件 IO 也能分词）
// ============================================================
static const char* EMBEDDED_DICT[] = {
    // clang-format off
    "的", "一", "是", "在", "不", "了", "有", "和", "人", "这",
    "中", "大", "为", "上", "个", "国", "我", "以", "要", "他",
    "时", "来", "用", "们", "生", "到", "作", "地", "于", "出",
    "就", "分", "对", "成", "会", "可", "主", "发", "年", "动",
    "同", "能", "也", "下", "过", "子", "说", "产", "种", "面",
    "而", "方", "后", "多", "定", "行", "学", "法", "所", "民",
    "得", "经", "十", "三", "之", "进", "着", "等", "部", "度",
    "家", "电", "力", "里", "如", "水", "化", "高", "自", "二",
    "理", "起", "小", "物", "现", "实", "加", "量", "都", "两",
    "体", "制", "机", "当", "使", "点", "从", "业", "本", "去",
    "把", "性", "应", "开", "它", "合", "还", "因", "由", "其",
    "些", "然", "前", "外", "天", "政", "四", "日", "那", "社",
    "义", "事", "平", "形", "相", "全", "表", "间", "样", "与",
    "关", "各", "重", "新", "线", "内", "数", "正", "心", "反",
    "你", "明", "看", "原", "又", "么", "利", "比", "或", "但",
    "质", "气", "第", "向", "道", "命", "此", "变", "条", "只",
    "没", "结", "解", "问", "意", "建", "月", "公", "无", "系",
    "军", "很", "情", "者", "最", "立", "代", "想", "已", "通",
    "并", "提", "直", "题", "党", "程", "展", "五", "果", "料",
    "象", "员", "革", "位", "入", "常", "文", "总", "次", "品",
    "式", "活", "设", "及", "管", "特", "件", "长", "求", "老",
    "头", "基", "资", "边", "流", "路", "级", "少", "图", "山",
    "统", "接", "知", "较", "将", "组", "见", "计", "别", "她",
    "手", "角", "期", "根", "论", "运", "农", "指", "几", "九",
    "区", "强", "放", "决", "西", "被", "干", "做", "必", "战",
    "先", "回", "则", "任", "取", "据", "处", "队", "南", "给",
    "系统", "技术", "模型", "数据", "检索", "向量", "知识", "文档", "算法",
    "处理", "分析", "文本", "引擎", "分词", "索引", "语言", "编码", "解码",
    "训练", "推理", "嵌入", "维度", "相似", "匹配", "存储", "查询", "优化",
    "加速", "性能", "内存", "缓存", "并行", "调度", "框架", "配置", "部署",
    "服务", "代理", "网络", "接口", "协议", "请求", "响应", "任务", "执行",
    "用户", "管理", "权限", "认证", "授权", "角色", "租户", "会话", "对话",
    "Python", "Cpp", "Java", "Linux", "GPU", "CPU", "API", "HTTP", "JSON",
    "搜索", "召回", "排序", "过滤", "评估", "测试", "监控", "日志", "调试",
    "版本", "分支", "合并", "提交", "发布", "迭代", "重构", "抽象", "封装",
    "工程", "架构", "方案", "设计", "实现", "验证", "集成", "扩展", "维护",
    // 中文通用词
    "可以", "没有", "自己", "什么", "这样", "这个", "问题", "发现", "进行",
    "使用", "已经", "工作", "这些", "可能", "需要", "知道", "起来", "开始",
    "提供", "支持", "一个", "能够", "通过", "包括", "运行", "环境", "开发",
    "工具", "方法", "过程", "功能", "结果", "信息", "内容", "方式", "其他",
    "我们", "他们", "什么", "怎么", "如何", "为什么", "哪里", "这里", "那里",
    "所有", "然后", "虽然", "但是", "因为", "所以", "如果", "而且", "或者",
    "不同", "非常", "比较", "一般", "重要", "当前", "目前", "现在", "正在",
    "继续", "完成", "成功", "失败", "错误", "正确", "有效", "无效", "是否",
    "关于", "作为", "根据", "按照", "对于", "通过", "经过", "经过", "为了",
    "随着", "除了", "并且", "以及", "另外", "首先", "其次", "最后", "然后",
    "希望", "觉得", "认为", "需要", "应该", "必须", "建议", "注意", "保证",
    "表示", "包含", "存在", "考虑", "选择", "设置", "负责", "准备", "执行",
    "显示", "访问", "操作", "检查", "控制", "影响", "决定", "帮助", "提高",
    "减少", "增加", "保持", "改变", "改进", "计算", "更新", "下载", "上传",
    "安装", "启动", "停止", "关闭", "打开", "保存", "删除", "加载", "释放",
    nullptr
};
// clang-format on

// ============================================================
// Tokenizer 实现
// ============================================================

Tokenizer::Tokenizer() : trie_(std::make_unique<Trie>()) {
    // 加载内嵌词典
    for (const char** word = EMBEDDED_DICT; *word; ++word) {
        trie_->insert(*word);
    }
}

Tokenizer::~Tokenizer() = default;
Tokenizer::Tokenizer(Tokenizer&&) noexcept = default;
Tokenizer& Tokenizer::operator=(Tokenizer&&) noexcept = default;

std::size_t Tokenizer::loadDict(const char* path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        return 0;
    }
    std::string line;
    std::size_t count = 0;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#' || line[0] == '\r') {
            continue;
        }
        // jieba dict 格式: word freq pos
        auto space = line.find(' ');
        if (space == std::string::npos) {
            space = line.size();
        }
        trie_->insert(line.substr(0, space));
        ++count;
    }
    return count;
}

std::vector<std::string> Tokenizer::cut(const std::string& text) {
    std::vector<std::string> result;
    result.reserve(text.size() / 2); // 预分配，减少 reallocation

    std::size_t pos = 0;
    while (pos < text.size()) {
        auto len = trie_->longestMatch(text, pos);
        if (len > 0) {
            result.emplace_back(text.substr(pos, len));
            pos += len;
        } else {
            // UTF-8 字符边界: 首字节高位连续的 1 的个数 = 字符字节数
            std::size_t charLen = utf8CharLen(static_cast<unsigned char>(text[pos]));
            result.emplace_back(text.substr(pos, charLen));
            pos += charLen;
        }
    }
    return result;
}

std::vector<std::string> Tokenizer::cutForSearch(const std::string& text) {
    // 先做精确分词
    auto result = cut(text);

    // 对长词（≥2个字符）做二元字切分，提升召回率
    std::vector<std::string> expanded;
    expanded.reserve(result.size() * 2);

    for (auto& word : result) {
        expanded.push_back(word);
        std::size_t charCount = utf8CharCount(word);
        if (charCount >= 3) {
            // 按字符边界滑动 2-char bigrams
            std::size_t pos = 0;
            for (std::size_t ci = 0; ci + 1 < charCount; ++ci) {
                std::size_t c1 = utf8CharLen(static_cast<unsigned char>(word[pos]));
                std::size_t c2 = utf8CharLen(static_cast<unsigned char>(word[pos + c1]));
                expanded.emplace_back(word.substr(pos, c1 + c2));
                pos += c1;
            }
        }
    }
    return expanded;
}

std::size_t Tokenizer::dictSize() const noexcept { return trie_->wordCount; }

} // namespace cht
