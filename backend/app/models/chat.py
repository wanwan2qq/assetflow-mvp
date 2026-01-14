"""
Chat session data models
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Text
from sqlmodel import Field, SQLModel


class MessageRole(str, Enum):
    USER = "user"
    AI = "ai"


class ChatMessage(SQLModel, table=True):
    """Individual chat messages for conversation history"""
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: MessageRole = Field(index=True)  # user or ai
    content: str = Field(sa_type=Text)  # Full message content including widget tags
    meta_data: dict | None = Field(sa_type=JSON, default=None)  # Widget data and other metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)


class ChatSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    session_data: dict = Field(sa_type=JSON)  # 存储对话上下文
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
