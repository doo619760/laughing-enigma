"""Configuration management for the AI Assistant."""

import json
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict


DEFAULT_MODEL = "claude-sonnet-4-6"
APP_DIR = Path.home() / ".ai_assistant"
CONFIG_FILE = APP_DIR / "config.json"
HISTORY_DIR = APP_DIR / "conversations"
TASKS_FILE = APP_DIR / "tasks.json"


@dataclass
class Config:
    """Application configuration."""

    api_key: str = ""
    model: str = DEFAULT_MODEL
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str = (
        "You are a super helpful AI assistant. You are friendly, thorough, and "
        "proactive. You anticipate what the user might need and provide clear, "
        "actionable answers. When helping with code, you explain your reasoning. "
        "When helping with tasks, you break things down into manageable steps. "
        "You use markdown formatting for clarity. You are honest about what you "
        "don't know and suggest alternatives when you can't help directly."
    )
    max_history_messages: int = 50
    stream_responses: bool = True
    save_conversations: bool = True

    @classmethod
    def load(cls) -> "Config":
        """Load config from disk, creating defaults if needed."""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)

        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

        # Check environment variable for API key
        config = cls(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        config.save()
        return config

    def save(self):
        """Persist config to disk."""
        APP_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(asdict(self), f, indent=2)
