"""集成测试。

测试多个模块协同工作：UserManager + SessionManager + SQLiteBackend。
"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config_manager import AppConfig
from core.session_manager import SessionManager
from core.user_manager import UserManager
from models.schemas import User
from storage.sqlite_backend import SQLiteBackend


@pytest.fixture
async def setup():
    """提供完整的集成环境：backend + UserManager + SessionManager。"""
    db_path = "data/sqlite/test_int.db"
    backend = SQLiteBackend(db_path)
    await backend.initialize()
    config = AppConfig()
    user_mgr = UserManager(backend)
    session_mgr = SessionManager(backend, config)
    yield backend, user_mgr, session_mgr
    await backend.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestFullWorkflow:

    async def test_create_user_then_session_then_message(self, setup):
        """集成测试：建用户→建会话→加消息→查询。"""
        backend, user_mgr, session_mgr = setup
        user = await user_mgr.create_user("alice")
        session = await session_mgr.create_session(user.id, "qwen3.6-flash")
        await session_mgr.add_message(session, role="human", content="你好")
        await session_mgr.add_message(session, role="ai", content="你好！")
        msgs = await session_mgr.load_messages_as_langchain(session.id)
        assert len(msgs) == 2

    async def test_search_across_modules(self, setup):
        """集成测试：跨模块搜索（UserManager + SessionManager）。"""
        backend, user_mgr, session_mgr = setup
        user = await user_mgr.create_user("alice")
        session = await session_mgr.create_session(user.id, "m1")
        await session_mgr.add_message(session, role="human", content="Python 编程")
        results = await session_mgr.search_messages(user.id, "Python")
        assert len(results) == 1
        assert "Python" in results[0].content

    async def test_user_isolation_integration(self, setup):
        """集成测试：两用户数据隔离。"""
        backend, user_mgr, session_mgr = setup
        user_a = await user_mgr.create_user("alice")
        user_b = await user_mgr.create_user("bob")
        sa = await session_mgr.create_session(user_a.id, "m1")
        await session_mgr.add_message(sa, role="human", content="A的秘密")
        # 用户 B 搜索不到 A 的消息
        results = await session_mgr.search_messages(user_b.id, "A的秘密")
        assert len(results) == 0

    async def test_cascade_delete_integration(self, setup):
        """集成测试：级联删除（删用户→会话消息也删）。"""
        backend, user_mgr, session_mgr = setup
        user = await user_mgr.create_user("alice")
        session = await session_mgr.create_session(user.id, "m1")
        await session_mgr.add_message(session, role="human", content="test")
        await user_mgr.delete_user(user.id)
        found = await user_mgr.get_user("alice")
        assert found is None

    async def test_session_lifecycle_integration(self, setup):
        """集成测试：会话生命周期（创建→重命名→加载→删除）。"""
        backend, user_mgr, session_mgr = setup
        user = await user_mgr.create_user("alice")
        session = await session_mgr.create_session(user.id, "m1")
        # 重命名
        await session_mgr.rename_session(session.id, "新名字")
        found = await session_mgr.get_session(session.id)
        assert found.title == "新名字"
        # 删除
        await session_mgr.delete_session(session.id)
        found2 = await session_mgr.get_session(session.id)
        assert found2 is None
