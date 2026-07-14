"""File 存储后端实现。

实现 StorageBackend 定义的全部接口方法，用 JSON 文件存取数据。
对应需求文档第四章「存储架构」（File 为零依赖后端）。

设计说明：
    - 每种实体存为一个 JSON 文件，内容是 JSON 数组。
    - datetime 字段以 ISO 格式字符串存储。
    - 级联删除手动实现（没有数据库的 ON DELETE CASCADE）。
    - 性能：每次操作读写整个文件，适合小数据量。
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from models.schemas import Message, Preset, Session, User, UserConfig
from storage.base import StorageBackend


class FileBackend(StorageBackend):
    """File 存储后端（JSON 文件存取）。"""

    def __init__(self, base_path: str = "data/filestore"):
        self.base_path = Path(base_path)

    async def initialize(self) -> None:
        self.base_path.mkdir(parents=True, exist_ok=True)
        for name in ["users", "sessions", "messages", "presets", "user_configs"]:
            f = self.base_path / f"{name}.json"
            if not f.exists():
                self._write_json(f, [])

    async def close(self) -> None:
        pass

    def _read_json(self, filepath: Path) -> list:
        if not filepath.exists():
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []

    def _write_json(self, filepath: Path, data: list) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _file(self, name: str) -> Path:
        return self.base_path / f"{name}.json"

    @staticmethod
    def _next_id(records: list) -> int:
        return max((r["id"] for r in records), default=0) + 1

    @staticmethod
    def _dt_to_str(dt: datetime) -> str:
        return dt.isoformat()

    @staticmethod
    def _str_to_dt(s: str) -> datetime:
        return datetime.fromisoformat(s)

    def _cascade_delete_user(self, user_id: int, sessions: list, messages: list,
                             presets: list, configs: list):
        session_ids = [s["id"] for s in sessions if s["user_id"] == user_id]
        sessions = [s for s in sessions if s["user_id"] != user_id]
        messages = [m for m in messages if m["session_id"] not in session_ids]
        presets = [p for p in presets if p.get("user_id") != user_id]
        configs = [c for c in configs if c["user_id"] != user_id]
        return sessions, messages, presets, configs

    # ── 用户 ──────────────────────────────────────────────────────────────

    async def create_user(self, user: User) -> User:
        records = self._read_json(self._file("users"))
        user.id = self._next_id(records)
        records.append({"id": user.id, "username": user.username, "default_model": user.default_model,
                        "default_preset_id": user.default_preset_id,
                        "created_at": self._dt_to_str(user.created_at),
                        "updated_at": self._dt_to_str(user.updated_at)})
        self._write_json(self._file("users"), records)
        return user

    async def get_user_by_name(self, username: str) -> Optional[User]:
        records = self._read_json(self._file("users"))
        for r in records:
            if r["username"] == username:
                return self._row_to_user(r)
        return None

    async def list_users(self) -> list[User]:
        records = self._read_json(self._file("users"))
        return [self._row_to_user(r) for r in sorted(records, key=lambda x: x["id"])]

    async def delete_user(self, user_id: int) -> None:
        records = self._read_json(self._file("users"))
        records = [r for r in records if r["id"] != user_id]
        self._write_json(self._file("users"), records)
        sessions = self._read_json(self._file("sessions"))
        messages = self._read_json(self._file("messages"))
        presets = self._read_json(self._file("presets"))
        configs = self._read_json(self._file("user_configs"))
        sessions, messages, presets, configs = self._cascade_delete_user(
            user_id, sessions, messages, presets, configs)
        self._write_json(self._file("sessions"), sessions)
        self._write_json(self._file("messages"), messages)
        self._write_json(self._file("presets"), presets)
        self._write_json(self._file("user_configs"), configs)

    async def update_user(self, user: User) -> None:
        records = self._read_json(self._file("users"))
        for r in records:
            if r["id"] == user.id:
                r.update({"username": user.username, "default_model": user.default_model,
                          "default_preset_id": user.default_preset_id,
                          "updated_at": self._dt_to_str(user.updated_at)})
                break
        self._write_json(self._file("users"), records)

    @staticmethod
    def _row_to_user(r: dict) -> User:
        return User(id=r["id"], username=r["username"], default_model=r.get("default_model"),
                    default_preset_id=r.get("default_preset_id"),
                    created_at=FileBackend._str_to_dt(r["created_at"]),
                    updated_at=FileBackend._str_to_dt(r["updated_at"]))

    # ── 会话 ──────────────────────────────────────────────────────────────

    async def create_session(self, session: Session) -> Session:
        records = self._read_json(self._file("sessions"))
        session.id = self._next_id(records)
        records.append({"id": session.id, "user_id": session.user_id, "title": session.title,
                        "model_name": session.model_name, "preset_id": session.preset_id,
                        "total_prompt_tokens": session.total_prompt_tokens,
                        "total_completion_tokens": session.total_completion_tokens,
                        "created_at": self._dt_to_str(session.created_at),
                        "updated_at": self._dt_to_str(session.updated_at)})
        self._write_json(self._file("sessions"), records)
        return session

    async def get_session(self, session_id: int) -> Optional[Session]:
        records = self._read_json(self._file("sessions"))
        for r in records:
            if r["id"] == session_id:
                return self._row_to_session(r)
        return None

    async def list_sessions(self, user_id: int) -> list[Session]:
        records = self._read_json(self._file("sessions"))
        filtered = [r for r in records if r["user_id"] == user_id]
        return [self._row_to_session(r) for r in sorted(filtered, key=lambda x: x["id"], reverse=True)]

    async def update_session(self, session: Session) -> None:
        session.updated_at = datetime.now(timezone.utc)
        records = self._read_json(self._file("sessions"))
        for r in records:
            if r["id"] == session.id:
                r.update({"title": session.title, "model_name": session.model_name,
                          "preset_id": session.preset_id,
                          "total_prompt_tokens": session.total_prompt_tokens,
                          "total_completion_tokens": session.total_completion_tokens,
                          "updated_at": self._dt_to_str(session.updated_at)})
                break
        self._write_json(self._file("sessions"), records)

    async def delete_session(self, session_id: int) -> None:
        records = self._read_json(self._file("sessions"))
        records = [r for r in records if r["id"] != session_id]
        self._write_json(self._file("sessions"), records)
        messages = self._read_json(self._file("messages"))
        messages = [m for m in messages if m["session_id"] != session_id]
        self._write_json(self._file("messages"), messages)

    @staticmethod
    def _row_to_session(r: dict) -> Session:
        return Session(id=r["id"], user_id=r["user_id"], title=r["title"],
                       model_name=r["model_name"], preset_id=r.get("preset_id"),
                       total_prompt_tokens=r.get("total_prompt_tokens", 0),
                       total_completion_tokens=r.get("total_completion_tokens", 0),
                       created_at=FileBackend._str_to_dt(r["created_at"]),
                       updated_at=FileBackend._str_to_dt(r["updated_at"]))

    # ── 消息 ──────────────────────────────────────────────────────────────

    async def add_message(self, message: Message) -> Message:
        records = self._read_json(self._file("messages"))
        message.id = self._next_id(records)
        records.append({"id": message.id, "session_id": message.session_id, "role": message.role,
                        "content": message.content, "prompt_tokens": message.prompt_tokens,
                        "completion_tokens": message.completion_tokens,
                        "created_at": self._dt_to_str(message.created_at)})
        self._write_json(self._file("messages"), records)
        return message

    async def list_messages(self, session_id: int) -> list[Message]:
        records = self._read_json(self._file("messages"))
        filtered = [r for r in records if r["session_id"] == session_id]
        return [self._row_to_message(r) for r in sorted(filtered, key=lambda x: x["id"])]

    async def search_messages(self, user_id: int, keyword: str) -> list[Message]:
        sessions = self._read_json(self._file("sessions"))
        session_ids = {s["id"] for s in sessions if s["user_id"] == user_id}
        records = self._read_json(self._file("messages"))
        result = [r for r in records if r["session_id"] in session_ids and keyword.lower() in r["content"].lower()]
        return [self._row_to_message(r) for r in sorted(result, key=lambda x: x["id"])]

    @staticmethod
    def _row_to_message(r: dict) -> Message:
        return Message(id=r["id"], session_id=r["session_id"], role=r["role"],
                       content=r["content"], prompt_tokens=r.get("prompt_tokens", 0),
                       completion_tokens=r.get("completion_tokens", 0),
                       created_at=FileBackend._str_to_dt(r["created_at"]))

    # ── 预设 ──────────────────────────────────────────────────────────────

    async def get_preset_by_id(self, preset_id: int) -> Optional[Preset]:
        records = self._read_json(self._file("presets"))
        for r in records:
            if r["id"] == preset_id:
                return self._row_to_preset(r)
        return None

    async def save_preset(self, preset: Preset) -> Preset:
        records = self._read_json(self._file("presets"))
        if not preset.id:
            preset.id = self._next_id(records)
            records.append({"id": preset.id, "user_id": preset.user_id, "name": preset.name,
                            "description": preset.description, "system_prompt": preset.system_prompt,
                            "is_builtin": preset.is_builtin,
                            "created_at": self._dt_to_str(preset.created_at),
                            "updated_at": self._dt_to_str(preset.updated_at)})
        else:
            for r in records:
                if r["id"] == preset.id:
                    r.update({"name": preset.name, "description": preset.description,
                              "system_prompt": preset.system_prompt, "is_builtin": preset.is_builtin,
                              "updated_at": self._dt_to_str(preset.updated_at)})
                    break
        self._write_json(self._file("presets"), records)
        return preset

    async def list_presets(self, user_id: int) -> list[Preset]:
        records = self._read_json(self._file("presets"))
        filtered = [r for r in records if r.get("user_id") is None or r.get("user_id") == user_id]
        return [self._row_to_preset(r) for r in sorted(filtered, key=lambda x: x["id"])]

    async def delete_preset(self, preset_id: int) -> None:
        records = self._read_json(self._file("presets"))
        records = [r for r in records if r["id"] != preset_id]
        self._write_json(self._file("presets"), records)

    @staticmethod
    def _row_to_preset(r: dict) -> Preset:
        return Preset(id=r["id"], user_id=r.get("user_id"), name=r["name"],
                      description=r.get("description", ""), system_prompt=r["system_prompt"],
                      is_builtin=r.get("is_builtin", False),
                      created_at=FileBackend._str_to_dt(r["created_at"]),
                      updated_at=FileBackend._str_to_dt(r["updated_at"]))

    # ── 用户配置 ──────────────────────────────────────────────────────────

    async def get_user_config(self, user_id: int, key: str) -> Optional[str]:
        records = self._read_json(self._file("user_configs"))
        for r in records:
            if r["user_id"] == user_id and r["key"] == key:
                return r["value"]
        return None

    async def set_user_config(self, config: UserConfig) -> None:
        records = self._read_json(self._file("user_configs"))
        for r in records:
            if r["user_id"] == config.user_id and r["key"] == config.key:
                r["value"] = config.value
                r["updated_at"] = self._dt_to_str(config.updated_at)
                self._write_json(self._file("user_configs"), records)
                return
        config.id = self._next_id(records)
        records.append({"id": config.id, "user_id": config.user_id, "key": config.key,
                        "value": config.value, "updated_at": self._dt_to_str(config.updated_at)})
        self._write_json(self._file("user_configs"), records)
