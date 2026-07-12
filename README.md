![](docs/img/logo-long-chatchat-trans-v2.png)
<a href="https://trendshift.io/repositories/329" target="_blank"><img src="https://trendshift.io/api/badge/repositories/329" alt="chatchat-space%2FLangchain-Chatchat | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[![pypi badge](https://img.shields.io/pypi/v/langchain-chatchat.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/python-3.8%7C3.9%7C3.10%7C3.11-blue.svg)](https://pypi.org/project/pypiserver/)

🌍 [READ THIS IN ENGLISH](README_en.md)

📃 **LangChain-Chatchat** (原 Langchain-ChatGLM)

基于大语言模型与 Langchain 框架实现的开源、可离线部署的 **RAG + Agent** 应用项目。支持本地知识库问答、Agent 工具调用、多租户隔离、OpenAI 兼容 API。

---

## 目录

* [核心亮点](README.md#核心亮点)
* [架构设计](README.md#架构设计)
* [功能介绍](README.md#功能介绍)
* [多租户系统](README.md#多租户系统)
* [RBAC 权限控制](README.md#rbac-权限控制)
* [前端界面](README.md#前端界面)
* [快速上手](README.md#快速上手)
* [项目里程碑](README.md#项目里程碑)

---

## 核心亮点

### RAG + Agent 融合

| 功能 | 说明 |
|------|------|
| **知识库对话** | 文件 → 文本分割 → 向量化 → 检索 top_k → 上下文注入 LLM |
| **Agent 对话** | 8 种 Agent 类型（GLM3 / Qwen / OpenAI Functions / ReAct / MCP 等），17 个可注册工具 |
| **搜索引擎对话** | 5 种引擎后端（Bing / DuckDuckGo / Metaphor / SearX / 国内 Bing）|
| **文件对话** | 上传文件即时向量化 + FAISS 内存检索 |
| **数据库对话** | Text2SQL 自然语言转 SQL（支持 MySQL / PostgreSQL / ClickHouse 等）|
| **多模态对话** | 图片对话（qwen-vl-chat）、文生图 |
| **深度调研 Skill** | 4 步 mini-Agent：搜索 → 提取 URL → 抓取页面 → LLM 总结报告 |

### 企业级基础设施

| 功能 | 说明 |
|------|------|
| **多租户隔离** | DB 14 张表 + 磁盘路径 + API 全链路 `tenant_id` 传播 |
| **RBAC 权限** | admin / member / viewer 三级角色，细粒度资源-操作权限矩阵 |
| **JWT 认证** | Bearer Token + bcrypt 密码哈希，token 携带 tenant_id claim |
| **OpenAI 兼容** | `/v1/*` 端点完整兼容 OpenAI SDK，智能模型路由与并发控制 |
| **MCP 协议** | 支持 stdio/SSE 两种传输，前端管理界面 + Agent 工具集成 |

### 文档处理

| 功能 | 说明 |
|------|------|
| **OCR 识别** | RapidOCR 引擎（Paddle/ONNX），支持 PDF / DOCX / PPTX / 图片 |
| **中文优化** | 中文字符递归分割器、阿里语义分割模型、标题增强 |
| **混合检索** | Ensemble 检索器（BM25 + 向量搜索，权重可配）|

### 模型生态

- **本地框架**：Xinference / Ollama / LocalAI / FastChat
- **在线 API**：OpenAI / Azure / Anthropic / 智谱 / 百川等
- **模型类型**：LLM + Embedding + Rerank + Text2Image + Vision + Audio

---

## 架构设计

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| API | FastAPI (Python 3.8+) + SSE 流式响应 |
| 数据库 | SQLAlchemy ORM + SQLite（默认）/ PostgreSQL |
| 向量存储 | FAISS（默认）/ Milvus / Zilliz / PGVector / Elasticsearch / ChromaDB |
| 认证 | JWT Bearer Token + bcrypt + contextvars |
| 文档处理 | Langchain + 自研 RapidOCR + jieba 分词 |

### 分层架构

```
┌──────────────────────────────────────┐
│  Vue 3 SPA (frontend/)               │  11 个视图页面
│  Chat / KB / Agent / Tenant / MCP    │  Pinia 状态管理
└──────────────┬───────────────────────┘
               │  HTTP + SSE
┌──────────────▼───────────────────────┐
│  FastAPI (api_server/)               │  8 个路由模块
│  JWT 鉴权 → RBAC 权限 → 租户上下文    │  21 个受保护端点
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│  Business Logic                      │
│  ├─ chat/        (4 种对话模式)       │
│  ├─ knowledge_base/ (KB 管理+向量)    │
│  ├─ agent/       (17 个工具)          │
│  └─ file_rag/    (文档加载+分割+检索)  │
└──────────────┬───────────────────────┘
               │
     ┌─────────┼─────────┬──────────────┐
     ▼         ▼         ▼              ▼
  SQL DB   FAISS    Model API    MCP Servers
  (14表)   (本地)   (Xinference/  (外部工具)
                    Ollama/OpenAI)
```

### 核心设计模式

| 模式 | 应用 |
|------|------|
| **多层多租户** | `tenant_id` 贯穿 ORM → Repository → KBService → 磁盘路径全链路 |
| **contextvars 上下文** | HTTP 请求的 `tenant_id` 自动注入所有 DB 查询和文件操作，线程池安全 |
| **RBAC** | User → Tenant → Role → Permission 四层模型，admin 隐式通过所有检查 |
| **工厂模式** | `KBServiceFactory` 运行时解析 7 种向量存储；模型平台动态路由 |
| **仓库模式** | `@with_session` / `@with_tenant` 装饰器管理 Session 生命周期 |
| **依赖注入** | `Depends(get_current_user)` / `Depends(require_permission(...))` |
| **注册表模式** | `@regist_tool` 装饰器自动注册 Agent 工具，前端动态读取工具列表 |
| **策略模式** | 8 种 Agent 类型 + 5 种搜索引擎 + 7 种向量数据库，运行时切换 |

---

## 功能介绍

### Agent 工具生态（17 个工具）

| 工具 | 功能 | 类型 |
|------|------|------|
| `search_local_knowledgebase` | 搜索本地知识库 | RAG |
| `search_internet` | 互联网搜索（5 种引擎）| 联网 |
| `research_skill` | 深度调研：搜索→抓取→总结 | 编排 |
| `text2sql` | 自然语言转 SQL | 数据库 |
| `text2promql` | 自然语言转 PromQL | 监控 |
| `text2images` | 文生图 | 图像 |
| `url_reader` | 网页内容抓取（r.jina.ai）| 内容 |
| `weather_check` | 心知天气查询 | 生活 |
| `amap_weather` | 高德天气 | 生活 |
| `amap_poi_search` | 高德 POI 搜索 | 地图 |
| `wikipedia_search` | 维基百科 | 知识 |
| `wolfram` | 数学计算/公式 | 学术 |
| `calculate` | 表达式计算（numexpr）| 工具 |
| `arxiv` | 学术论文搜索 | 学术 |
| `search_youtube` | YouTube 视频搜索 | 媒体 |
| `shell` | 系统命令执行 | 系统 |

### Agent 类型（8 种）

| Agent | 适用模型 | 特点 |
|-------|---------|------|
| `openai-functions` | GPT-3.5/4 | OpenAI Function Calling |
| `openai-tools` | GPT-4o | OpenAI 原生 tool_calling |
| `glm3` | ChatGLM3 / GLM-4 | 国产模型优化 |
| `qwen` | Qwen / Qwen2 | 国产模型优化 |
| `structured-chat-agent` | 通用 | ReAct 结构化聊天 |
| `platform-agent` | 通用 | 平台通用 Agent |
| `platform-knowledge-mode` | 通用 | 知识模式 + MCP 工具集成 |
| `default` | 通用 | 基础单次对话 |

### 知识库

- **7 种向量数据库**：FAISS（本地）/ Milvus / Zilliz / PGVector / Elasticsearch / ChromaDB / Relyt
- **Ensemble 检索**：BM25（jieba 分词）+ 向量搜索混合，权重可配
- **多格式支持**：PDF / DOCX / PPTX / XLSX / HTML / CSV / JSON / Markdown / TXT / 图片（OCR）
- **RapidOCR 引擎**：中文 OCR，Paddle / ONNX 双运行时，支持 GPU 加速

### 对话模式

| 模式 | 端点 | 说明 |
|------|------|------|
| **Agent 对话** | `/chat/chat/completions` | LLM + 17 个工具 + MCP 集成 |
| **知识库对话** | `/chat/kb_chat` | local_kb / temp_kb / search_engine 三子模式 |
| **文件对话** | `/chat/file_chat` | 上传文件即时 FAISS 索引 + 问答 |
| **OpenAI 兼容** | `/v1/chat/completions` | 完整 OpenAI SDK 兼容，智能模型路由 |

---

## 多租户系统

### 数据隔离维度

```
租户 A                           租户 B
├── 知识库 (KB1, KB2)            ├── 知识库 (KB3)
├── 对话记录 + 历史               ├── 对话记录 + 历史
├── 上传文件                      ├── 上传文件
├── FAISS 向量索引                ├── FAISS 向量索引
├── MCP 连接配置                  ├── MCP 连接配置
├── Agent 工具配置                ├── Agent 工具配置
└── 成员: user1(admin), user2     └── 成员: user3(admin)
```

### 隔离实现

| 层面 | 实现方式 |
|------|---------|
| **数据库** | 14 张业务表全部携带 `tenant_id`；`@with_tenant` 装饰器从 contextvars 自动注入过滤条件 |
| **API** | JWT token 携带 `tenant_id` claim → `get_current_user()` 验证 → `set_current_tenant_context()` 注入上下文 |
| **磁盘** | 路径函数全链路显式传递 `tenant_id`：`{KB_ROOT}/{tenant_id}/{kb_name}/content/vector_store/` |
| **缓存** | `KBFaissPool.load_vector_store()` 传递 `tenant_id` 到 `get_vs_path()`，不同租户独立 FAISS 索引 |
| **线程安全** | `ThreadPoolExecutor` 自动复制 contextvars 到子线程（Python 3.7+），`run_in_thread_pool` 保持租户上下文 |

### 租户管理

| 端点 | 权限 | 说明 |
|------|------|------|
| `POST /api/v1/tenants` | 登录用户 | 创建租户（创建者自动成为 admin） |
| `GET /api/v1/tenants` | 登录用户 | 获取我的租户列表 |
| `POST /api/v1/tenants/{id}/members` | admin | 添加成员（按用户名查找，含存在性校验） |
| `GET /api/v1/tenants/{id}/members` | admin | 查看成员列表（含用户名 + 角色） |
| `DELETE /api/v1/tenants/{id}/members/{uid}` | admin | 移除成员 |

### 上下文传播链路

```
HTTP 请求 → FastAPI Depends(get_current_user)
  → JWT 解码 (tenant_id claim)
  → set_current_tenant_context(tenant_id, user_id)
  → contextvars 注入
  → KBServiceFactory.get_service(kb_name, tenant_id=...)    (显式)
  → @with_tenant → session.query().filter(tenant_id=...)     (自动)
  → get_kb_path/get_vs_path/get_file_path(kb_name, tenant_id) (显式)
  → 磁盘路径: knowledge_base/{tenant_id}/{kb_name}/
```

---

## RBAC 权限控制

### 权限模型

```
User ──┬── UserTenant (role: admin|member|viewer) ──► Tenant
       │
       └── is_superuser: 绕过所有权限检查
```

| 角色 | knowledge_base | chat | 说明 |
|------|:---:|:---:|------|
| **admin** | read / write / delete | read / write | 隐式所有权限；新租户创建者自动获得 |
| **member** | read / write | read / write | 可管理知识库内容，不可删除 |
| **viewer** | read | read | 只读访问 |

### 受保护端点（21 个）

| 资源 | read | write | delete |
|------|------|-------|--------|
| **knowledge_base** | list_kbs, list_files, search_docs, search_temp_docs, download_doc, kb_chat | create_kb, upload_docs, update_info, update_docs, recreate_vector_store, upload_temp_docs | delete_kb, delete_docs |
| **chat** | kb_chat, file_chat, chat_completions | chat_feedback | — |

### 权限检查流程

```python
# 使用方式：在路由函数签名末尾声明依赖
def delete_kb(
    knowledge_base_name: str = Form(...),
    current_user: dict = Depends(require_permission("knowledge_base", "delete")),
) -> BaseResponse:
    ...

# 内部流程:
# 1. get_current_user() → JWT 验证 → 设置 contextvars
# 2. is_superuser? → 直接通过
# 3. 是否为 tenant admin? → 直接通过
# 4. 查询 PermissionModel 表 → 返回 True/False
```

---

## 前端界面

基于 **Vue 3 + TypeScript + Element Plus + Pinia**，11 个视图页面，生产构建由 FastAPI 直接托管。

### 页面一览

| 页面 | 文件 | 核心功能 |
|------|------|---------|
| **ChatView** | `ChatView.vue` | RAG 知识库聊天：选择知识库、上传文件、检索参数滑块（Top-K / 分数阈值）、聊天模式切换（local_kb / temp_kb / 搜索引擎）、流式 Markdown 渲染、思考过程展示、工具调用状态、参考文档展开 |
| **LlmChatView** | `LlmChatView.vue` | Agent 聊天：17 个工具勾选面板、MCP 模式开关、模型选择器、温度滑块、流式输出（思考→工具调用→回复→参考文档四阶段）|
| **HistoryView** | `HistoryView.vue` | 对话历史：服务器 + 本地持久化、按 kb/llm 标签过滤、消息详情（含文档引用和工具调用）、继续对话导航 |
| **KbListView** | `KbListView.vue` | 知识库管理：表格列表、创建对话框（名称 + FAISS/ChromaDB + 嵌入模型）、删除确认 |
| **KbDetailView** | `KbDetailView.vue` | 知识库详情：多格式文件上传（.txt/.pdf/.md/.docx/.pptx/.xlsx/.html/.csv/.json）、文档搜索、文件下载/删除、向量库重建 |
| **LoginView** | `LoginView.vue` | 登录：品牌 Logo、深色渐变背景、JWT 认证 |
| **RegisterView** | `RegisterView.vue` | 注册：用户名/密码/邮箱/姓名、表单验证 |
| **TenantListView** | `TenantListView.vue` | 租户管理：列表含角色标签（admin/member/viewer）、创建租户 |
| **TenantDetailView** | `TenantDetailView.vue` | 租户详情：成员添加（按用户名检索，含存在性校验）、成员列表（用户名 + 角色）、移除成员 |
| **UserListView** | `UserListView.vue` | 用户管理（仅超管）：用户表、启用/禁用切换 |
| **McpConfigView** | `McpConfigView.vue` | MCP 连接：创建/编辑/删除/测试连接、stdio/SSE 传输、命令参数、超时配置 |

### 全局组件

| 组件 | 功能 |
|------|------|
| **AppLayout** | 主布局：侧边栏导航、顶部栏显示 `username@tenant_name` + 角色标签、租户切换下拉菜单 |
| **MessageBubble** | 聊天消息气泡：思考/工具调用/回复/参考文档四阶段流式渲染 |
| **TenantSwitcher** | 租户切换器：调用 `/auth/switch-tenant` 获取新 JWT |
| **KbFileTree** | 知识库文件树浏览器 |

### 技术特性

- **SSE 流式渲染**：自定义 `useChat` composable，手写 SSE 解析器处理 `data:` 帧
- **Pinia 状态管理**：auth / settings / tenant 三个 store
- **Axios 拦截器**：自动附加 `Authorization: Bearer <token>`，401 自动跳转登录
- **Markdown 渲染**：`marked` + `highlight.js`，支持代码高亮

---

## 快速上手

### pip 安装

```shell
pip install langchain-chatchat -U
# 如需 Xinference:
pip install "langchain-chatchat[xinference]" -U
```

### 1. 启动模型服务

请先部署模型推理框架（Xinference / Ollama / OneAPI 等）并加载 LLM + Embedding 模型。

> 建议 Langchain-Chatchat 与模型框架使用不同虚拟环境。

### 2. 初始化配置

```shell
# 可选：设置数据根目录
export CHATCHAT_ROOT=/path/to/chatchat_data   # Linux/macOS
set CHATCHAT_ROOT=/path/to/chatchat_data      # Windows

chatchat init   # 创建目录 + 复制 samples + 生成 yaml
```

修改配置文件：

```yaml
# model_settings.yaml
DEFAULT_LLM_MODEL: qwen1.5-chat
DEFAULT_EMBEDDING_MODEL: bge-large-zh-v1.5
# 在 MODEL_PLATFORMS 中填入平台连接信息

# basic_settings.yaml
KB_ROOT_PATH: /path/to/knowledge_base
JWT_SECRET_KEY: your-secret-key
```

### 3. 初始化知识库

```shell
chatchat kb -r
```

### 4. 启动

```shell
chatchat start -a
```

访问 `http://127.0.0.1:7861`，前端界面在 `/app/`。

> 需外部 IP 访问时，修改 `basic_settings.yaml` 中 `DEFAULT_BIND_HOST` 为 `0.0.0.0`。

### 源码开发

参考 [开发指南](docs/contributing/README_dev.md)

### Docker

```shell
docker pull chatimage/chatchat:0.3.1.3-93e2c87-20240829
```

> 推荐 docker-compose，参见 [README_docker](docs/install/README_docker.md)

---

## 项目里程碑

+ `2023年4月`: **0.1.0** — `Langchain-ChatGLM` 发布，ChatGLM-6B 本地知识库问答
+ `2023年8月`: **0.2.0** — 改名 `Langchain-Chatchat`，fastchat 模型加载
+ `2023年10月`: **0.2.5** — Agent 功能，黑客马拉松三等奖
+ `2023年12月`: 开源项目突破 **20K** stars
+ `2024年6月`: **0.3.0** — 全新架构，模型平台抽象，多 Agent 类型
+ `2024年7月`: **0.3.1** — Vue 3 前端 + 多租户隔离 + RBAC 权限 + MCP 协议 + 17 个 Agent 工具 + 5 种搜索引擎 + 7 种向量数据库

---

## 协议

本项目代码遵循 [Apache-2.0](LICENSE) 协议。

## 联系我们

### Telegram

[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white "langchain-chatchat")](https://t.me/+RjliQ3jnJ1YyN2E9)

### 项目交流群

<img src="docs/img/qr_code_117_2.jpg" alt="二维码" width="300" />

### 公众号

<img src="docs/img/official_wechat_mp_account.png" alt="二维码" width="300" />

## 引用

```
@software{langchain_chatchat,
    title        = {{langchain-chatchat}},
    author       = {Liu, Qian and Song, Jinke, and Huang, Zhiguo, and Zhang, Yuxuan, and glide-the, and liunux4odoo},
    year         = 2024,
    journal      = {GitHub repository},
    publisher    = {GitHub},
    howpublished = {\url{https://github.com/chatchat-space/Langchain-Chatchat}}
}
```
