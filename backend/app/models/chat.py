"""
Chat session data models
"""

from datetime import datetime

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class ChatSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    session_data: dict = Field(sa_type=JSON)  # 存储对话上下文
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
