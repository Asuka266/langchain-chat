"""对话引擎（核心模块）。

封装 LLM 的调用逻辑：多轮对话、流式输出、超时重试、Token 统计、模型切换。
Step 10 重构：支持多服务商模型切换（switch_model）。
Step 16a 优化：变量命名 + 上下文裁剪（trim_messages）。
"""

from typing import AsyncIterator, Optional

import logging

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

from core.config_manager import AppConfig


class ChatEngine:
    """对话引擎。"""

    def __init__(self, config: AppConfig):
        self.config = config
        self.current_model: str = config.default_model
        self.chat_model: ChatOpenAI = self._create_chat_model(self.current_model)

    def _create_chat_model(self, model_value: str) -> ChatOpenAI:
        provider = self.config.find_provider_by_model(model_value)
        if provider is None:
            raise ValueError(f"模型 '{model_value}' 不在可选列表中")
        api_key = self.config.get_api_key(provider["api_key_env"])
        if not api_key:
            raise ValueError(
                f"服务商 '{provider['name']}' 的 API Key 未配置"
                f"（请检查 .env 的 {provider['api_key_env']}）"
            )
        return ChatOpenAI(
            model=model_value,
            api_key=api_key,
            base_url=provider["base_url"],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            timeout=self.config.llm_timeout,
            max_retries=self.config.llm_max_retries,
            streaming=True,
        )

    def switch_model(self, model_value: str) -> None:
        """切换模型（A5）。"""
        self.chat_model = self._create_chat_model(model_value)
        self.current_model = model_value
        logger.info("模型切换: -> %s", model_value)

    def trim_messages(self, messages: list[BaseMessage], max_tokens: int = None) -> list[BaseMessage]:
        """裁剪消息列表（滑动窗口 + Token 计数）。

        SystemMessage 永远保留，从最后一条往前累加 Token 直到达到 max_tokens。
        Token 数用字符数 / 2 估算（中文为主时较准确）。
        """
        if max_tokens is None:
            max_tokens = self.config.context_max_tokens

        system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
        other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

        if not other_msgs:
            return system_msgs

        # 从最后一条往前累加 Token
        kept = []
        total = 0
        for msg in reversed(other_msgs):
            est = max(1, len(msg.content) // 2)
            if total + est > max_tokens and kept:
                break
            kept.insert(0, msg)
            total += est

        return system_msgs + kept

    def chat(self, messages: list[BaseMessage]) -> tuple[str, dict]:
        response: AIMessage = self.chat_model.invoke(messages)
        return response.content, self._extract_usage(response)

    async def astream(self, messages: list[BaseMessage]) -> AsyncIterator[tuple[str, Optional[dict]]]:
        final_usage = None
        async for chunk in self.chat_model.astream(messages):
            text = chunk.content
            if text:
                yield text, None
            usage = self._extract_usage(chunk)
            if usage is not None:
                final_usage = usage
        yield "", final_usage

    def _extract_usage(self, message: BaseMessage) -> Optional[dict]:
        usage_meta = getattr(message, "usage_metadata", None)
        if usage_meta is None:
            return None
        return {
            "prompt_tokens": usage_meta.get("input_tokens", 0),
            "completion_tokens": usage_meta.get("output_tokens", 0),
            "total_tokens": usage_meta.get("total_tokens", 0),
        }

    async def close(self) -> None:
        pass
