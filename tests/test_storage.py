"""存储层测试（SQLiteBackend）。

测试 SQLiteBackend 的核心 CRUD 方法，覆盖正常、边界、异常情况。
每个测试使用 conftest.py 的 db_backend fixture，获得独立的临时数据库。
"""

import pytest

from models.schemas import Message, Preset, Session, User


class TestUser:
    """用户相关方法的测试。"""

    async def test_create_user_normal(self, db_backend):
        """正常情况：创建用户。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        assert user.id > 0
        assert user.username == "alice"
        assert user.created_at is not None

    async def test_create_multiple_users(self, db_backend):
        """正常情况：创建多个用户，验证 id 递增。"""
        user1 = await db_backend.create_user(User(id=0, username="alice"))
        user2 = await db_backend.create_user(User(id=0, username="bob"))
        assert user2.id > user1.id

    async def test_get_user_by_name_exists(self, db_backend):
        """正常情况：查询已存在的用户。"""
        await db_backend.create_user(User(id=0, username="alice"))
        found = await db_backend.get_user_by_name("alice")
        assert found is not None
        assert found.username == "alice"

    async def test_get_user_by_name_not_exists(self, db_backend):
        """边界情况：查询不存在的用户，返回 None。"""
        found = await db_backend.get_user_by_name("nobody")
        assert found is None

    async def test_list_users_empty(self, db_backend):
        """边界情况：空数据库返回空列表。"""
        users = await db_backend.list_users()
        assert users == []

    async def test_list_users_multiple(self, db_backend):
        """正常情况：列出多个用户。"""
        await db_backend.create_user(User(id=0, username="alice"))
        await db_backend.create_user(User(id=0, username="bob"))
        users = await db_backend.list_users()
        assert len(users) == 2

    async def test_delete_user(self, db_backend):
        """正常情况：删除用户后查不到。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        await db_backend.delete_user(user.id)
        found = await db_backend.get_user_by_name("alice")
        assert found is None

    async def test_update_user(self, db_backend):
        """正常情况：更新用户 default_model。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        user.default_model = "deepseek-v4-pro"
        await db_backend.update_user(user)
        found = await db_backend.get_user_by_name("alice")
        assert found.default_model == "deepseek-v4-pro"


class TestSession:
    """会话相关方法的测试。"""

    async def test_create_session(self, db_backend):
        """正常情况：创建会话。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        session = await db_backend.create_session(Session(
            id=0, user_id=user.id, title="测试", model_name="qwen3.6-flash"))
        assert session.id > 0
        assert session.title == "测试"

    async def test_list_sessions_by_user(self, db_backend):
        """正常情况：列出指定用户的会话。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        await db_backend.create_session(Session(id=0, user_id=user.id, title="S1", model_name="m1"))
        await db_backend.create_session(Session(id=0, user_id=user.id, title="S2", model_name="m2"))
        sessions = await db_backend.list_sessions(user.id)
        assert len(sessions) == 2

    async def test_list_sessions_user_isolation(self, db_backend):
        """用户隔离：A 的会话不出现在 B 的列表。"""
        user_a = await db_backend.create_user(User(id=0, username="alice"))
        user_b = await db_backend.create_user(User(id=0, username="bob"))
        await db_backend.create_session(Session(id=0, user_id=user_a.id, title="A", model_name="m1"))
        sessions_b = await db_backend.list_sessions(user_b.id)
        assert len(sessions_b) == 0

    async def test_delete_session_cascade(self, db_backend):
        """级联删除：删除会话后消息也被删除。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        session = await db_backend.create_session(Session(
            id=0, user_id=user.id, title="测试", model_name="m1"))
        await db_backend.add_message(Message(id=0, session_id=session.id, role="human", content="hello"))
        await db_backend.delete_session(session.id)
        messages = await db_backend.list_messages(session.id)
        assert len(messages) == 0


class TestMessage:
    """消息相关方法的测试。"""

    async def test_add_and_list_messages(self, db_backend):
        """正常情况：添加并查询消息。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        session = await db_backend.create_session(Session(
            id=0, user_id=user.id, title="测试", model_name="m1"))
        await db_backend.add_message(Message(id=0, session_id=session.id, role="human", content="你好"))
        await db_backend.add_message(Message(id=0, session_id=session.id, role="ai", content="你好！"))
        messages = await db_backend.list_messages(session.id)
        assert len(messages) == 2
        assert messages[0].role == "human"
        assert messages[1].role == "ai"

    async def test_search_messages(self, db_backend):
        """正常情况：搜索关键词。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        session = await db_backend.create_session(Session(
            id=0, user_id=user.id, title="测试", model_name="m1"))
        await db_backend.add_message(Message(id=0, session_id=session.id, role="human", content="Python 是好语言"))
        await db_backend.add_message(Message(id=0, session_id=session.id, role="ai", content="Java 也不错"))
        results = await db_backend.search_messages(user.id, "Python")
        assert len(results) == 1
        assert "Python" in results[0].content

    async def test_search_messages_no_result(self, db_backend):
        """边界情况：搜索不存在的关键词返回空。"""
        user = await db_backend.create_user(User(id=0, username="alice"))
        session = await db_backend.create_session(Session(
            id=0, user_id=user.id, title="测试", model_name="m1"))
        await db_backend.add_message(Message(id=0, session_id=session.id, role="human", content="hello"))
        results = await db_backend.search_messages(user.id, "zzzzz")
        assert len(results) == 0


class TestPreset:
    """预设相关方法的测试。"""

    async def test_save_and_get_preset(self, db_backend):
        """正常情况：保存并查询预设。"""
        preset = await db_backend.save_preset(Preset(
            id=0, user_id=None, name="翻译助手", description="中英互译",
            system_prompt="你是翻译", is_builtin=True))
        assert preset.id > 0
        found = await db_backend.get_preset_by_id(preset.id)
        assert found is not None
        assert found.name == "翻译助手"

    async def test_list_presets(self, db_backend):
        """正常情况：列出内置和用户预设。"""
        # 先创建一个用户（外键约束需要）
        user = await db_backend.create_user(User(id=0, username="preset_user"))
        await db_backend.save_preset(Preset(
            id=0, user_id=None, name="内置1", system_prompt="p1", is_builtin=True))
        await db_backend.save_preset(Preset(
            id=0, user_id=user.id, name="自定义1", system_prompt="p2", is_builtin=False))
        presets = await db_backend.list_presets(user_id=user.id)
        assert len(presets) == 2

    async def test_delete_preset(self, db_backend):
        """正常情况：删除预设后查不到。"""
        preset = await db_backend.save_preset(Preset(
            id=0, user_id=None, name="临时", system_prompt="prompt", is_builtin=True))
        await db_backend.delete_preset(preset.id)
        found = await db_backend.get_preset_by_id(preset.id)
        assert found is None
