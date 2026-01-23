"""
Conversation Context Data Structures

This module defines the unified data structures for managing
conversation context throughout the chat system.

AI Coding Guidance:
- Use ConversationContext as the single source of truth for context data
- Don't create ad-hoc dict structures for context; use these classes
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ConversationContext(BaseModel):
    """
    Unified conversation context data structure.
    
    This replaces the scattered context dicts in the original ChatAgent,
    providing a consistent interface for context management.
    
    Layers:
    - L1: User/Asset/Profile (from database)
    - L2: Cognition State (from UserCognition)
    - L3: Vector Memory (from RAG retrieval)
    """
    
    user_id: int
    session_id: str | None = None
    
    # Conversation history (most recent N messages)
    conversation_history: list[dict[str, str]] = Field(default_factory=list)
    
    # L1: User profile (from UserProfile table)
    user_profile: dict[str, Any] | None = None
    
    # L1: Extracted assets (from UserAsset table)
    extracted_assets: list[dict[str, Any]] = Field(default_factory=list)
    
    # L1: Detailed real estate assets (from RealEstateAsset table)
    real_estate_assets: list[dict[str, Any]] = Field(default_factory=list)
    
    # L2: Cognition state (from UserCognition table)
    cognition: dict[str, Any] | None = None
    
    # Current conversation stage
    current_stage: str = "initial"  # initial, property_collection, asset_collection, analysis
    
    # L3: Retrieved relevant memories (from VectorMemory)
    relevant_memories: list[str] = Field(default_factory=list)
    
    # Portfolio analysis results (cached)
    portfolio_analysis: dict[str, Any] | None = None
    
    # Timestamps for cache management
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.utcnow()
    
    def get_recent_messages(self, limit: int = 10) -> list[dict[str, str]]:
        """Get the most recent N messages."""
        return self.conversation_history[-limit:]
    
    def update_stage(self, completeness_score: float) -> None:
        """Update conversation stage based on completeness score."""
        if completeness_score < 0.3:
            self.current_stage = "initial"
        elif completeness_score < 0.6:
            self.current_stage = "property_collection"
        elif completeness_score < 0.8:
            self.current_stage = "asset_collection"
        else:
            self.current_stage = "analysis"
        self.updated_at = datetime.utcnow()
    
    def to_prompt_context(self) -> dict[str, Any]:
        """
        Convert context to format suitable for LLM prompt.
        
        This is the standardized format used when building prompts.
        """
        return {
            "user_id": self.user_id,
            "stage": self.current_stage,
            "profile": self.user_profile,
            "assets": self.extracted_assets,
            "cognition": self.cognition,
            "memories": self.relevant_memories,
            "recent_messages": self.get_recent_messages(10),
        }


class ContextUpdate(BaseModel):
    """
    Represents an update to be applied to ConversationContext.
    
    Used by ContextManager to batch updates efficiently.
    """
    
    # Assets to add/update
    assets: list[dict[str, Any]] | None = None
    
    # Profile fields to update
    profile_updates: dict[str, Any] | None = None
    
    # Cognition fields to update
    cognition_updates: dict[str, Any] | None = None
    
    # New stage value
    new_stage: str | None = None
    
    # Portfolio analysis to cache
    portfolio_analysis: dict[str, Any] | None = None
