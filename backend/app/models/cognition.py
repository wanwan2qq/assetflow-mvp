"""
User cognition and state management models
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class UserCognition(SQLModel, table=True):
    """
    User cognition model for tracking information collection state and AI insights.
    This model implements L2 layer state management to prevent repetitive questioning.
    """
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True, index=True)
    
    # Financial goals (JSON list)
    financial_goals: list[str] | None = Field(
        sa_type=JSON, 
        default=None,
        description="User's financial goals like ['retirement', 'buy_house', 'education']"
    )
    
    # Risk profile (JSON dict)
    risk_profile: dict | None = Field(
        sa_type=JSON,
        default=None,
        description="Risk assessment like {'tolerance': 'low', 'anxiety': 'high', 'experience': 'beginner'}"
    )
    
    # Collection status tracking (JSON dict)
    collection_status: dict | None = Field(
        sa_type=JSON,
        default=None,
        description="Asset collection state like {'real_estate': true, 'cash': false, 'investment': true}"
    )
    
    # AI's internal summary and notes
    advisor_note: str | None = Field(
        default=None,
        max_length=2000,
        description="AI advisor's internal summary of the user's situation and preferences"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def get_collection_status(self, asset_type: str) -> bool:
        """Get collection status for a specific asset type"""
        if not self.collection_status:
            return False
        return self.collection_status.get(asset_type, False)
    
    def set_collection_status(self, asset_type: str, collected: bool) -> None:
        """Set collection status for a specific asset type"""
        if not self.collection_status:
            self.collection_status = {}
        self.collection_status[asset_type] = collected
        self.updated_at = datetime.utcnow()
    
    def add_financial_goal(self, goal: str) -> None:
        """Add a financial goal if not already present"""
        if not self.financial_goals:
            self.financial_goals = []
        if goal not in self.financial_goals:
            self.financial_goals.append(goal)
            self.updated_at = datetime.utcnow()
    
    def update_risk_profile(self, key: str, value: str) -> None:
        """Update a specific aspect of risk profile"""
        if not self.risk_profile:
            self.risk_profile = {}
        self.risk_profile[key] = value
        self.updated_at = datetime.utcnow()