"""Conversation history management with persistence."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional

from .config import HISTORY_DIR


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tool_use: Optional[dict] = None


@dataclass
class Conversation:
    """A conversation session with history."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = "New Conversation"
    messages: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, role: str, content: str, tool_use: Optional[dict] = None):
        """Add a message to the conversation."""
        msg = Message(role=role, content=content, tool_use=tool_use)
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()

        # Auto-title from first user message
        if self.title == "New Conversation" and role == "user":
            self.title = content[:60] + ("..." if len(content) > 60 else "")

        return msg

    def get_api_messages(self, max_messages: int = 50) -> list:
        """Get messages formatted for the Claude API."""
        recent = self.messages[-max_messages:]
        return [{"role": m.role, "content": m.content} for m in recent]

    def save(self):
        """Save conversation to disk."""
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        filepath = HISTORY_DIR / f"{self.id}.json"
        data = {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [asdict(m) for m in self.messages],
        }
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, conversation_id: str) -> "Conversation":
        """Load a conversation from disk."""
        filepath = HISTORY_DIR / f"{conversation_id}.json"
        with open(filepath) as f:
            data = json.load(f)

        conv = cls(
            id=data["id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
        for m in data["messages"]:
            conv.messages.append(Message(**m))
        return conv

    @classmethod
    def list_all(cls) -> list:
        """List all saved conversations."""
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        conversations = []
        for f in sorted(HISTORY_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                conversations.append({
                    "id": data["id"],
                    "title": data["title"],
                    "updated_at": data["updated_at"],
                    "message_count": len(data["messages"]),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return conversations
