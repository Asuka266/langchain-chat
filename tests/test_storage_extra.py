"""存储层补充测试。

覆盖之前未测的方法：user_config, get_session, update_session, save_preset(update),
get_preset_by_id(not exists), pagination, message order, initialize, close。
"""

import pytest

from models.schemas import Message, Preset, Session, User, UserConfig


class TestUserConfig:
    async def test_set_and_get_config(self, db_backend):
        user = await db_backend.create_user(User(id=0, username="cfg_user"))
        cfg = UserConfig(id=0, user_id=user.id, key="theme", value="dark")
        await db_backend.set_user_config(cfg)
        val = await db_backend.get_user_config(user.id, "theme")
        assert val == "dark"

    async def test_get_config_not_exists(self, db_backend):
        val = await db_backend.get_user_config(999, "nonexistent")
        assert val is None

    async def test_update_existing_config(self, db_backend):
        user = await db_backend.create_user(User(id=0, username="cfg2"))
        cfg = UserConfig(id=0, user_id=user.id, key="lang", value="zh")
        await db_backend.set_user_config(cfg)
        cfg.value = "en"
        await db_backend.set_user_config(cfg)
        val = await db_backend.get_user_config(user.id, "lang")
        assert val == "en"


class TestSessionExtra:
    async def test_get_session_exists(self, db_backend):
        user = await db_backend.create_user(User(id=0, username="s_user"))
        s = await db_backend.create_session(Session(id=0, user_id=user.id, title="T", model_name="m"))
        found = await db_backend.get_session(s.id)
        assert found is not None
        assert found.title == "T"

    async def test_get_session_not_exists(self, db_backend):
        found = await db_backend.get_session(999)
        assert found is None

    async def test_update_session(self, db_backend):
        user = await db_backend.create_user(User(id=0, username="s2"))
        s = await db_backend.create_session(Session(id=0, user_id=user.id, title="Old", model_name="m"))
        s.title = "New"
        await db_backend.update_session(s)
        found = await db_backend.get_session(s.id)
        assert found.title == "New"

    async def test_list_sessions_pagination(self, db_backend):
        user = await db_backend.create_user(User(id=0, username="pag"))
        for i in range(5):
            await db_backend.create_session(Session(id=0, user_id=user.id, title=f"S{i}", model_name="m"))
        # 分页：limit=2, offset=1 → 返回第 2-3 条
        page = await db_backend.list_sessions(user.id, limit=2, offset=1)
        assert len(page) == 2


class TestMessageExtra:
    async def test_message_order(self, db_backend):
        user = await db_backend.create_user(User(id=0, username="mo"))
        s = await db_backend.create_session(Session(id=0, user_id=user.id, title="T", model_name="m"))
        await db_backend.add_message(Message(id=0, session_id=s.id, role="human", content="first"))
        await db_backend.add_message(Message(id=0, session_id=s.id, role="ai", content="second"))
        msgs = await db_backend.list_messages(s.id)
        assert msgs[0].content == "first"
        assert msgs[1].content == "second"


class TestPresetExtra:
    async def test_update_preset(self, db_backend):
        p = await db_backend.save_preset(Preset(id=0, user_id=None, name="old", system_prompt="p", is_builtin=True))
        p.name = "new_name"
        await db_backend.save_preset(p)
        found = await db_backend.get_preset_by_id(p.id)
        assert found.name == "new_name"

    async def test_get_preset_not_exists(self, db_backend):
        found = await db_backend.get_preset_by_id(999)
        assert found is None

    async def test_list_presets_builtin_only(self, db_backend):
        await db_backend.save_preset(Preset(id=0, user_id=None, name="B1", system_prompt="p", is_builtin=True))
        presets = await db_backend.list_presets(user_id=1)
        assert len(presets) == 1


class TestInitializeClose:
    async def test_initialize_creates_tables(self, db_backend):
        # db_backend fixture already calls initialize - just verify it doesn't crash
        # and tables exist by doing an operation
        await db_backend.create_user(User(id=0, username="ic_test"))
        found = await db_backend.get_user_by_name("ic_test")
        assert found is not None

    async def test_close_no_error(self, db_backend):
        # close is called by fixture - verify no error
        pass
