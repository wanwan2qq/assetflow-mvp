"""
User interaction tracking models
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class InteractionType(str, Enum):
    """Types of user interactions with commercial products"""

    VIEW = "view"
    CLICK = "click"
    CONTACT = "contact"
    DISMISS = "dismiss"
    SHARE = "share"


class UserInteraction(SQLModel, table=True):
    """Model for tracking user interactions with commercial products"""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    product_id: int = Field(foreign_key="commercialproduct.id", index=True)
    interaction_type: InteractionType = Field(index=True)
    interaction_metadata: dict = Field(
        sa_type=JSON, default={}
    )  # Additional interaction data
    session_id: str | None = Field(default=None, index=True)  # Chat session context
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    class Config:
        """Pydantic configuration"""

        use_enum_values = True
