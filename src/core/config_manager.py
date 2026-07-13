"""配置加载与管理。

本模块负责读取并合并两个配置源：
    1. .env 文件：各服务商的 API Key、默认模型名。
    2. config.yaml 文件：服务商分组配置、生成参数、存储配置等。

Step 10 重构：从单一服务商改为多服务商分组（providers 结构）。
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


def _load_env():
    """加载 .env 文件到环境变量。"""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)


_load_env()


def get_config_value(env_key: str, default: str = "") -> str:
    """从环境变量读取配置值。"""
    return os.environ.get(env_key, default)


class AppConfig:
    """应用配置（单例）。"""

    def __init__(self) -> None:
        self._yaml_config: dict[str, Any] = self._load_yaml("config.yaml")

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = Path(filename)
        if not path.exists():
            print(f"[配置警告] 配置文件 {filename} 不存在，使用空配置")
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    # ── 敏感配置（从 .env 读取）─────────────────────────────────────────

    @property
    def default_model(self) -> str:
        """默认模型名（从 .env 的 DEFAULT_MODEL 读取）。"""
        return get_config_value("DEFAULT_MODEL", "deepseek-chat")

    def get_api_key(self, env_key: str) -> str:
        """按变量名从 .env 读取 API Key。"""
        return get_config_value(env_key, "")

    # ── 服务商配置 ─────────────────────────────────────────────────────

    @property
    def providers(self) -> list[dict]:
        return self._yaml_config.get("providers", [])

    def get_all_models(self) -> list[dict[str, str]]:
        result = []
        for provider in self.providers:
            for model in provider.get("models", []):
                result.append({
                    "name": model.get("name", model.get("value", "")),
                    "value": model.get("value", ""),
                    "provider": provider.get("name", ""),
                })
        return result

    def find_provider_by_model(self, model_value: str) -> Optional[dict]:
        for provider in self.providers:
            for model in provider.get("models", []):
                if model.get("value") == model_value:
                    return provider
        return None

    # ── 生成参数 ───────────────────────────────────────────────────────

    @property
    def temperature(self) -> float:
        return self._yaml_config.get("temperature", 0.7)

    @property
    def max_tokens(self) -> int:
        return self._yaml_config.get("max_tokens", 2048)

    # ── 其他配置 ──────────────────────────────────────────────────────

    @property
    def current_step(self) -> str:
        return self._yaml_config.get("app", {}).get("current_step", "开发中")

    @property
    def storage_type(self) -> str:
        return self._yaml_config.get("storage", {}).get("type", "sqlite")

    @property
    def llm_timeout(self) -> int:
        return self._yaml_config.get("llm", {}).get("timeout", 30)

    @property
    def llm_max_retries(self) -> int:
        return self._yaml_config.get("llm", {}).get("max_retries", 3)

    @property
    def title_max_length(self) -> int:
        return self._yaml_config.get("session", {}).get("title_max_length", 30)

    def get(self, *keys: str, default: Any = None) -> Any:
        value: Any = self._yaml_config
        for key in keys:
            if not isinstance(value, dict):
                return default
            value = value.get(key)
            if value is None:
                return default
        return value


_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
