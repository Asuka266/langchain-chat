"""langchain-chat 程序总入口。

Step 7 阶段：加载配置、初始化存储、导入内置预设、创建对话引擎、启动 TUI。
运行方式：uv run python src/main.py
"""

import asyncio
import sys
from pathlib import Path

# 将 src 目录加入模块搜索路径，确保 import 链路在任意运行方式下都工作。
sys.path.insert(0, str(Path(__file__).resolve().parent))


async def async_main() -> None:
    """异步主函数。

    启动流程（Step 7 起）：
        1. 加载配置
        2. 初始化存储后端
        3. 导入系统内置预设（幂等）
        4. 创建对话引擎
        5. 启动 TUI 主循环（注入存储后端、引擎、配置）
    """
    # 1. 加载配置
    from core.config_manager import get_config

    config = get_config()
    print(f"[启动] 存储后端: {config.storage_type}，默认模型: {config.default_model}")

    # 2. 初始化存储后端
    from storage.factory import StorageFactory

    backend = StorageFactory.create(config.storage_type)
    await backend.initialize()
    print(f"[启动] 存储后端已就绪: {type(backend).__name__}")

    # 3. 导入系统内置预设
    from core.preset_manager import PresetManager

    preset_manager = PresetManager(backend)
    imported = await preset_manager.load_builtin_presets()
    if imported > 0:
        print(f"[启动] 导入了 {imported} 个系统内置预设")

    # 4. 创建对话引擎
    from core.chat_engine import ChatEngine

    engine = ChatEngine(config)
    print(f"[启动] 对话引擎已就绪: {config.default_model}")

    # 5. 启动 TUI 主循环（注入存储后端、引擎、配置）
    from ui.tui.app import TUIApp

    try:
        app = TUIApp(backend=backend, engine=engine, config=config)
        await app.run()
    finally:
        await engine.close()
        await backend.close()
        print("[关闭] 对话引擎与存储后端已关闭")


def main() -> None:
    """程序主函数（同步入口，内部启动异步事件循环）。"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
