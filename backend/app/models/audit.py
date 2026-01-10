"""
Audit trail models for tracking data changes
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlmodel import JSON, Column, DateTime, Field, SQLModel


class AuditAction(str, Enum):
    """Audit action types"""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class AuditLog(SQLModel, table=True):
    """Audit log for tracking all data changes"""

    id: int | None = Field(default=None, primary_key=True)

    # What was changed
    table_name: str = Field(
        max_length=100, description="Name of the table that was modified"
    )
    record_id: int = Field(description="ID of the record that was modified")
    action: AuditAction = Field(description="Type of action performed")

    # Who made the change
    user_id: int | None = Field(
        default=None, description="ID of user who made the change"
    )
    user_type: str = Field(
        max_length=50, default="user", description="Type of user (user, system, admin)"
    )

    # When the change was made
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="When the change was made",
    )

    # What changed
    old_values: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Previous values before change",
    )
    new_values: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON), description="New values after change"
    )

    # Additional context
    ip_address: str | None = Field(
        default=None, max_length=45, description="IP address of the client"
    )
    user_agent: str | None = Field(
        default=None, max_length=500, description="User agent string"
    )
    session_id: str | None = Field(
        default=None, max_length=100, description="Session identifier"
    )

    # Extra metadata
    extra_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional metadata about the change",
    )

    class Config:
        """Pydantic configuration"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class UserAssetHistory(SQLModel, table=True):
    """Historical record of user asset changes for detailed tracking"""

    id: int | None = Field(default=None, primary_key=True)

    # Reference to the asset
    asset_id: int = Field(foreign_key="userasset.id", description="ID of the asset")
    user_id: int = Field(
        foreign_key="user.id", description="ID of the user who owns the asset"
    )

    # Historical values
    asset_type: str = Field(
        max_length=50, description="Type of asset at this point in time"
    )
    name: str = Field(max_length=200, description="Name of asset at this point in time")
    value: float = Field(description="Value of asset at this point in time")
    is_confirmed: bool = Field(description="Confirmation status at this point in time")
    extra_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Extra data at this point in time",
    )

    # Change tracking
    change_reason: str | None = Field(
        default=None, max_length=500, description="Reason for the change"
    )
    changed_by: int | None = Field(
        default=None, description="User ID who made the change"
    )
    changed_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="When this version was created",
    )

    # Validation
    is_valid_from: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="When this version became valid",
    )
    is_valid_to: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime),
        description="When this version became invalid (null = current)",
    )

    class Config:
        """Pydantic configuration"""

        json_encoders = {datetime: lambda v: v.isoformat()}
