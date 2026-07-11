![](docs/img/logo-long-chatchat-trans-v2.png)
<a href="https://trendshift.io/repositories/329" target="_blank"><img src="https://trendshift.io/api/badge/repositories/329" alt="chatchat-space%2FLangchain-Chatchat | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[![pypi badge](https://img.shields.io/pypi/v/langchain-chatchat.svg)](https://shields.io/)
[![Generic badge](https://img.shields.io/badge/python-3.8%7C3.9%7C3.10%7C3.11-blue.svg)](https://pypi.org/project/pypiserver/)

🌍 [READ THIS IN ENGLISH](README_en.md)

📃 **LangChain-Chatchat** (原 Langchain-ChatGLM)

基于 ChatGLM 等大语言模型与 Langchain 等应用框架实现，开源、可离线部署的 RAG 与 Agent 应用项目。

---

## 目录

* [概述](README.md#概述)
* [架构设计](README.md#架构设计)
* [功能介绍](README.md#功能介绍)
* [多租户系统](README.md#多租户系统)
* [RBAC 权限控制](README.md#rbac-权限控制)
* [快速上手](README.md#快速上手)
* [项目里程碑](README.md#项目里程碑)
* [联系我们](README.md#联系我们)

---

## 概述

🤖️ 一种利用 [langchain](https://github.com/langchain-ai/langchain) 思想实现的基于本地知识库的问答应用，目标期望建立一套对中文场景与开源模型支持友好、可离线运行的知识库问答解决方案。

✅ 本项目支持市面上主流的开源 LLM、Embedding 模型与向量数据库，可实现全部使用**开源**模型**离线私有部署**。同时也支持 OpenAI API 及各类在线模型 API 的接入。

⛓️ 实现原理：加载文件 → 读取文本 → 文本分割 → 向量化 → 相似度检索 top_k → 上下文 + 问题 → prompt → LLM 生成回答。

![实现原理图](docs/img/langchain+chatglm.png)

---

## 架构设计

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| API 服务 | FastAPI (Python 3.8+) |
| 数据库 | SQLAlchemy ORM + SQLite/PostgreSQL |
| 向量存储 | FAISS / Milvus / Zilliz / PGVector / Elasticsearch / ChromaDB |
| 模型接入 | Xinference / Ollama / OneAPI / OpenAI 兼容协议 |
| 认证 | JWT Bearer Token + bcrypt |
| 文档处理 | Langchain Document Loaders + 自研 OCR (RapidOCR) |

### 分层架构

```
Vue 3 SPA (frontend/)
       │
       ▼
FastAPI (api_server/)        ← JWT 鉴权 + RBAC 权限中间件
       │
       ▼
Business Logic               ← chat/ knowledge_base/ agent/
       │
       ├── Repository Layer  ← SQLAlchemy ORM + 租户隔离过滤
       │
       ├── Vector Stores     ← FAISS / Milvus / ChromaDB / ES / PG
       │
       └── Model Platforms   ← Xinference / Ollama / OpenAI / OneAPI
```

### 核心设计模式

| 模式 | 应用场景 |
|------|---------|
| **多层多租户** | tenant_id 贯穿 DB 模型 → API → 磁盘路径全链路 |
| **contextvars 上下文传播** | HTTP 请求的 tenant_id 自动注入所有 DB 查询和文件操作 |
| **RBAC 权限** | user → tenant → role → permission 四层模型，admin 隐式通过 |
| **工厂模式** | KBServiceFactory 运行时解析向量存储类型 |
| **仓库模式** | Session 生命周期与业务逻辑分离，`@with_session` 装饰器管理 |
| **依赖注入** | FastAPI `Depends(get_current_user)` / `Depends(require_permission(...))` |

### 项目结构

```
Langchain-Chatchat/
├── libs/chatchat-server/chatchat/
│   ├── server/
│   │   ├── api_server/          # FastAPI 路由层 (10 个模块)
│   │   │   ├── auth_routes.py       # 认证: login/register/switch-tenant
│   │   │   ├── tenant_routes.py     # 租户管理: CRUD + 成员管理
│   │   │   ├── kb_routes.py         # 知识库: 文件/向量/搜索/对话
│   │   │   ├── chat_routes.py       # 对话: kb_chat/file_chat/feedback
│   │   │   ├── openai_routes.py     # OpenAI 兼容 /v1/* 端点
│   │   │   ├── mcp_routes.py        # MCP 连接管理
│   │   │   ├── server_routes.py     # 模型列表/配置
│   │   │   └── tool_routes.py       # 工具调用
│   │   ├── auth/                # JWT + RBAC (dependencies.py)
│   │   ├── db/                  # SQLAlchemy ORM
│   │   │   ├── models/              # 14 个数据模型 (全带 tenant_id)
│   │   │   ├── repository/          # 仓库模式 CRUD
│   │   │   ├── session.py           # with_session / with_tenant 装饰器
│   │   │   └── migrations/          # Alembic 迁移脚本
│   │   ├── chat/                # kb_chat / file_chat / feedback
│   │   ├── knowledge_base/      # KB 服务 + 文件处理 + 向量缓存 + 摘要
│   │   ├── agent/               # Agent 工具工厂
│   │   ├── file_rag/            # 文档加载器 + 文本分割器 + 检索器
│   │   └── context.py           # contextvars 租户上下文
│   ├── frontend/                # Vue 3 源码
│   ├── static/frontend/         # 前端构建产物 (生产环境)
│   └── settings.py              # Pydantic 配置聚合 (5 类)
└── chatchat_data/               # 运行时数据 (YAML 配置 + KB + DB)
```

---

## 功能介绍

### 0.3.x 版本功能一览

| 功能 | 0.2.x | 0.3.x |
|------|-------|-------|
| 模型接入 | 本地：fastchat / 在线：XXXModelWorker | model_provider 统一接入，兼容 OpenAI SDK |
| Agent | ❌不稳定 | ✅ 针对 ChatGLM3/Qwen 优化 |
| LLM 对话 | ✅ | ✅ |
| 知识库对话 | ✅ | ✅ |
| 搜索引擎对话 | ✅ | ✅ |
| 文件对话 | ✅ 仅向量检索 | ✅ File RAG: BM25+KNN 等多检索方式 |
| 数据库对话 | ❌ | ✅ |
| 多模态图片对话 | ❌ | ✅ (qwen-vl-chat) |
| ARXIV 文献对话 | ❌ | ✅ |
| Wolfram 对话 | ❌ | ✅ |
| 文生图 | ❌ | ✅ |
| 多租户 | ❌ | ✅ 租户隔离 + RBAC 权限 |
| 本地知识库管理 | ✅ | ✅ |
| WEBUI | ✅ Streamlit | ✅ Vue 3 SPA (更好的多会话+自定义提示词) |

### Agent 工具调用

| 操作方式 | 功能 | 适用场景 |
|---------|------|---------|
| 启用 Agent + 多工具 | LLM 自动工具选择调用 | ChatGLM3/Qwen 等具备 Agent 能力的模型 |
| 启用 Agent + 单工具 | LLM 仅解析参数 | Agent 能力一般的模型 |
| 不启用 Agent + 单工具 | 手动调参 | 不具备 Agent 能力的模型 |

### 支持的模型部署框架

| 框架 | Xinference | LocalAI | Ollama | FastChat |
|------|-----------|---------|--------|----------|
| OpenAI API 对齐 | ✅ | ✅ | ✅ | ✅ |
| 推理引擎 | GPTQ, GGML, vLLM, TensorRT, mlx | GPTQ, GGML, vLLM, TensorRT | GGUF, GGML | vLLM |
| 模型类型 | LLM, Embedding, Rerank, T2I, Vision, Audio | 同上 | LLM, T2I, Vision | LLM, Vision |
| Function Call | ✅ | ✅ | ✅ | / |

在线 API 支持：OpenAI ChatGPT / Azure OpenAI / Anthropic Claude / 智谱清言 / 百川等。

---

## 多租户系统

### 概述

从 0.3.1 起，Langchain-Chatchat 支持完整的多租户数据隔离。每个用户可以创建或加入多个租户（Tenant），同一租户内的用户共享知识库、对话记录等资源，不同租户之间的数据完全隔离。

### 数据隔离维度

```
租户 A                         租户 B
├── 知识库 (KB1, KB2)          ├── 知识库 (KB3)
├── 对话记录                     ├── 对话记录
├── 上传文件                     ├── 上传文件
├── 向量缓存 (FAISS)             ├── 向量缓存 (FAISS)
├── 磁盘路径: /{tenant_a}/...    ├── 磁盘路径: /{tenant_b}/...
└── 成员: user1(admin), user2   └── 成员: user3(admin)
```

### 隔离实现

| 层面 | 实现方式 |
|------|---------|
| **数据库** | 14 个业务表全部携带 `tenant_id` 列，仓库层 `@with_tenant` 装饰器自动过滤 |
| **API** | JWT token 携带 tenant_id → `set_current_tenant_context()` 注入 contextvars |
| **磁盘** | `get_kb_path/get_vs_path/get_file_path` 全部传递 tenant_id，目录结构 `{KB_ROOT}/{tenant_id}/{kb_name}/` |
| **缓存** | FAISS 向量库加载/保存路径纳入 tenant_id，不同租户独立索引文件 |

### 租户管理 API

| 端点 | 权限 | 说明 |
|------|------|------|
| `POST /api/v1/tenants` | 登录用户 | 创建租户（创建者自动成为 admin） |
| `GET /api/v1/tenants` | 登录用户 | 获取用户所属租户列表 |
| `POST /api/v1/tenants/{id}/members` | admin | 添加成员（按用户名查找+校验存在性） |
| `GET /api/v1/tenants/{id}/members` | admin | 查看成员列表（含用户名和角色） |
| `DELETE /api/v1/tenants/{id}/members/{user_id}` | admin | 移除成员 |

### 租户切换

用户登录后通过顶部栏下拉菜单切换当前活跃租户。切换后：
1. 前端调用 `/api/v1/auth/switch-tenant` 获取新 JWT token
2. 新 token 的 `tenant_id` claim 指向目标租户
3. 后续所有 API 请求自动绑定新租户上下文

### 知识库路径结构

```
{KB_ROOT_PATH}/
├── {tenant_id_a}/
│   ├── kb_alpha/
│   │   ├── content/          ← 上传的原始文件
│   │   └── vector_store/     ← FAISS 向量索引
│   └── kb_beta/
│       ├── content/
│       └── vector_store/
├── {tenant_id_b}/
│   └── kb_gamma/
│       ├── content/
│       └── vector_store/
└── info.db                   ← SQLite 元数据库
```

---

## RBAC 权限控制

### 权限模型

```
User ──┬── UserTenant (role) ──► Tenant
       │
       └── is_superuser: 绕过所有权限检查
```

| 角色 | knowledge_base | chat | 说明 |
|------|:---:|:---:|------|
| **admin** | read / write / delete | read / write | 隐式拥有所有权限 |
| **member** | read / write | read / write | 可管理知识库，不可删除 |
| **viewer** | read | read | 只读访问 |

### 权限检查机制

```python
# 依赖注入模式：在路由函数签名末尾声明
def create_kb(
    ...,
    current_user: dict = Depends(require_permission("knowledge_base", "write")),
) -> BaseResponse:
    ...

# require_permission 内部流程:
# 1. 调用 get_current_user() 验证 JWT → 设置 contextvars
# 2. 检查 is_superuser → 直接通过
# 3. 检查是否为 tenant admin → 直接通过
# 4. 查询 PermissionModel 表验证 role 权限
```

### 受保护的端点

所有核心业务端点（21 个）均已挂载鉴权依赖：

| 资源 | read (get_current_user) | write (require_permission) | delete (require_permission) |
|------|------------------------|---------------------------|----------------------------|
| **knowledge_base** | list_kbs, list_files, search_docs, download_doc, kb_chat | create_kb, upload_docs, update_docs, recreate_vector_store | delete_kb, delete_docs |
| **chat** | kb_chat, file_chat, chat_completions | chat_feedback | — |

### 无 token 请求行为

未携带有效 JWT 的请求 → **401 Unauthorized**；权限不足 → **403 Forbidden**。

---

## 快速上手

### pip 安装部署

#### 0. 软硬件要求

💡 软件：Python 3.8-3.11，Windows / macOS / Linux 均已测试。

💻 硬件：支持 CPU / GPU / NPU / MPS 等多种硬件条件。

#### 1. 安装

```shell
pip install langchain-chatchat -U

# 如需搭配 Xinference:
pip install "langchain-chatchat[xinference]" -U
```

#### 2. 启动模型推理框架

请先部署模型推理框架（Xinference / Ollama / OneAPI 等）并加载所需 LLM 和 Embedding 模型。

> 建议将 Langchain-Chatchat 和模型框架放在不同的 Python 虚拟环境中。

#### 3. 初始化配置

```shell
# 可选：设置数据根目录
# Linux/macOS:
export CHATCHAT_ROOT=/path/to/chatchat_data
# Windows:
set CHATCHAT_ROOT=/path/to/chatchat_data

# 初始化（创建目录、复制 samples、生成 yaml 配置）
chatchat init
```

修改生成的配置文件：

- `model_settings.yaml` — 配置模型平台和默认 LLM/Embedding
- `basic_settings.yaml` — 配置知识库路径、数据库 URI、JWT 密钥

```yaml
# model_settings.yaml 核心修改:
DEFAULT_LLM_MODEL: qwen1.5-chat
DEFAULT_EMBEDDING_MODEL: bge-large-zh-v1.5
# 在 MODEL_PLATFORMS 中填入模型平台连接信息

# basic_settings.yaml:
KB_ROOT_PATH: /path/to/knowledge_base
SQLALCHEMY_DATABASE_URI: sqlite:////path/to/info.db
JWT_SECRET_KEY: your-secret-key
```

#### 4. 初始化知识库

```shell
chatchat kb -r
```

出现文件计数和用时即为成功。

#### 5. 启动

```shell
chatchat start -a
```

默认监听 `http://127.0.0.1:7861`，前端界面位于 `/app/`。

> 如需外部访问，修改 `basic_settings.yaml` 中 `DEFAULT_BIND_HOST` 为 `0.0.0.0`。

### 源码安装部署/开发部署

参考 [开发指南](docs/contributing/README_dev.md)

### Docker 部署

```shell
docker pull chatimage/chatchat:0.3.1.3-93e2c87-20240829
```

> 推荐使用 docker-compose，参考 [README_docker](docs/install/README_docker.md)

---

## 项目里程碑

+ `2023年4月`: `Langchain-ChatGLM 0.1.0` 发布，支持 ChatGLM-6B 本地知识库问答。
+ `2023年8月`: 改名 `Langchain-Chatchat`，`0.2.0` 发布，fastchat 模型加载，更多模型和数据库。
+ `2023年10月`: `0.2.5` 发布，Agent 功能，黑客马拉松三等奖。
+ `2023年12月`: 开源项目获得超过 **20K** stars。
+ `2024年6月`: `0.3.0` 发布，全新项目架构。
+ `2024年7月`: `0.3.1` 发布，Vue 3 前端 + 多租户隔离 + RBAC 权限系统。

+ 🔥 让我们一起期待未来 Chatchat 的故事 ···

---

## 协议

本项目代码遵循 [Apache-2.0](LICENSE) 协议。

## 联系我们

### Telegram

[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white "langchain-chatchat")](https://t.me/+RjliQ3jnJ1YyN2E9)

### 项目交流群

<img src="docs/img/qr_code_117_2.jpg" alt="二维码" width="300" />

🎉 Langchain-Chatchat 项目微信交流群，欢迎加入群聊参与讨论交流。

### 公众号

<img src="docs/img/official_wechat_mp_account.png" alt="二维码" width="300" />

🎉 Langchain-Chatchat 项目官方公众号，欢迎扫码关注。

## 引用

如果本项目有帮助到您的研究，请引用我们：

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
