# LangChain Chat — 架构设计文档

> 面向开发者的架构设计说明，含分层设计、数据流、可插拔存储、多服务商配置、审计结果、扩展预留。

## 一、五层分层架构

```
┌─────────────────────────────────────────┐
│  UI 实现层（ui/tui/）                    │  负责界面渲染、用户交互
├─────────────────────────────────────────┤
│  UI 接口层（interface/ui_protocol.py）    │  定义 UI 必须遵守的契约（AbstractUI）
├─────────────────────────────────────────┤
│  核心业务层（core/）                      │  业务逻辑（对话引擎、会话管理、用户管理等）
├─────────────────────────────────────────┤
│  数据模型层（models/schemas.py）          │  Pydantic 数据模型（User/Session/Message 等）
├─────────────────────────────────────────┤
│  存储层（storage/）                       │  数据持久化（SQLite/MySQL/File 可插拔）
└─────────────────────────────────────────┘
```

**依赖规则**：上层依赖下层，下层不依赖上层。UI 不碰 storage，core 不碰 UI。

## 二、可插拔存储设计

```
StorageBackend（抽象基类，21 个方法）
    ├── SQLiteBackend ── aiosqlite ── app.db
    ├── MySQLBackend  ── aiomysql  ── MySQL Server
    └── FileBackend   ── json     ── *.json 文件
```

切换方式：修改 `config.yaml` 的 `storage.type` 即可，无需改任何代码。

## 三、多服务商模型配置

```
providers:
  通义千问 ── QWEN_API_KEY ── qwen3.6-flash / deepseek-v4-pro（代理）
  DeepSeek ── DEEPSEEK_API_KEY ── deepseek-v4-pro / deepseek-v4-flash
  OpenAI代理 ── OPENAI_API_KEY ── free-gpt-3.5-turbo
```

安全设计：config.yaml 只写 `api_key_env` 变量名，真实 Key 存 .env。

## 四、对话数据流

```
用户输入 → chat_view（HumanMessage）
    → ChatEngine.astream（调用 LLM）
    → 流式渲染（逐 chunk 显示）
    → 回复 → AIMessage
    → SessionManager.add_message（持久化到数据库）
    → 下一轮对话时带完整历史
```

## 五、架构审计结果

审计时间：2026-07-10。覆盖全部源文件。

| 检查项 | 结果 |
|--------|------|
| 分层穿透 | ✅ 无穿透（chat_view 不再直接访问 backend） |
| UI 层 import storage | ✅ 已修复（移除 app.py 中 StorageFactory import） |
| 反向依赖 | ✅ core/models 不依赖 UI |
| 接口一致性 | ✅ base.py 21 个抽象方法，三个后端全部实现 |

## 六、扩展预留（需求 H2~H5）

### H1: WebUI 接口（已有 AbstractUI）
TUIApp 继承 AbstractUI。WebUI 只需实现另一个 AbstractUI 子类，所有业务层代码可直接复用。

### H2: 多模型并行对比
将单次 LLM 调用扩展为并发调用多个模型，结果对比展示。ChatEngine 的 switch_model 已为跨服务商调用提供基础。

### H3: 图文上传
在 chat_view 增加图片/文件输入，ChatEngine 扩展接收多模态消息。

### H4: 语音输入/输出
利用语音转文字 API（输入）+ TTS（输出）集成。

### H5: 工具调用（Tool Calling）
利用 LangChain 的 Tool/Agent 体系扩展。消息类型已为 tool 角色预留扩展空间。
