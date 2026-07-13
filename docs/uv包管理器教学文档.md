# uv 包管理器教学文档

> **版本**：v1.1  
> **日期**：2026-07-10  
> **适用场景**：Python 项目开发，现代包管理与环境管理  
> **配套项目**：langchain-chat（LangChain 多轮会话项目）

---

## 目录

- [一、uv 是什么](#一uv-是什么)
- [二、为什么要用 uv](#二为什么要用-uv)
- [三、为什么选 uv](#三为什么选-uv)
- [四、安装 uv](#四安装-uv)
- [五、uv 环境变量管理（完整版）](#五uv-环境变量管理完整版)
- [六、用 uv 管理 Python 版本](#六用-uv-管理-python-版本)
- [七、用 uv 管理虚拟环境](#七用-uv-管理虚拟环境)
- [八、用 uv 管理依赖](#八用-uv-管理依赖)
- [九、用 uv 运行项目](#九用-uv-运行项目)
- [十、uv 与系统 Python / Anaconda 的关系](#十uv-与系统-python--anaconda-的关系)
- [十一、完整工作流程示例](#十一完整工作流程示例)
- [附录：命令速查表](#附录命令速查表)

---

## 一、uv 是什么

### 定义

**uv** 是由 **Astral 公司**（一个专注于 Python 工具链的公司）开发的现代化 Python 包管理器，使用 **Rust 语言**编写。

### 核心能力

uv 一个工具整合了传统 Python 开发中多个工具的功能：

| 传统工具组合 | uv 的对应能力 |
|-------------|--------------|
| `pip`（安装包） | `uv add` / `uv pip` |
| `venv`（创建虚拟环境） | `uv venv`（自动创建） |
| `pip-tools`（依赖锁定） | `uv lock`（自动生成 uv.lock） |
| `pyenv`（管理多版本 Python） | `uv python install` |
| `virtualenv`（更快的环境创建） | 内置，比 virtualenv 快很多 |
| `poetry`（项目管理） | `uv init` / `uv add` / `uv sync` |

### 一句话理解

> uv 是一个 **"一个工具搞定 Python 一切环境问题"** 的现代化工具，用 Rust 写的所以极快。

---

## 二、为什么要用 uv

### 传统 Python 环境管理的痛点

#### 痛点 1：工具繁多，需要组合使用

传统方式下，你需要：

```
pyenv      → 管理多个 Python 版本
venv       → 创建虚拟环境
pip        → 安装包
pip-tools  → 锁定依赖版本
poetry     → 项目管理
```

每个工具都要单独学、单独装，组合使用时还容易出问题。

#### 痛点 2：速度慢

传统的 `pip install` 在大型项目中可能很慢（解析依赖、下载、安装）。

#### 痛点 3：环境混乱

- 全局环境 vs 虚拟环境分不清
- 不同项目依赖冲突
- 团队成员环境不一致

### uv 如何解决这些痛点

| 痛点 | uv 的解决方案 |
|------|--------------|
| 工具繁多 | 一个工具搞定一切，命令简洁统一 |
| 速度慢 | 用 Rust 编写，比 pip 快 **10-100 倍** |
| 环境混乱 | 项目级隔离，`pyproject.toml` + `uv.lock` 保证一致性 |

---

## 三、为什么选 uv

### 与其他工具对比

| 工具 | 语言 | 速度 | 功能覆盖 | 社区活跃度 | 学习成本 |
|------|------|------|----------|-----------|----------|
| **uv** | Rust | 极快 | 全（版本+环境+依赖+锁定） | 快速增长 | 低 |
| pip + venv | Python | 慢 | 基础（无版本管理、无锁定） | 极高 | 低 |
| poetry | Python | 中等 | 部分（无版本管理） | 高 | 中 |
| pipenv | Python | 慢 | 部分 | 下降中 | 中 |
| conda | C/Python | 慢 | 全（含科学计算库） | 高 | 高 |
| hatch | Python | 中等 | 部分 | 中 | 中 |

### 选择 uv 的核心理由

1. **速度快**：Rust 编写，性能碾压同类工具
2. **功能全**：一个工具覆盖 Python 版本管理、虚拟环境、依赖管理、锁定文件
3. **兼容性好**：与 `pip` 生态完全兼容，支持 `requirements.txt`
4. **现代标准**：使用 `pyproject.toml`（PEP 621 标准）
5. **活跃维护**：Astral 公司全职维护，更新频繁
6. **学习成本低**：命令简洁直观，与 pip 命令风格相似

### 什么时候**不**用 uv

| 场景 | 推荐工具 | 原因 |
|------|----------|------|
| 科学计算（需要 MKL、CUDA 等非 Python 依赖） | conda | conda 能管理非 Python 依赖 |
| 维护老项目（只有 requirements.txt，无 pyproject.toml） | pip | 不必为了老项目引入新工具 |
| 公司强制规定使用特定工具 | 按公司规定 | 团队一致性优先 |

---

## 四、安装 uv

### 4.1 如何验证是否已安装

打开终端（PowerShell 或 CMD），执行：

```bash
uv --version
```

- **已安装**：显示版本号，如 `uv 0.11.8`
- **未安装**：提示 `'uv' 不是内部或外部命令`

### 4.2 如何安装（Windows 11）

#### 方式 1：PowerShell 安装（官方推荐）

打开 **PowerShell**，执行：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### 方式 2：winget 安装

```powershell
winget install --id=astral-sh.uv -e
```

#### 方式 3：pip 安装（需已有 Python）

```bash
pip install uv
```

#### 方式 4：手动下载

1. 访问 https://github.com/astral-sh/uv/releases
2. 下载 `uv-x86_64-pc-windows-msvc.zip`
3. 解压后将 `uv.exe` 放到某目录
4. 把该目录添加到系统环境变量 PATH

---

## 五、uv 环境变量管理（完整版）

### 5.1 为什么需要了解环境变量

uv 的很多行为可以通过**环境变量**来定制，例如：
- Python 安装在哪里
- 缓存放哪里
- 包从哪里下载（镜像源）
- 项目虚拟环境叫什么

### 5.2 修改环境变量的通用方法

#### 方法 A：用 `setx` 命令永久设置（推荐）

```bash
setx 变量名 "变量值"
```

示例：
```bash
setx UV_PYTHON_INSTALL_DIR "D:\uv_python"
```

#### 方法 B：系统环境变量 GUI 设置（图形界面）

1. `Win + R` → `sysdm.cpl` → 高级 → 环境变量
2. 新建或编辑变量，确定后重新打开终端

#### 方法 C：临时设置（仅当前终端有效）

CMD：`set UV_PYTHON_INSTALL_DIR=D:\uv_python`
PowerShell：`$env:UV_PYTHON_INSTALL_DIR = "D:\uv_python"`

### 5.3 uv 常用环境变量完整清单

| 环境变量 | 作用 | 默认值（Windows） | 常用度 |
|----------|------|-------------------|--------|
| `UV_PYTHON_INSTALL_DIR` | uv 管理的 Python 安装目录 | `C:\Users\{用户}\AppData\Roaming\uv\python` | 高 |
| `UV_TOOL_DIR` | uv 工具环境安装目录 | `C:\Users\{用户}\AppData\Roaming\uv\tools` | 中 |
| `UV_TOOL_BIN_DIR` | uv 工具可执行文件的 bin 目录 | `C:\Users\{用户}\AppData\Roaming\uv\bin` | 中 |
| `UV_CACHE_DIR` | uv 缓存目录 | `C:\Users\{用户}\AppData\Local\uv\cache` | 高 |
| `UV_PROJECT_ENVIRONMENT` | 项目虚拟环境的路径 | `项目目录\.venv` | 中 |
| `UV_INDEX_URL` | Python 包索引的 URL（镜像源） | `https://pypi.org/simple` | 高（国内必用） |

---

## 六、用 uv 管理 Python 版本

```bash
uv python install 3.12      # 安装 Python 3.12
uv python list               # 查看所有已安装的 Python 版本
uv python pin 3.12           # 给当前项目固定 Python 版本
uv python uninstall 3.12     # 卸载 Python 3.12
uv run python --version      # 查看当前项目用的 Python 版本
```

---

## 七、用 uv 管理虚拟环境

| 操作 | 传统方式（venv/pip） | uv 方式 |
|------|---------------------|---------|
| 创建虚拟环境 | `python -m venv .venv` | `uv venv`（或自动创建） |
| **激活虚拟环境** | `.venv\Scripts\activate` | **不需要** |
| 安装依赖 | `pip install xxx` | `uv add xxx` |
| 运行程序 | `python xxx.py` | `uv run python xxx.py` |

> **关键理解**：`uv run` 命令会自动使用项目 `.venv` 中的环境，无需手动激活。

---

## 八、用 uv 管理依赖

```bash
uv add langchain             # 添加运行时依赖
uv add --dev pytest          # 添加开发依赖
uv remove langchain          # 删除依赖
uv sync                      # 同步依赖（团队协作核心命令）
uv lock                      # 生成/更新 uv.lock
uv pip list                  # 查看已安装的包
```

| 文件 | 作用 | 是否提交 git |
|------|------|-------------|
| `pyproject.toml` | 声明项目元数据和依赖 | 提交 |
| `uv.lock` | 锁定精确版本（自动生成） | 提交 |
| `.venv` | 实际的虚拟环境 | 不提交 |

---

## 九、用 uv 运行项目

**黄金法则**：在 uv 项目中，**所有 Python 相关命令都用 `uv run` 前缀**。

```bash
uv run python src/main.py    # 运行项目
uv run pytest                 # 运行测试
```

---

## 十、uv 与系统 Python / Anaconda 的关系

| 原则 | 说明 |
|------|------|
| uv 项目用 `uv run` | 所有 Python 命令都用 `uv run python ...` |
| 不混用 pip 和 uv | uv 项目中用 `uv add`，不要用 `pip install` |
| 不混用 conda 和 uv | 同一个项目只用一个工具管理依赖 |

---

## 十一、完整工作流程示例

### 场景 1：从零创建项目

```bash
cd D:\ZCodeProject
uv init langchain-chat
cd langchain-chat
uv python pin 3.12
uv add langchain langchain-openai rich prompt_toolkit
uv add --dev pytest pytest-asyncio ruff
uv run python src/main.py
```

### 场景 2：clone 别人的项目后

```bash
git clone <仓库地址>
cd langchain-chat
uv python install 3.12
uv sync
uv run python src/main.py
```

### 场景 3：团队协作中添加新依赖

```bash
# 开发者 A
uv add httpx
git add pyproject.toml uv.lock
git commit -m "feat: add httpx dependency"
git push

# 开发者 B
git pull
uv sync    # 自动安装 httpx
```

---

## 附录：命令速查表

| 命令 | 作用 |
|------|------|
| `uv python install 3.12` | 安装 Python 3.12 |
| `uv python list` | 查看所有已安装的 Python 版本 |
| `uv python pin 3.12` | 固定当前项目 Python 版本 |
| `uv venv` | 创建虚拟环境 |
| `uv add 包名` | 添加运行时依赖 |
| `uv add --dev 包名` | 添加开发依赖 |
| `uv remove 包名` | 删除依赖 |
| `uv sync` | 同步依赖 |
| `uv lock` | 生成/更新 uv.lock |
| `uv run python xxx.py` | 在虚拟环境中运行脚本 |
| `uv cache clean` | 清理缓存 |

---

## 核心要点回顾

1. **uv 一个工具搞定 Python 一切**：版本管理 + 虚拟环境 + 依赖管理 + 锁定文件
2. **`uv run` 是黄金法则**：不需要手动激活虚拟环境
3. **每个项目独立指定 Python 版本**：用 `uv python pin`
4. **pyproject.toml + uv.lock 提交 git，.venv 不提交**
5. **`uv sync` 是团队协作的核心**：保证环境一致
6. **不混用工具**：uv 项目中不用 pip、不用 conda

---

> **更多信息**：
> - uv 官方文档：https://docs.astral.sh/uv/
> - uv GitHub：https://github.com/astral-sh/uv
