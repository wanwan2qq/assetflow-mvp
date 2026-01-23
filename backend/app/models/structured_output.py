"""
Structured Output Models for LLM Extraction

This module defines Pydantic models for validating and parsing
LLM extraction outputs. Using structured response models improves:
1. Type safety and validation
2. Robust JSON parsing with fallbacks
3. Clear error messages when parsing fails

AI Coding Guidance:
- Use these models for all LLM extraction outputs
- Don't accept raw dicts; parse into these models first
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Asset Extraction Models
# ============================================================================

class AssetTypeEnum(str, Enum):
    """Asset types for extraction."""
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    INVESTMENT = "investment"
    INSURANCE = "insurance"
    LIABILITY = "liability"
    OTHER = "other"


class ExtractedAssetOutput(BaseModel):
    """Structured output for a single extracted asset."""
    
    asset_type: AssetTypeEnum = Field(
        default=AssetTypeEnum.OTHER,
        description="Type of asset"
    )
    name: str = Field(
        default="未知资产",
        description="Name or description of the asset"
    )
    value: float | None = Field(
        default=None,
        description="Estimated value in CNY"
    )
    location: str | None = Field(
        default=None,
        description="Location (for real estate)"
    )
    area: float | None = Field(
        default=None,
        description="Area in square meters (for real estate)"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score 0-1"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    @field_validator('asset_type', mode='before')
    @classmethod
    def validate_asset_type(cls, v):
        """Convert string to enum, fallback to OTHER."""
        if isinstance(v, AssetTypeEnum):
            return v
        if isinstance(v, str):
            try:
                return AssetTypeEnum(v)
            except ValueError:
                return AssetTypeEnum.OTHER
        return AssetTypeEnum.OTHER
    
    @field_validator('value', mode='before')
    @classmethod
    def validate_value(cls, v):
        """Convert various value formats to float."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            # Handle Chinese number formats like "20万"
            v = v.strip()
            multiplier = 1
            if "万" in v:
                multiplier = 10000
                v = v.replace("万", "")
            elif "亿" in v:
                multiplier = 100000000
                v = v.replace("亿", "")
            try:
                return float(v) * multiplier
            except ValueError:
                return None
        return None


class AssetExtractionOutput(BaseModel):
    """Structured output for asset extraction."""
    
    assets: list[ExtractedAssetOutput] = Field(
        default_factory=list,
        description="List of extracted assets"
    )
    
    @classmethod
    def from_raw(cls, raw: dict | list | None) -> "AssetExtractionOutput":
        """Parse raw LLM output into structured model with fallbacks."""
        if raw is None:
            return cls()
        
        if isinstance(raw, list):
            assets = []
            for item in raw:
                if isinstance(item, dict):
                    try:
                        assets.append(ExtractedAssetOutput(**item))
                    except Exception:
                        # Skip invalid items
                        continue
            return cls(assets=assets)
        
        if isinstance(raw, dict):
            if "assets" in raw:
                return cls.from_raw(raw["assets"])
            # Try treating the dict as a single asset
            try:
                return cls(assets=[ExtractedAssetOutput(**raw)])
            except Exception:
                return cls()
        
        return cls()


# ============================================================================
# Profile Extraction Models
# ============================================================================

class RiskPreferenceEnum(str, Enum):
    """Risk preference levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class FamilyStructureEnum(str, Enum):
    """Family structure types."""
    SINGLE = "single"
    MARRIED = "married"
    MARRIED_WITH_KIDS = "married_with_kids"


class ExtractedProfileOutput(BaseModel):
    """Structured output for extracted user profile."""
    
    age_range: str | None = Field(
        default=None,
        description="Age range like '30-40'"
    )
    family_structure: str | None = Field(
        default=None,
        description="Family structure"
    )
    occupation: str | None = Field(
        default=None,
        description="User's occupation"
    )
    income_range: str | None = Field(
        default=None,
        description="Annual income range"
    )
    monthly_expense: float | None = Field(
        default=None,
        description="Monthly expense in CNY"
    )
    risk_preference: str | None = Field(
        default=None,
        description="Risk preference level"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score 0-1"
    )
    
    @field_validator('monthly_expense', mode='before')
    @classmethod
    def validate_expense(cls, v):
        """Convert various expense formats to float."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, str):
            v = v.strip()
            multiplier = 1
            if "万" in v:
                multiplier = 10000
                v = v.replace("万", "")
            try:
                return float(v) * multiplier
            except ValueError:
                return None
        return None
    
    def is_empty(self) -> bool:
        """Check if profile has any meaningful data."""
        return all([
            self.age_range is None,
            self.family_structure is None,
            self.occupation is None,
            self.income_range is None,
            self.monthly_expense is None,
            self.risk_preference is None,
        ])
    
    @classmethod
    def from_raw(cls, raw: dict | None) -> "ExtractedProfileOutput":
        """Parse raw LLM output into structured model."""
        if raw is None or not isinstance(raw, dict):
            return cls()
        
        # Handle nested "profile" key
        if "profile" in raw:
            raw = raw["profile"]
        
        try:
            return cls(**raw)
        except Exception:
            return cls()


