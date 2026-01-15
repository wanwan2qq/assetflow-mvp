"""
LLM-based information extraction for asset and user profile data
Refactored to use DeepSeek/OpenAI instead of brittle regex patterns
"""

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class AssetType(str, Enum):
    """Asset types for extraction"""

    REAL_ESTATE = "real_estate"
    CASH = "cash"
    INVESTMENT = "investment"
    INSURANCE = "insurance"
    LIABILITY = "liability"


class ExtractedAsset(BaseModel):
    """Extracted asset information"""

    asset_type: AssetType
    name: str
    value: float | None = None
    location: str | None = None
    area: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    extracted_from: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ExtractedUserProfile(BaseModel):
    """Extracted user profile information"""

    age_range: str | None = None
    family_structure: str | None = None
    monthly_expense: float | None = None
    risk_preference: str | None = None
    occupation: str | None = None
    income_range: str | None = None
    confidence: float = 0.0
    extracted_from: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class InformationExtractor:
    """LLM-based information extraction service"""

    def __init__(self):
        """Initialize the LLM-based extractor"""
        # Check if we have a valid OpenAI API key
        self.has_real_openai_key = (
            settings.OPENAI_API_KEY
            and not settings.OPENAI_API_KEY.startswith("sk-mock")
            and settings.OPENAI_API_KEY != "mock-key"
        )

        if not self.has_real_openai_key:
            logger.warning(
                "No valid OpenAI API key - extraction will use fallback mode"
            )
            self.llm = None
        else:
            # Initialize LLM for extraction
            llm_kwargs = {
                "model": "deepseek-chat",
                "temperature": 0.1,  # Low temperature for consistent extraction
                "api_key": settings.OPENAI_API_KEY,
            }

            if settings.OPENAI_API_BASE:
                llm_kwargs["base_url"] = settings.OPENAI_API_BASE

            self.llm = ChatOpenAI(**llm_kwargs)

    async def extract_information_from_conversation(
        self, text: str, conversation_history: list[dict] | None = None
    ) -> tuple[list[ExtractedAsset], ExtractedUserProfile | None, dict[str, Any]]:
        """
        Extract structured information from conversational text using LLM

        Args:
            text: User message to extract from
            conversation_history: Optional conversation context

        Returns:
            Tuple of (assets, user_profile, validation_result)
        """
        if not self.llm:
            # Fallback to simple extraction when LLM is not available
            return await self._fallback_extraction(text)

        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(text, conversation_history or [])

            # Get LLM response
            response = await self.llm.ainvoke(prompt)

            # Parse JSON response
            try:
                result = json.loads(response.content)
                logger.info(f"LLM extraction successful: {result}")

                # Convert to ExtractedAsset and ExtractedUserProfile objects
                assets = self._parse_assets(result.get("assets", []), text)
                profile = self._parse_profile(result.get("profile", {}), text)
                intent = result.get("intent", "new_info")

                # Create validation result
                validation = self._create_validation(assets, profile, intent)

                return assets, profile, validation

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                logger.error(f"Response content: {response.content}")
                return await self._fallback_extraction(text)

        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            return await self._fallback_extraction(text)

    def _build_extraction_prompt(
        self, user_message: str, conversation_history: list[dict]
    ) -> str:
        """Build the extraction prompt for the LLM"""

        # Build conversation context
        context_messages = []
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_messages.append(f"{role}: {content}")

        context_str = (
            "\n".join(context_messages) if context_messages else "No previous context"
        )

        prompt = f"""You are an expert financial information extraction system. Extract structured information from user messages about their assets and profile.

**CRITICAL INSTRUCTIONS:**
1. You MUST respond with ONLY valid JSON - no explanations, no markdown, no extra text
2. Be conservative - only extract information you are confident about
3. Handle fuzzy numbers (e.g., "about 500k" -> 500000, "大概50万" -> 500000)
4. Detect correction intent: if user says "No, it's..." or "不是，是..." set intent to "correction"

**CONVERSATION CONTEXT:**
{context_str}

**CURRENT USER MESSAGE:**
{user_message}

**REQUIRED JSON OUTPUT FORMAT:**
{{
    "assets": [
        {{
            "type": "real_estate|cash|investment|insurance|liability",
            "name": "资产名称",
            "value": 500000,
            "location": "位置(如适用)",
            "area": 120.5,
            "metadata": {{"key": "value"}}
        }}
    ],
    "profile": {{
        "age_range": "30-40",
        "family_structure": "married_with_kids",
        "monthly_expense": 15000,
        "risk_preference": "conservative|moderate|aggressive",
        "occupation": "职业",
        "income_range": "收入范围"
    }},
    "intent": "new_info|correction"
}}

**EXTRACTION RULES:**

1. **Assets Extraction:**
   - Extract specific asset mentions with amounts
   - For real estate: extract location, area (平方米), and value
   - For cash: extract amount and account type if mentioned
   - For investments: extract type (股票/基金/etc) and amount
   - For insurance: extract type and coverage amount
   - For liabilities: extract type (房贷/车贷/etc) and amount

2. **Profile Extraction:**
   - age_range: Extract from "X岁", "X-Y岁", "80后/90后" -> "30-40", "40-50", etc.
   - family_structure: "single", "married", "married_with_kids", "divorced", "widowed"
   - monthly_expense: Extract from "月支出", "每月花费", etc.
   - risk_preference: "conservative" (保守/稳健), "moderate" (平衡), "aggressive" (激进/进取)
   - occupation: Extract job title if mentioned
   - income_range: Extract income information if mentioned

3. **Intent Detection:**
   - "new_info": User is providing new information
   - "correction": User is correcting previous information (keywords: "不是", "不对", "应该是", "其实是", "No", "Actually")

4. **Amount Conversion (Chinese):**
   - "50万" -> 500000
   - "100万" -> 1000000
   - "1千万" -> 10000000
   - "1亿" -> 100000000
   - "about 500k" -> 500000
   - "大概50万" -> 500000

5. **Asset Type Mapping (Chinese):**
   - 房产/房子/住房/小区/楼盘 -> "real_estate"
   - 现金/存款/银行/储蓄 -> "cash"
   - 股票/基金/投资/理财 -> "investment"
   - 保险/重疾险/意外险 -> "insurance"
   - 贷款/房贷/车贷/债务 -> "liability"

**IMPORTANT:**
- Only include fields with actual extracted data
- If no assets found, return empty array
- If no profile data found, return empty object
- Always include "intent" field

Respond with ONLY the JSON object:"""

        return prompt

    def _parse_assets(
        self, assets_data: list[dict], extracted_from: str
    ) -> list[ExtractedAsset]:
        """Parse assets from LLM response"""
        assets = []

        for asset_data in assets_data:
            try:
                asset_type = AssetType(asset_data.get("type", "cash"))
                name = asset_data.get("name", f"{asset_type.value}资产")
                value = asset_data.get("value")
                location = asset_data.get("location")
                area = asset_data.get("area")
                metadata = asset_data.get("metadata", {})

                # Add location and area to metadata if present
                if location:
                    metadata["location"] = location
                if area:
                    metadata["area"] = area

                asset = ExtractedAsset(
                    asset_type=asset_type,
                    name=name,
                    value=value,
                    location=location,
                    area=area,
                    metadata=metadata,
                    confidence=0.85,  # High confidence from LLM extraction
                    extracted_from=extracted_from,
                )
                assets.append(asset)

            except Exception as e:
                logger.error(f"Error parsing asset: {e}, data: {asset_data}")
                continue

        return assets

    def _parse_profile(
        self, profile_data: dict, extracted_from: str
    ) -> ExtractedUserProfile | None:
        """Parse user profile from LLM response"""
        if not profile_data or not any(profile_data.values()):
            return None

        try:
            profile = ExtractedUserProfile(
                age_range=profile_data.get("age_range"),
                family_structure=profile_data.get("family_structure"),
                monthly_expense=profile_data.get("monthly_expense"),
                risk_preference=profile_data.get("risk_preference"),
                occupation=profile_data.get("occupation"),
                income_range=profile_data.get("income_range"),
                confidence=0.80,  # High confidence from LLM extraction
                extracted_from=extracted_from,
            )
            return profile

        except Exception as e:
            logger.error(f"Error parsing profile: {e}, data: {profile_data}")
            return None

    def _create_validation(
        self,
        assets: list[ExtractedAsset],
        profile: ExtractedUserProfile | None,
        intent: str,
    ) -> dict[str, Any]:
        """Create validation result"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "suggestions": [],
            "completeness_score": 0.0,
            "intent": intent,
        }

        # Validate assets
        if not assets:
            validation_result["warnings"].append("未检测到任何资产信息")
            validation_result["suggestions"].append(
                "请提供更详细的资产信息，如房产位置、面积、价值等"
            )
        else:
            # Check asset completeness
            complete_assets = 0
            for asset in assets:
                if asset.value and asset.confidence > 0.5:
                    complete_assets += 1

            if complete_assets == 0:
                validation_result["warnings"].append("资产信息不够完整")
                validation_result["suggestions"].append("请提供具体的资产价值信息")

        # Validate profile
        if not profile:
            validation_result["warnings"].append("未检测到用户画像信息")
            validation_result["suggestions"].append(
                "请提供年龄、家庭结构等基本信息以获得更准确的建议"
            )

        # Calculate completeness score
        score_components = []

        # Asset completeness (40%)
        if assets:
            asset_score = min(len(assets) / 3.0, 1.0) * 0.4  # Up to 3 asset types
            score_components.append(asset_score)

        # Profile completeness (60%)
        if profile:
            profile_fields = [
                profile.age_range,
                profile.family_structure,
                profile.monthly_expense,
                profile.risk_preference,
            ]
            filled_fields = sum(1 for field in profile_fields if field is not None)
            profile_score = (filled_fields / len(profile_fields)) * 0.6
            score_components.append(profile_score)

        validation_result["completeness_score"] = sum(score_components)

        if validation_result["completeness_score"] < 0.3:
            validation_result["is_valid"] = False

        return validation_result

    async def _fallback_extraction(
        self, text: str
    ) -> tuple[list[ExtractedAsset], ExtractedUserProfile | None, dict[str, Any]]:
        """Fallback extraction using simple keyword matching when LLM is not available"""
        logger.info("Using fallback extraction (no LLM available)")

        assets = []
        profile_data = {}

        # Simple keyword-based extraction for development/testing
        text_lower = text.lower()

        # Extract real estate mentions
        if any(
            keyword in text
            for keyword in ["房产", "房子", "住房", "小区", "楼盘", "公寓"]
        ):
            assets.append(
                ExtractedAsset(
                    asset_type=AssetType.REAL_ESTATE,
                    name="房产",
                    value=None,
                    confidence=0.3,
                    extracted_from=text,
                )
            )

        # Extract cash mentions
        if any(keyword in text for keyword in ["现金", "存款", "银行", "储蓄"]):
            assets.append(
                ExtractedAsset(
                    asset_type=AssetType.CASH,
                    name="现金",
                    value=None,
                    confidence=0.3,
                    extracted_from=text,
                )
            )

        # Extract investment mentions
        if any(keyword in text for keyword in ["股票", "基金", "投资", "理财"]):
            assets.append(
                ExtractedAsset(
                    asset_type=AssetType.INVESTMENT,
                    name="投资",
                    value=None,
                    confidence=0.3,
                    extracted_from=text,
                )
            )

        # Simple profile extraction
        if any(keyword in text for keyword in ["保守", "稳健", "安全"]):
            profile_data["risk_preference"] = "conservative"
        elif any(keyword in text for keyword in ["激进", "高风险", "进取"]):
            profile_data["risk_preference"] = "aggressive"

        profile = (
            ExtractedUserProfile(
                **profile_data, confidence=0.3, extracted_from=text
            )
            if profile_data
            else None
        )

        validation = self._create_validation(assets, profile, "new_info")

        return assets, profile, validation


# Global extractor instance
information_extractor = InformationExtractor()


def extract_information_from_conversation(
    text: str,
) -> tuple[list[ExtractedAsset], ExtractedUserProfile | None, dict[str, Any]]:
    """
    Synchronous wrapper for backward compatibility
    Extract structured information from conversational text

    Returns:
        Tuple of (assets, user_profile, validation_result)
    """
    import asyncio

    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a new thread to run the async code
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                asyncio.run,
                information_extractor.extract_information_from_conversation(text)
            )
            return future.result()
    except RuntimeError:
        # No running loop, we can use run_until_complete
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            information_extractor.extract_information_from_conversation(text)
        )


async def extract_information(user_message: str, current_history: list) -> dict:
    """
    Phase 2: LLM-based information extraction for automatic state sync.

    Args:
        user_message: The user's current message
        current_history: List of previous conversation messages

    Returns:
        dict: Structured extraction result with assets, goals, risk_profile, and completeness_update
    """
    try:
        # Use the new LLM-based extractor
        assets, profile, validation = await information_extractor.extract_information_from_conversation(
            user_message, current_history
        )

        # Convert to Phase 2 format
        result = {
            "assets": [],
            "goals": [],
            "risk_profile": {},
            "completeness_update": {},
            "intent": validation.get("intent", "new_info"),
        }

        # Convert assets
        for asset in assets:
            asset_data = {
                "type": asset.asset_type.value,
                "amount": asset.value or 0,
                "currency": "CNY",
                "name": asset.name,
            }

            if asset.location:
                asset_data["location"] = asset.location
            if asset.area:
                asset_data["area"] = asset.area
            if asset.metadata:
                asset_data["metadata"] = asset.metadata

            result["assets"].append(asset_data)

            # Mark completeness
            result["completeness_update"][asset.asset_type.value] = True

        # Convert profile - FIXED: Include ALL profile fields
        if profile:
            if profile.risk_preference:
                result["risk_profile"]["tolerance"] = profile.risk_preference
            if profile.age_range:
                result["risk_profile"]["age_range"] = profile.age_range
            if profile.family_structure:
                result["risk_profile"]["family_structure"] = profile.family_structure
            if profile.monthly_expense:
                result["risk_profile"]["monthly_expense"] = profile.monthly_expense
            # FIXED: Add occupation and income_range to risk_profile
            if profile.occupation:
                result["risk_profile"]["occupation"] = profile.occupation
            if profile.income_range:
                result["risk_profile"]["income_range"] = profile.income_range

            # Extract goals from profile (simple heuristics)
            if profile.age_range:
                age_start = int(profile.age_range.split("-")[0]) if "-" in profile.age_range else 30
                if age_start < 35:
                    result["goals"].append("buy_house")
                if age_start > 40:
                    result["goals"].append("retirement")
            if profile.family_structure == "married_with_kids":
                result["goals"].append("education")

        logger.info(f"LLM extraction result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in extract_information: {e}")
        # Return empty result on error
        return {
            "assets": [],
            "goals": [],
            "risk_profile": {},
            "completeness_update": {},
            "intent": "new_info",
        }
