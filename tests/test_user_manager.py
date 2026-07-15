"""用户管理业务层测试（UserManager）。

测试 UserManager 的业务规则：用户名唯一、参数校验、异常处理。
"""

import os

import pytest

from core.user_manager import UserManager
from storage.sqlite_backend import SQLiteBackend


@pytest.fixture
async def user_manager():
    """提供一个干净的 UserManager（含临时数据库）。"""
    db_path = "data/sqlite/test_um.db"
    backend = SQLiteBackend(db_path)
    await backend.initialize()
    manager = UserManager(backend)
    yield manager
    await backend.close()
    if os.path.exists(db_path):
        os.remove(db_path)


class TestUserManager:

    async def test_create_user_success(self, user_manager):
        """正常情况：创建用户成功。"""
        user = await user_manager.create_user("alice")
        assert user.username == "alice"
        assert user.id > 0

    async def test_create_user_empty_name_raises(self, user_manager):
        """异常情况：空用户名报 ValueError。"""
        with pytest.raises(ValueError, match="不能为空"):
            await user_manager.create_user("")

    async def test_create_user_whitespace_name_raises(self, user_manager):
        """异常情况：纯空格用户名报 ValueError。"""
        with pytest.raises(ValueError, match="不能为空"):
            await user_manager.create_user("   ")

    async def test_create_duplicate_user_raises(self, user_manager):
        """异常情况：重复用户名报 ValueError。"""
        await user_manager.create_user("alice")
        with pytest.raises(ValueError, match="已存在"):
            await user_manager.create_user("alice")

    async def test_get_user_exists(self, user_manager):
        """正常情况：查询已存在的用户。"""
        await user_manager.create_user("alice")
        user = await user_manager.get_user("alice")
        assert user is not None
        assert user.username == "alice"

    async def test_get_user_not_exists(self, user_manager):
        """边界情况：查询不存在的用户返回 None。"""
        user = await user_manager.get_user("nobody")
        assert user is None

    async def test_user_exists_true(self, user_manager):
        """正常情况：user_exists 返回 True。"""
        await user_manager.create_user("alice")
        assert await user_manager.user_exists("alice") is True

    async def test_user_exists_false(self, user_manager):
        """边界情况：user_exists 返回 False。"""
        assert await user_manager.user_exists("nobody") is False

    async def test_delete_user(self, user_manager):
        """正常情况：删除用户后查不到。"""
        user = await user_manager.create_user("alice")
        await user_manager.delete_user(user.id)
        assert await user_manager.get_user("alice") is None

    async def test_list_users(self, user_manager):
        """正常情况：列出多个用户。"""
        await user_manager.create_user("alice")
        await user_manager.create_user("bob")
        users = await user_manager.list_users()
        assert len(users) == 2