# ============================================================================
# Combined Extraction Result
# ============================================================================

class ExtractionResultOutput(BaseModel):
    """Combined extraction result for all extracted information."""
    
    assets: list[ExtractedAssetOutput] = Field(
        default_factory=list,
        description="Extracted assets"
    )
    risk_profile: dict[str, Any] = Field(
        default_factory=dict,
        description="Risk profile and user info"
    )
    goals: list[str] = Field(
        default_factory=list,
        description="Identified financial goals"
    )
    completeness_update: dict[str, bool] = Field(
        default_factory=dict,
        description="What information was collected"
    )
    intent: str = Field(
        default="new_info",
        description="Detected user intent"
    )
    
    @classmethod
    def from_raw(cls, raw: dict | None) -> "ExtractionResultOutput":
        """Parse raw extraction result into structured model."""
        if raw is None or not isinstance(raw, dict):
            return cls()
        
        try:
            # Parse assets
            assets_raw = raw.get("assets", [])
            assets = []
            if isinstance(assets_raw, list):
                for item in assets_raw:
                    if isinstance(item, dict):
                        try:
                            assets.append(ExtractedAssetOutput(**item))
                        except Exception:
                            continue
            
            return cls(
                assets=assets,
                risk_profile=raw.get("risk_profile", {}),
                goals=raw.get("goals", []),
                completeness_update=raw.get("completeness_update", {}),
                intent=raw.get("intent", "new_info"),
            )
        except Exception:
            return cls()
    
    def to_dict(self) -> dict:
        """Convert to dict format for asset_extraction_service."""
        return {
            "assets": [
                {
                    "type": asset.asset_type.value,
                    "amount": asset.value or 0,
                    "currency": "CNY",
                    "name": asset.name,
                    "location": asset.location,
                    "area": asset.area,
                    "metadata": asset.metadata,
                }
                for asset in self.assets
            ],
            "risk_profile": self.risk_profile,
            "goals": self.goals,
            "completeness_update": self.completeness_update,
            "intent": self.intent,
        }
    
    def has_meaningful_data(self) -> bool:
        """Check if any meaningful data was extracted."""
        return bool(self.assets) or bool(self.risk_profile)


# ============================================================================
# JSON Parsing Utilities
# ============================================================================

def parse_json_safely(text: str) -> dict | None:
    """
    Safely parse JSON from LLM output with multiple fallback strategies.
    
    Args:
        text: Raw text that may contain JSON
        
    Returns:
        Parsed dict or None if parsing fails
    """
    import json
    import re
    
    if not text or not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Strategy 1: Direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code block ```json ... ```
    json_block_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Extract from any code block ``` ... ```
    code_block_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Find JSON object in text { ... }
    json_obj_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_obj_match:
        try:
            return json.loads(json_obj_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Strategy 5: Find JSON array in text [ ... ]
    json_arr_match = re.search(r'\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', text, re.DOTALL)
    if json_arr_match:
        try:
            return json.loads(json_arr_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return None


def parse_extraction_output(raw_text: str) -> ExtractionResultOutput:
    """
    Parse raw LLM extraction output into structured model.
    
    This is the main entry point for parsing extraction results.
    
    Args:
        raw_text: Raw LLM output text
        
    Returns:
        ExtractionResultOutput with validated data
    """
    parsed = parse_json_safely(raw_text)
    return ExtractionResultOutput.from_raw(parsed)
