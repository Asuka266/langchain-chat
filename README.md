# LangChain Chat

> 基于 LangChain 的多轮会话系统（教学项目）

从零开始，按 14 个步骤搭建的 Python 企业级 AI 对话终端应用。支持多轮对话、用户管理、预设角色、可插拔存储、多服务商模型切换、对话搜索与导出。

## 项目特性

- **多轮对话**：基于 LangChain Memory 机制 + 流式逐 token 输出
- **用户隔离**：多用户独立，数据互不可见
- **预设系统**：5 个内置角色 + 用户自定义预设
- **可插拔存储**：SQLite / MySQL / File 三种后端，配置一键切换
- **多服务商模型**：通义千问 / DeepSeek / OpenAI，支持跨服务商切换
- **对话搜索**：关键词搜索历史消息，按会话分组展示
- **导出 Markdown**：一键导出会话为 Markdown 文件
- **全链路异步**：LLM 调用、IO、数据库全部 async/await
- **分层架构**：五层解耦（UI → Interface → Core → Models → Storage）
- **单元测试**：35 个 pytest 用例
- **教学导向**：每步 Git tag 可回退，含完整教学文档

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| LLM 框架 | LangChain + langchain-openai |
| 异步数据库 | aiosqlite / aiomysql |
| TUI 终端 | Rich + prompt_toolkit |
| 配置管理 | PyYAML + python-dotenv + pydantic |
| 包管理 | uv |
| 测试 | pytest + pytest-asyncio + pytest-cov |
| 代码质量 | ruff |

## 快速开始

### 1. 环境要求

- Python 3.12（>=3.10,<3.13）
- uv 包管理器

### 2. 安装与配置

```bash
git clone <仓库地址>
cd langchain-chat
cp .env.example .env
# 编辑 .env，填入至少一个服务商的 API Key
uv sync
```

### 3. 运行

```bash
uv run python src/main.py
```

## 使用说明

### 主菜单

| 序号 | 功能 |
|------|------|
| 1 | 用户管理（创建/列出/切换/删除） |
| 2 | 会话管理（列表/加载/重命名/删除/记录/导出） |
| 3 | 预设管理（查看内置/新增/编辑/删除自定义） |
| 4 | 开始对话（多轮流式，选预设） |
| 5 | 搜索对话（关键词搜索历史） |
| 6 | 设置（查看/切换模型） |

### 对话命令

| 命令 | 功能 |
|------|------|
| `/help` | 显示帮助 |
| `/exit` | 退出对话 |
| `/new` | 新建会话 |
| `/rename 标题` | 修改会话标题 |
| `/model` | 查看当前/可选模型 |
| `/model 模型名` | 切换模型（保留上下文） |

### 运行测试

```bash
uv run pytest -v
```

## 配置说明

### 三层配置

| 层 | 文件 | 内容 |
|----|------|------|
| 敏感 | `.env` | API Key、密码 |
| 业务 | `config.yaml` | 服务商、存储、生成参数 |
| 日志 | `config/logging.yaml` | 日志格式与级别 |

### 增加模型/服务商

编辑 `config.yaml` 的 `providers` 段，新增服务商需同步在 `.env` 添加对应 Key。

### 切换存储

修改 `config.yaml` 的 `storage.type`：`sqlite` / `mysql` / `file`。

## 开发步骤

| Tag | 内容 |
|-----|------|
| `step-1-init` | 项目初始化与工程化配置 |
| `step-2-skeleton` | 数据模型 + 存储接口 + TUI 骨架 |
| `step-3-sqlite` | SQLite 存储后端 + 数据库初始化 |
| `step-4-user-mgmt` | 用户管理 + TUI 菜单 |
| `step-5-presets` | 预设管理 + 内置导入 |
| `step-6-chat-engine` | 对话引擎（LLM + 流式 + Token） |
| `step-7-first-chat` | 核心里程碑：多轮流式对话 |
| `step-8-session-mgmt` | 会话管理完善 + 分层修复 |
| `step-9-search` | 对话搜索 + 会话记录查看 |
| `step-10-export-switch` | 导出 Markdown + 多服务商切换 + 设置菜单 |
| `step-11-mysql` | MySQL 存储后端 |
| `step-12-logging-file` | File 后端 + 日志系统 |
| `step-13-tests` | 单元测试（35 个用例） |
| `step-14-docs-extend` | README + 架构文档 + 审计 |

## 文档

- [需求说明文档](docs/需求说明文档.md)
- [实施步骤计划](docs/实施步骤计划.md)
- [需求变更与扩展登记](docs/需求变更与扩展登记.md)
- [Git 命令与操作教学](docs/Git命令与操作教学.md)
- [uv 包管理器教学文档](docs/uv包管理器教学文档.md)
- [架构设计文档](docs/architecture.md)
