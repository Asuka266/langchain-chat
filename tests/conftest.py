"""全局 pytest fixture。

为所有测试提供独立的、干净的临时数据库。
每个测试函数都会获得一个全新的数据库实例，互不影响（FIRST 原则的 Independent）。
"""

import os
import sys
from pathlib import Path

import pytest

# 将 src 目录加入搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from storage.sqlite_backend import SQLiteBackend


@pytest.fixture
async def db_backend():
    """提供一个干净的临时 SQLiteBackend。

    每个使用此 fixture 的测试函数都会获得：
    1. 一个全新的临时数据库文件
    2. 已初始化（建表完成）
    3. 测试结束后自动删除临时文件
    """
    db_path = "data/sqlite/test_pytest.db"
    backend = SQLiteBackend(db_path)
    await backend.initialize()
    yield backend
    await backend.close()
    if os.path.exists(db_path):
        os.remove(db_path)
