from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field

class IntentType(str, Enum):
    """Types of user intents in conversation."""
    INFO_COLLECTION = "info_collection"   # Providing asset/profile info
    POLICY_QUERY = "policy_query"         # Asking about policies/rules
    ADVISORY = "advisory"                 # Asking for advice/analysis
    CHIT_CHAT = "chit_chat"               # General chat/confirmation
    ACTION_REQUEST = "action_request"     # Explicit action requests

class IntentResult(BaseModel):
    """Result of intent classification."""
    intent_type: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
