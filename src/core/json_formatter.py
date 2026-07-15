"""自定义 JSON 格式日志 Formatter。

将日志记录格式化为每行一个 JSON 对象，方便机器解析和日志采集系统消费。
对应需求 G2（JSON 格式日志）。

敏感信息脱敏：对 message 中的 API Key 模式（sk-xxx）进行脱敏处理。
"""

import json
import re
import logging
from datetime import datetime

_API_KEY_PATTERN = re.compile(r'sk-[A-Za-z0-9]{10,}')


def mask_api_key(text: str) -> str:
    """对文本中的 API Key 进行脱敏（只显示前 8 位）。"""
    return _API_KEY_PATTERN.sub(lambda m: m.group()[:8] + '...', text)


class JsonFormatter(logging.Formatter):
    """JSON 格式日志 Formatter。"""

    def format(self, record: logging.LogRecord) -> str:
        log_dict = {
            "time": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "module": record.name,
            "message": mask_api_key(str(record.msg)),
        }
        return json.dumps(log_dict, ensure_ascii=False)
