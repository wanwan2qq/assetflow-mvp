"""
LLM-based information extraction for asset and user profile data
Refactored to use modular prompts and configuration-driven approach
Enhanced with Standard & Poor's 4-quadrant model support
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
    """LLM-based information extraction service with modular prompt architecture"""

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
        Extract structured information from conversational text using modular LLM prompts

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
            # Extract assets, profile, and intent in parallel using specialized prompts
            assets = await self._extract_assets(text, conversation_history or [])
            profile = await self._extract_profile(text, conversation_history or [])
            intent_data = await self._detect_intent(text, conversation_history or [])

            # Create validation result
            validation = self._create_validation(assets, profile, intent_data.get("primary_intent", "new_info"))

            return assets, profile, validation

        except Exception as e:
            logger.error(f"Error in modular LLM extraction: {e}")
            return await self._fallback_extraction(text)

    async def _extract_assets(
        self, user_message: str, conversation_history: list[dict]
    ) -> list[ExtractedAsset]:
        """Extract assets using specialized asset extraction prompt with enhanced error handling"""
        try:
            prompt = self._build_asset_extraction_prompt(user_message, conversation_history)
            response = await self.llm.ainvoke(prompt)
            
            # Enhanced response validation
            if not response or not response.content:
                logger.warning("Asset extraction: Empty response from LLM")
                return []
            
            response_content = response.content.strip()
            if not response_content:
                logger.warning("Asset extraction: Empty content after strip")
                return []
            
            # Try to clean up response if it contains markdown code blocks
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    response_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    response_content = response_content[json_start:json_end].strip()
            
            # Parse JSON with better error handling
            try:
                result = json.loads(response_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Asset extraction JSON parse error: {json_err}")
                logger.error(f"Raw response content: {response_content[:200]}...")
                
                # Fallback: try to extract assets using regex patterns
                logger.info("Attempting fallback asset extraction using regex patterns")
                return self._fallback_asset_extraction(user_message)
            
            assets = self._parse_assets(result.get("assets", []), user_message)
            
            logger.info(f"Asset extraction successful: {len(assets)} assets found")
            return assets
            
        except Exception as e:
            logger.error(f"Error in asset extraction: {e}")
            logger.error(f"Attempting fallback asset extraction")
            return self._fallback_asset_extraction(user_message)

    async def _extract_profile(
        self, user_message: str, conversation_history: list[dict]
    ) -> ExtractedUserProfile | None:
        """Extract user profile using specialized profile extraction prompt with enhanced error handling"""
        try:
            prompt = self._build_profile_extraction_prompt(user_message, conversation_history)
            response = await self.llm.ainvoke(prompt)
            
            # Enhanced response validation
            if not response or not response.content:
                logger.warning("Profile extraction: Empty response from LLM")
                return None
            
            response_content = response.content.strip()
            if not response_content:
                logger.warning("Profile extraction: Empty content after strip")
                return None
            
            # Try to clean up response if it contains markdown code blocks
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    response_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    response_content = response_content[json_start:json_end].strip()
            
            # Parse JSON with better error handling
            try:
                result = json.loads(response_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Profile extraction JSON parse error: {json_err}")
                logger.error(f"Raw response content: {response_content[:200]}...")
                
                # Fallback: try to extract profile using regex patterns
                logger.info("Attempting fallback profile extraction using regex patterns")
                return self._fallback_profile_extraction(user_message)
            
            profile = self._parse_profile(result.get("profile", {}), user_message)
            
            logger.info(f"Profile extraction successful: {profile is not None}")
            return profile
            
        except Exception as e:
            logger.error(f"Error in profile extraction: {e}")
            logger.error(f"Attempting fallback profile extraction")
            return self._fallback_profile_extraction(user_message)

    async def _detect_intent(
        self, user_message: str, conversation_history: list[dict]
    ) -> dict[str, Any]:
        """Detect user intent using specialized intent detection prompt with enhanced error handling"""
        try:
            prompt = self._build_intent_detection_prompt(user_message, conversation_history)
            response = await self.llm.ainvoke(prompt)
            
            # Enhanced response validation
            if not response or not response.content:
                logger.warning("Intent detection: Empty response from LLM")
                return {"primary_intent": "new_info", "confidence": 0.5}
            
            response_content = response.content.strip()
            if not response_content:
                logger.warning("Intent detection: Empty content after strip")
                return {"primary_intent": "new_info", "confidence": 0.5}
            
            # Try to clean up response if it contains markdown code blocks
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    response_content = response_content[json_start:json_end].strip()
            elif "```" in response_content:
                json_start = response_content.find("```") + 3
                json_end = response_content.find("```", json_start)
                if json_end > json_start:
                    response_content = response_content[json_start:json_end].strip()
            
            # Parse JSON with better error handling
            try:
                result = json.loads(response_content)
            except json.JSONDecodeError as json_err:
                logger.error(f"Intent detection JSON parse error: {json_err}")
                logger.error(f"Raw response content: {response_content[:200]}...")
                
                # Fallback: simple intent detection
                return self._fallback_intent_detection(user_message)
            
            intent_data = result.get("intent", {})
            
            logger.info(f"Intent detection successful: {intent_data.get('primary_intent', 'unknown')}")
            return intent_data
            
        except Exception as e:
            logger.error(f"Error in intent detection: {e}")
            return self._fallback_intent_detection(user_message)

    def _build_asset_extraction_prompt(
        self, user_message: str, conversation_history: list[dict]
    ) -> str:
        """Build the asset extraction prompt"""
        from app.core.prompt_manager import prompt_manager

        # Build conversation context
        context_str = self._build_context_string(conversation_history)

        # Load system instruction from modular prompt
        system_instruction = prompt_manager.render(
            category="extraction",
            filename="asset_extraction",
            key="system_instruction"
        )

        # Load and render user instruction with variables
        user_instruction = prompt_manager.render(
            category="extraction",
            filename="asset_extraction",
            key="user_instruction",
            context_str=context_str,
            user_message=user_message
        )

        return f"{system_instruction}\n\n{user_instruction}"

    def _build_profile_extraction_prompt(
        self, user_message: str, conversation_history: list[dict]
    ) -> str:
        """Build the profile extraction prompt"""
        from app.core.prompt_manager import prompt_manager

        # Build conversation context
        context_str = self._build_context_string(conversation_history)

        # Load system instruction from modular prompt
        system_instruction = prompt_manager.render(
            category="extraction",
            filename="profile_extraction",
            key="system_instruction"
        )

        # Load and render user instruction with variables
        user_instruction = prompt_manager.render(
            category="extraction",
            filename="profile_extraction",
            key="user_instruction",
            context_str=context_str,
            user_message=user_message
        )

        return f"{system_instruction}\n\n{user_instruction}"

    def _build_intent_detection_prompt(
        self, user_message: str, conversation_history: list[dict]
    ) -> str:
        """Build the intent detection prompt"""
        from app.core.prompt_manager import prompt_manager

        # Build conversation context
        context_str = self._build_context_string(conversation_history)

        # Load system instruction from modular prompt
        system_instruction = prompt_manager.render(
            category="extraction",
            filename="intent_detection",
            key="system_instruction"
        )

        # Load and render user instruction with variables
        user_instruction = prompt_manager.render(
            category="extraction",
            filename="intent_detection",
            key="user_instruction",
            context_str=context_str,
            user_message=user_message
        )

        return f"{system_instruction}\n\n{user_instruction}"

    def _build_context_string(self, conversation_history: list[dict]) -> str:
        """Build conversation context string from history"""
        context_messages = []
        for msg in conversation_history[-5:]:  # Last 5 messages for context
            role = msg.get("role", "user")
            content = msg.get("content", "")
            context_messages.append(f"{role}: {content}")

        return "\n".join(context_messages) if context_messages else "No previous context"

    def _parse_assets(
        self, assets_data: list[dict], extracted_from: str
    ) -> list[ExtractedAsset]:
        """Parse assets from LLM response with enhanced SP quadrant support"""
        from app.core.prompt_manager import prompt_manager
        
        assets = []
        
        # Load SP quadrant configuration for enhanced parsing
        try:
            sp_config = prompt_manager.get_sp_quadrant_config()
        except Exception as e:
            logger.warning(f"Could not load SP quadrant config: {e}")
            sp_config = {}

        for asset_data in assets_data:
            try:
                asset_type = AssetType(asset_data.get("type", "cash"))
                name = asset_data.get("name", f"{asset_type.value}资产")
                value = asset_data.get("value")
                location = asset_data.get("location")
                area = asset_data.get("area")
                metadata = asset_data.get("metadata", {})

                # Enhanced metadata processing with SP quadrant classification
                if asset_type == AssetType.INVESTMENT:
                    subtype = metadata.get("subtype")
                    risk_level = metadata.get("risk_level")
                    
                    # Classify into SP quadrant if possible
                    quadrant = self._classify_sp_quadrant(subtype, risk_level, sp_config)
                    if quadrant:
                        metadata["sp_quadrant"] = quadrant

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

    def _classify_sp_quadrant(
        self, subtype: str, risk_level: str, sp_config: dict
    ) -> str | None:
        """Classify asset into Standard & Poor's 4-quadrant model"""
        if not subtype or not risk_level or not sp_config:
            return None
        
        quadrants = sp_config.get("quadrants", {})
        
        # Check each quadrant for matching asset types
        for quadrant_name, quadrant_data in quadrants.items():
            asset_types = quadrant_data.get("asset_types", [])
            for asset_type in asset_types:
                if (asset_type.get("subtype") == subtype and 
                    asset_type.get("risk_level") == risk_level):
                    return quadrant_name
        
        return None

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

        # Enhanced profile extraction for fallback mode
        logger.info("Extracting user profile information in fallback mode")
        
        # Age range extraction
        import re
        age_patterns = [
            (r'(\d{2})\s*岁', lambda m: self._map_age_to_range(int(m.group(1)))),
            (r'今年\s*(\d{2})', lambda m: self._map_age_to_range(int(m.group(1)))),
            (r'(\d{2})\s*年', lambda m: self._map_age_to_range(int(m.group(1)))),
        ]
        
        for pattern, mapper in age_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    profile_data["age_range"] = mapper(match)
                    logger.info(f"Extracted age_range: {profile_data['age_range']}")
                    break
                except (ValueError, IndexError):
                    continue

        # Family structure extraction
        family_keywords = {
            "single": ["单身", "未婚", "一个人"],
            "married": ["已婚", "结婚", "夫妻", "老公", "老婆", "丈夫", "妻子"],
            "married_with_kids": ["孩子", "小孩", "儿子", "女儿", "宝宝", "家庭", "一家三口", "一家四口"],
        }
        
        for structure, keywords in family_keywords.items():
            if any(keyword in text for keyword in keywords):
                profile_data["family_structure"] = structure
                logger.info(f"Extracted family_structure: {structure}")
                # married_with_kids takes priority over married
                if structure == "married_with_kids":
                    break

        # Risk preference extraction
        risk_keywords = {
            "conservative": ["保守", "稳健", "安全", "低风险", "谨慎", "稳定"],
            "moderate": ["中等", "适中", "平衡", "中风险"],
            "aggressive": ["激进", "高风险", "进取", "冒险", "高收益"],
        }
        
        for risk_level, keywords in risk_keywords.items():
            if any(keyword in text for keyword in keywords):
                profile_data["risk_preference"] = risk_level
                logger.info(f"Extracted risk_preference: {risk_level}")
                break

        # Occupation extraction
        occupation_keywords = [
            "程序员", "工程师", "医生", "教师", "律师", "会计", "销售", "经理", 
            "公务员", "学生", "退休", "自由职业", "创业", "老板"
        ]
        
        for occupation in occupation_keywords:
            if occupation in text:
                profile_data["occupation"] = occupation
                logger.info(f"Extracted occupation: {occupation}")
                break

        # Income and expense extraction
        import re
        
        # Monthly expense patterns - improved to handle more formats
        expense_patterns = [
            r'月支出\s*大概\s*(\d+(?:\.\d+)?)\s*万',  # "月支出大概1.5万"
            r'月支出\s*(\d+(?:\.\d+)?)\s*万',        # "月支出1.5万"
            r'每月支出\s*大概\s*(\d+(?:\.\d+)?)\s*万', # "每月支出大概1.5万"
            r'每月支出\s*(\d+(?:\.\d+)?)\s*万',       # "每月支出1.5万"
            r'月支出\s*大概\s*(\d+)',                # "月支出大概15000"
            r'月支出\s*(\d+)',                      # "月支出15000"
            r'每月花费\s*(\d+)',                    # "每月花费15000"
            r'月开销\s*(\d+)',                      # "月开销15000"
            r'一个月\s*(\d+)',                      # "一个月15000"
        ]
        
        for pattern in expense_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    expense_str = match.group(1)
                    expense = float(expense_str)
                    
                    # Handle "万" unit
                    if '万' in pattern:
                        expense = expense * 10000
                    
                    profile_data["monthly_expense"] = expense
                    logger.info(f"Extracted monthly_expense: {expense}")
                    break
                except ValueError:
                    continue

        # Income range extraction - improved patterns
        income_patterns = [
            (r'年收入\s*大概\s*(\d+)\s*万', lambda m: f"{m.group(1)}万"),
            (r'年收入\s*(\d+)\s*万', lambda m: f"{m.group(1)}万"),
            (r'月收入\s*(\d+)\s*万', lambda m: f"{int(float(m.group(1)) * 12)}万"),
            (r'月收入\s*(\d+)', lambda m: f"{int(float(m.group(1)) * 12 / 10000)}万" if float(m.group(1)) > 1000 else f"{m.group(1)}"),
        ]
        
        for pattern, formatter in income_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    profile_data["income_range"] = formatter(match)
                    logger.info(f"Extracted income_range: {profile_data['income_range']}")
                    break
                except (ValueError, IndexError):
                    continue

        # Create profile if we have any meaningful data
        profile = None
        if profile_data:
            logger.info(f"Creating ExtractedUserProfile with data: {profile_data}")
            profile = ExtractedUserProfile(
                **profile_data, 
                confidence=0.5,  # Higher confidence for fallback since we're using multiple patterns
                extracted_from=text
            )
        else:
            logger.info("No profile data extracted in fallback mode")

        validation = self._create_validation(assets, profile, "new_info")

        return assets, profile, validation

    def _map_age_to_range(self, age: int) -> str:
        """Map specific age to age range"""
        if age < 20:
            return "20-30"
        elif age < 30:
            return "20-30"
        elif age < 40:
            return "30-40"
        elif age < 50:
            return "40-50"
        elif age < 60:
            return "50-60"
        else:
            return "60+"

    def _fallback_profile_extraction(self, user_message: str) -> ExtractedUserProfile | None:
        """Fallback profile extraction using regex patterns when LLM fails"""
        logger.info("Using fallback profile extraction")
        
        profile_data = {}
        text = user_message.lower()
        
        # Age range extraction
        import re
        age_patterns = [
            (r'(\d{2})\s*岁', lambda m: self._map_age_to_range(int(m.group(1)))),
            (r'今年\s*(\d{2})', lambda m: self._map_age_to_range(int(m.group(1)))),
            (r'(\d{2})\s*年', lambda m: self._map_age_to_range(int(m.group(1)))),
        ]
        
        for pattern, mapper in age_patterns:
            match = re.search(pattern, user_message)
            if match:
                try:
                    profile_data["age_range"] = mapper(match)
                    break
                except (ValueError, IndexError):
                    continue
        
        # Family structure extraction
        family_keywords = {
            "single": ["单身", "未婚", "一个人"],
            "married": ["已婚", "结婚", "夫妻", "老公", "老婆", "丈夫", "妻子"],
            "married_with_kids": ["孩子", "小孩", "儿子", "女儿", "宝宝", "家庭", "一家三口", "一家四口"],
        }
        
        for structure, keywords in family_keywords.items():
            if any(keyword in text for keyword in keywords):
                profile_data["family_structure"] = structure
                if structure == "married_with_kids":
                    break
        
        # Risk preference extraction
        risk_keywords = {
            "conservative": ["保守", "稳健", "安全", "低风险", "谨慎", "稳定"],
            "moderate": ["中等", "适中", "平衡", "中风险"],
            "aggressive": ["激进", "高风险", "进取", "冒险", "高收益"],
        }
        
        for risk_level, keywords in risk_keywords.items():
            if any(keyword in text for keyword in keywords):
                profile_data["risk_preference"] = risk_level
                break
        
        # Create profile if we have any data
        if profile_data:
            return ExtractedUserProfile(
                **profile_data,
                confidence=0.6,  # Medium confidence for fallback
                extracted_from=user_message
            )
        
        return None

    def _fallback_asset_extraction(self, user_message: str) -> list[ExtractedAsset]:
        """Fallback asset extraction using keyword matching when LLM fails"""
        logger.info("Using fallback asset extraction")
        
        assets = []
        text = user_message.lower()
        
        # Real estate detection
        if any(keyword in text for keyword in ["房产", "房子", "住房", "小区", "楼盘", "公寓"]):
            assets.append(ExtractedAsset(
                asset_type=AssetType.REAL_ESTATE,
                name="房产",
                value=None,
                confidence=0.6,
                extracted_from=user_message,
            ))
        
        # Cash detection
        if any(keyword in text for keyword in ["现金", "存款", "银行", "储蓄"]):
            assets.append(ExtractedAsset(
                asset_type=AssetType.CASH,
                name="现金",
                value=None,
                confidence=0.6,
                extracted_from=user_message,
            ))
        
        # Investment detection
        if any(keyword in text for keyword in ["股票", "基金", "投资", "理财"]):
            assets.append(ExtractedAsset(
                asset_type=AssetType.INVESTMENT,
                name="投资",
                value=None,
                confidence=0.6,
                extracted_from=user_message,
            ))
        
        return assets

    def _fallback_intent_detection(self, user_message: str) -> dict[str, Any]:
        """Fallback intent detection using keyword matching when LLM fails"""
        logger.info("Using fallback intent detection")
        
        text = user_message.lower()
        
        # Correction detection
        correction_keywords = ["不是", "不对", "应该是", "其实是", "错了", "不是这样"]
        if any(keyword in text for keyword in correction_keywords):
            return {
                "primary_intent": "correction",
                "correction_type": "value",
                "confidence": 0.7,
                "emotional_state": "neutral",
                "conversation_stage": "information_gathering"
            }
        
        # Question detection
        question_keywords = ["什么", "怎么", "如何", "为什么", "?", "？"]
        if any(keyword in text for keyword in question_keywords):
            return {
                "primary_intent": "question",
                "correction_type": "none",
                "confidence": 0.7,
                "emotional_state": "neutral",
                "conversation_stage": "information_gathering"
            }
        
        # Default to new_info
        return {
            "primary_intent": "new_info",
            "correction_type": "none",
            "confidence": 0.6,
            "emotional_state": "neutral",
            "conversation_stage": "information_gathering"
        }


# Global extractor instance
information_extractor = InformationExtractor()


def get_information_extractor() -> InformationExtractor:
    """
    Get the InformationExtractor instance.
    
    Factory function for dependency injection compatibility.
    Returns the global singleton instance.
    """
    return information_extractor


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
