"""
Wealth Management Data Models
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

class FlowType(str, Enum):
    """Type of cash flow"""
    INCOME = "income"
    EXPENSE = "expense"

class Frequency(str, Enum):
    """Frequency of cash flow"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ONCE = "once"

class CashFlowItem(SQLModel, table=True):
    """
    Represents an income or expense item.
    Can be recurring or one-time.
    Can be linked to a specific asset (e.g., rental income from property, mortgage payment for property).
    """
    __tablename__ = "cash_flow_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(min_length=1, max_length=200)
    amount: float = Field(ge=0)
    flow_type: FlowType
    frequency: Frequency
    is_recurring: bool = Field(default=True)
    recurrence_day: Optional[int] = Field(default=None, ge=1, le=31, description="Day of month for recurring items")
    
    # Optional link to an asset (e.g., this expense is the mortgage for asset X)
    related_asset_id: Optional[int] = Field(default=None, foreign_key="userasset.id")
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AssetValuationHistory(SQLModel, table=True):
    """
    Tracks the valuation history of an asset over time.
    """
    __tablename__ = "asset_valuation_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    asset_id: int = Field(foreign_key="userasset.id", index=True)
    date: datetime = Field(default_factory=datetime.utcnow, index=True)
    value: float
    source: str = Field(default="system", description="Source of valuation: user, ai, market_update, etc.")
    
class WealthHistory(SQLModel, table=True):
    """
    Daily/Weekly snapshot of user's total wealth.
    """
    __tablename__ = "wealth_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    date: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    total_assets: float = Field(default=0.0)
    total_liabilities: float = Field(default=0.0)
    net_worth: float = Field(default=0.0)
