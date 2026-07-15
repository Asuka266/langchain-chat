"""会话管理业务层测试（SessionManager）。"""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config_manager import AppConfig
from core.session_manager import SessionManager
from models.schemas import User
from storage.sqlite_backend import SQLiteBackend


@pytest.fixture
async def session_manager():
    db_path = "data/sqlite/test_sm.db"
    backend = SQLiteBackend(db_path)
    await backend.initialize()
    config = AppConfig()
    manager = SessionManager(backend, config)
    yield manager
    await backend.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestSessionManager:

    async def _ensure_user(self, sm):
        """创建测试用户，返回 user_id。"""
        user = await sm.backend.create_user(User(id=0, username="testuser"))
        return user.id

    async def test_create_session(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="qwen3.6-flash")
        assert session.id > 0
        assert session.title == "新会话"

    async def test_add_message_updates_tokens(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="m1")
        await session_manager.add_message(session, role="ai", content="回复",
                                           prompt_tokens=10, completion_tokens=20)
        assert session.total_prompt_tokens == 10
        assert session.total_completion_tokens == 20

    async def test_load_messages(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="m1")
        await session_manager.add_message(session, role="human", content="你好")
        await session_manager.add_message(session, role="ai", content="你好！")
        messages = await session_manager.load_messages_as_langchain(session.id)
        assert len(messages) == 2

    async def test_rename_session(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="m1")
        await session_manager.rename_session(session.id, "新标题")
        found = await session_manager.get_session(session.id)
        assert found.title == "新标题"

    async def test_rename_session_empty_raises(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="m1")
        with pytest.raises(ValueError, match="不能为空"):
            await session_manager.rename_session(session.id, "")

    async def test_delete_session(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="m1")
        await session_manager.delete_session(session.id)
        found = await session_manager.get_session(session.id)
        assert found is None

    async def test_search_messages(self, session_manager):
        uid = await self._ensure_user(session_manager)
        session = await session_manager.create_session(user_id=uid, model_name="m1")
        await session_manager.add_message(session, role="human", content="Python 编程")
        results = await session_manager.search_messages(uid, "Python")
        assert len(results) == 1
        assert "Python" in results[0].content
