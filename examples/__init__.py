"""LLM 编程学习示例。

本包包含从底层到高层的三层 LLM 调用示例，帮助理解「如何用代码和 LLM 对话」：
    - example1_http.py          第一层：HTTP 直接调 API（最底层）
    - example2_openai_sdk.py    第二层：OpenAI 官方 SDK
    - example3_langchain.py     第三层：LangChain ChatOpenAI（项目选用）

示例与项目正式代码（src/）完全隔离，只依赖第三方库，不 import src 模块。
"""
