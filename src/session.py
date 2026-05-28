import uuid
import time
from typing import List, Dict
import config


class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.title = ""
        self.created_at = time.time()
        self.last_active = time.time()
        self.history: List[Dict[str, str]] = []

    def add(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > config.MAX_HISTORY * 2:
            self.history = self.history[-(config.MAX_HISTORY * 2):]

    def get_history(self) -> List[Dict[str, str]]:
        max_msgs = config.MAX_HISTORY * 2
        return self.history[-max_msgs:] if len(self.history) > max_msgs else self.history

    def to_dict(self) -> dict:
        return {
            "id": self.session_id,
            "title": self.title or "新对话",
            "created_at": self.created_at,
            "last_active": self.last_active,
            "message_count": len(self.history),
        }


class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def get_or_create(self, session_id: str | None = None) -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        sid = session_id or str(uuid.uuid4())
        session = Session(sid)
        self._sessions[sid] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def get_all(self) -> List[dict]:
        sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.last_active,
            reverse=True,
        )
        return [s.to_dict() for s in sessions if s.history]

    def clear(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]


session_store = SessionStore()
