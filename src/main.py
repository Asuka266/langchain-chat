"""langchain-chat 程序总入口。

Step 12 阶段：加载日志配置、初始化存储、导入内置预设、创建对话引擎、启动 TUI。
运行方式：uv run python src/main.py
"""

import asyncio
import sys
from pathlib import Path

# 将 src 目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent))


async def async_main() -> None:
    """异步主函数。"""
    # 0. 加载日志配置（最先加载）
    import logging.config
    import yaml as yaml_for_logging

    Path("logs").mkdir(exist_ok=True)
    with open("config/logging.yaml", "r", encoding="utf-8") as f:
        logging.config.dictConfig(yaml_for_logging.safe_load(f))

    logger = logging.getLogger(__name__)
    logger.info("程序启动")

    # 1. 加载配置
    from core.config_manager import get_config

    config = get_config()
    logger.info("存储后端: %s，默认模型: %s", config.storage_type, config.default_model)
    print(f"[启动] 存储后端: {config.storage_type}，默认模型: {config.default_model}")

    # 2. 初始化存储后端
    from storage.factory import StorageFactory

    backend = StorageFactory.create(config.storage_type)
    await backend.initialize()
    logger.info("存储后端已就绪: %s", type(backend).__name__)
    print(f"[启动] 存储后端已就绪: {type(backend).__name__}")

    # 3. 导入系统内置预设
    from core.preset_manager import PresetManager

    preset_manager = PresetManager(backend)
    imported = await preset_manager.load_builtin_presets()
    if imported > 0:
        logger.info("导入了 %d 个系统内置预设", imported)
        print(f"[启动] 导入了 {imported} 个系统内置预设")

    # 4. 创建对话引擎
    from core.chat_engine import ChatEngine

    engine = ChatEngine(config)
    logger.info("对话引擎已就绪: %s", config.default_model)
    print(f"[启动] 对话引擎已就绪: {config.default_model}")

    # 5. 启动 TUI
    from ui.tui.app import TUIApp

    try:
        app = TUIApp(backend=backend, engine=engine, config=config)
        await app.run()
    finally:
        await engine.close()
        await backend.close()
        logger.info("程序关闭")
        print("[关闭] 对话引擎与存储后端已关闭")


def main() -> None:
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
