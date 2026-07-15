"""配置加载与管理。

本模块负责读取并合并多个配置源：
    1. .env 文件：各服务商的 API Key、默认模型名。
    2. config.yaml 文件：基础业务配置（所有环境共享）。
    3. config.{APP_ENV}.yaml 文件：环境覆盖配置（Step 15 多环境区分）。

合并规则（Step 15）：
    最终配置 = config.yaml（基础） + config.{APP_ENV}.yaml（环境覆盖）
    环境覆盖文件只写「与基础配置不同的字段」，合并时深度覆盖。
"""

import copy
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv


def _load_env():
    """加载 .env 文件到环境变量。

    Step 15 多环境：根据 APP_ENV 加载对应的 .env 文件。
    """
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path, override=True)

    app_env = os.environ.get("APP_ENV", "dev")

    env_specific = Path(f".env.{app_env}")
    if env_specific.exists():
        load_dotenv(env_specific, override=True)


_load_env()


def get_config_value(env_key: str, default: str = "") -> str:
    return os.environ.get(env_key, default)


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典。对于嵌套字典递归合并，非字典值覆盖。"""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class AppConfig:
    """应用配置（单例）。"""

    def __init__(self) -> None:
        self.app_env: str = os.environ.get("APP_ENV", "dev")

        base_config = self._load_yaml("config.yaml")
        env_config_file = f"config.{self.app_env}.yaml"
        env_config = self._load_yaml(env_config_file)
        self._yaml_config: dict[str, Any] = _deep_merge(base_config, env_config)

    def _load_yaml(self, filename: str) -> dict[str, Any]:
        path = Path(filename)
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    @property
    def default_model(self) -> str:
        return get_config_value("DEFAULT_MODEL", "deepseek-chat")

    def get_api_key(self, env_key: str) -> str:
        return get_config_value(env_key, "")

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

    @property
    def temperature(self) -> float:
        return self._yaml_config.get("temperature", 0.7)

    @property
    def max_tokens(self) -> int:
        return self._yaml_config.get("max_tokens", 2048)

    @property
    def current_step(self) -> str:
        return self._yaml_config.get("app", {}).get("current_step", "开发中")

    @property
    def storage_type(self) -> str:
        return self._yaml_config.get("storage", {}).get("type", "sqlite")

    @property
    def max_input_length(self) -> int:
        """用户单次输入最大字符数。"""
        return self._yaml_config.get("security", {}).get("max_input_length", 5000)

    @property
    def context_max_tokens(self) -> int:
        """发送给 LLM 的上下文最大 Token 数。"""
        return self._yaml_config.get("security", {}).get("context_max_tokens", 4000)

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
