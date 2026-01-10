"""
Natural language information extraction for asset and user profile data
"""

import logging
import re
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

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
    """Natural language information extraction service"""

    def __init__(self):
        # Property-related keywords and patterns
        self.property_keywords = [
            "房子",
            "房产",
            "住房",
            "小区",
            "楼盘",
            "公寓",
            "别墅",
            "商铺",
            "写字楼",
            "房屋",
            "物业",
            "地产",
        ]

        # Location patterns (major Chinese cities and districts)
        self.location_patterns = [
            # Major cities
            "北京",
            "上海",
            "深圳",
            "广州",
            "杭州",
            "南京",
            "成都",
            "武汉",
            "西安",
            "重庆",
            "天津",
            "苏州",
            "青岛",
            "长沙",
            "大连",
            "厦门",
            # Beijing districts/areas
            "朝阳",
            "海淀",
            "西城",
            "东城",
            "丰台",
            "石景山",
            "昌平",
            "大兴",
            "通州",
            "顺义",
            "房山",
            "门头沟",
            "平谷",
            "怀柔",
            "密云",
            "延庆",
            "天通苑",
            "望京",
            "中关村",
            "三里屯",
            "国贸",
            "亚运村",
            "回龙观",
            # Shanghai districts/areas
            "浦东",
            "徐汇",
            "长宁",
            "静安",
            "普陀",
            "虹口",
            "杨浦",
            "黄浦",
            "闵行",
            "宝山",
            "嘉定",
            "金山",
            "松江",
            "青浦",
            "奉贤",
            "崇明",
            "陆家嘴",
            "徐家汇",
            "静安寺",
            "人民广场",
            "外滩",
            "新天地",
        ]

        # Asset value patterns
        self.value_patterns = [
            r"(\d+(?:\.\d+)?)\s*万",  # X万, X.X万
            r"(\d+(?:\.\d+)?)\s*千万",  # X千万
            r"(\d+(?:\.\d+)?)\s*亿",  # X亿
            r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*元",  # X元, X,XXX元
            r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*块",  # X块钱
        ]

        # Area patterns
        self.area_patterns = [
            r"(\d+(?:\.\d+)?)\s*平(?:方米|米)?",  # X平, X平方米, X平米
            r"(\d+(?:\.\d+)?)\s*㎡",  # X㎡
            r"(\d+(?:\.\d+)?)\s*平方",  # X平方
        ]

        # Age range patterns
        self.age_patterns = [
            r"(\d{1,2})\s*岁",  # X岁
            r"(\d{1,2})\s*-\s*(\d{1,2})\s*岁",  # X-Y岁
            r"(\d{2})后",  # 80后, 90后
        ]

        # Family structure keywords
        self.family_keywords = {
            "single": ["单身", "未婚", "一个人", "独居"],
            "married": ["已婚", "结婚", "夫妻", "老公", "老婆", "丈夫", "妻子"],
            "married_with_kids": [
                "孩子",
                "小孩",
                "儿子",
                "女儿",
                "宝宝",
                "家庭",
                "三口之家",
                "四口之家",
            ],
        }

        # Asset type keywords
        self.asset_keywords = {
            AssetType.REAL_ESTATE: self.property_keywords,
            AssetType.CASH: [
                "现金",
                "存款",
                "银行",
                "储蓄",
                "活期",
                "定期",
                "余额宝",
                "理财通",
            ],
            AssetType.INVESTMENT: [
                "股票",
                "基金",
                "债券",
                "理财",
                "投资",
                "证券",
                "期货",
                "黄金",
                "外汇",
            ],
            AssetType.INSURANCE: [
                "保险",
                "重疾险",
                "意外险",
                "寿险",
                "医疗险",
                "车险",
                "财产险",
            ],
            AssetType.LIABILITY: [
                "贷款",
                "房贷",
                "车贷",
                "信用卡",
                "欠款",
                "债务",
                "借款",
                "按揭",
            ],
        }

    def extract_assets_from_text(self, text: str) -> list[ExtractedAsset]:
        """Extract asset information from natural language text"""
        assets = []

        # Extract real estate assets
        real_estate_assets = self._extract_real_estate(text)
        assets.extend(real_estate_assets)

        # Extract other asset types
        for asset_type, keywords in self.asset_keywords.items():
            if asset_type == AssetType.REAL_ESTATE:
                continue  # Already handled above

            asset_mentions = self._extract_asset_mentions(text, asset_type, keywords)
            assets.extend(asset_mentions)

        return assets

    def extract_user_profile_from_text(self, text: str) -> ExtractedUserProfile | None:
        """Extract user profile information from natural language text"""
        profile_data = {}
        confidence_scores = []

        # Extract age information
        age_info = self._extract_age_range(text)
        if age_info:
            profile_data["age_range"] = age_info["range"]
            confidence_scores.append(age_info["confidence"])

        # Extract family structure
        family_info = self._extract_family_structure(text)
        if family_info:
            profile_data["family_structure"] = family_info["structure"]
            confidence_scores.append(family_info["confidence"])

        # Extract monthly expenses
        expense_info = self._extract_monthly_expenses(text)
        if expense_info:
            profile_data["monthly_expense"] = expense_info["amount"]
            confidence_scores.append(expense_info["confidence"])

        # Extract risk preference
        risk_info = self._extract_risk_preference(text)
        if risk_info:
            profile_data["risk_preference"] = risk_info["preference"]
            confidence_scores.append(risk_info["confidence"])

        if not profile_data:
            return None

        # Calculate overall confidence
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores
            else 0.0
        )

        return ExtractedUserProfile(
            **profile_data, confidence=overall_confidence, extracted_from=text
        )

    def _extract_real_estate(self, text: str) -> list[ExtractedAsset]:
        """Extract real estate information with location and area"""
        assets = []

        # Check if text mentions property
        has_property = any(keyword in text for keyword in self.property_keywords)
        if not has_property:
            return assets

        # Extract location
        location = self._extract_location(text)

        # Extract area
        area = self._extract_area(text)

        # Extract value
        value = self._extract_value(text)

        # Create asset if we have meaningful information
        if location or area or value:
            metadata = {}
            if area:
                metadata["area"] = area
            if location:
                metadata["location"] = location

            # Generate asset name
            name_parts = []
            if location:
                name_parts.append(location)
            if area:
                name_parts.append(f"{area}平米")
            name = "房产" if not name_parts else " ".join(name_parts) + "房产"

            # Calculate confidence based on available information
            confidence = 0.3  # Base confidence for property mention
            if location:
                confidence += 0.3
            if area:
                confidence += 0.2
            if value:
                confidence += 0.2

            asset = ExtractedAsset(
                asset_type=AssetType.REAL_ESTATE,
                name=name,
                value=value,
                location=location,
                area=area,
                metadata=metadata,
                confidence=confidence,
                extracted_from=text,
            )
            assets.append(asset)

        return assets

    def _extract_asset_mentions(
        self, text: str, asset_type: AssetType, keywords: list[str]
    ) -> list[ExtractedAsset]:
        """Extract mentions of specific asset types"""
        assets = []

        # Check if text mentions this asset type
        mentioned_keywords = [kw for kw in keywords if kw in text]
        if not mentioned_keywords:
            return assets

        # Extract value associated with this asset type
        value = self._extract_value_near_keywords(text, mentioned_keywords)

        # Create asset entry
        name = mentioned_keywords[0]  # Use first mentioned keyword as name
        confidence = 0.5 if value else 0.3  # Higher confidence if value is found

        asset = ExtractedAsset(
            asset_type=asset_type,
            name=name,
            value=value,
            confidence=confidence,
            extracted_from=text,
        )
        assets.append(asset)

        return assets

    def _extract_location(self, text: str) -> str | None:
        """Extract location information from text"""
        for location in self.location_patterns:
            if location in text:
                return location
        return None

    def _extract_area(self, text: str) -> float | None:
        """Extract area information from text"""
        for pattern in self.area_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None

    def _extract_value(self, text: str) -> float | None:
        """Extract monetary value from text"""
        for pattern in self.value_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1).replace(",", ""))

                    # Convert based on unit
                    if "万" in pattern:
                        value *= 10000
                    elif "千万" in pattern:
                        value *= 10000000
                    elif "亿" in pattern:
                        value *= 100000000

                    return value
                except ValueError:
                    continue
        return None

    def _extract_value_near_keywords(
        self, text: str, keywords: list[str]
    ) -> float | None:
        """Extract value that appears near specific keywords"""
        # Simple approach: look for values in the same sentence as keywords
        sentences = re.split(r"[。！？；]", text)

        for sentence in sentences:
            # Check if sentence contains any of the keywords
            if any(kw in sentence for kw in keywords):
                value = self._extract_value(sentence)
                if value:
                    return value

        return None

    def _extract_age_range(self, text: str) -> dict[str, Any] | None:
        """Extract age range information"""
        for pattern in self.age_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 1:
                    # Single age or generation
                    age_str = match.group(1)
                    if "后" in match.group(0):  # 80后, 90后
                        decade = int(age_str)
                        return {"range": f"{decade}-{decade + 9}", "confidence": 0.8}
                    else:  # X岁
                        age = int(age_str)
                        # Group into ranges
                        if age < 30:
                            range_str = "20-30"
                        elif age < 40:
                            range_str = "30-40"
                        elif age < 50:
                            range_str = "40-50"
                        elif age < 60:
                            range_str = "50-60"
                        else:
                            range_str = "60+"

                        return {"range": range_str, "confidence": 0.9}
                elif len(match.groups()) == 2:
                    # Age range X-Y岁
                    start_age = int(match.group(1))
                    end_age = int(match.group(2))
                    return {"range": f"{start_age}-{end_age}", "confidence": 0.9}

        return None

    def _extract_family_structure(self, text: str) -> dict[str, Any] | None:
        """Extract family structure information"""
        # Check for kids first (highest priority)
        for keyword in self.family_keywords["married_with_kids"]:
            if keyword in text:
                return {"structure": "married_with_kids", "confidence": 0.8}

        # Check for married
        for keyword in self.family_keywords["married"]:
            if keyword in text:
                return {"structure": "married", "confidence": 0.7}

        # Check for single
        for keyword in self.family_keywords["single"]:
            if keyword in text:
                return {"structure": "single", "confidence": 0.7}

        return None

    def _extract_monthly_expenses(self, text: str) -> dict[str, Any] | None:
        """Extract monthly expense information"""
        expense_keywords = ["月支出", "每月花费", "月开销", "生活费", "月消费"]

        # Look for expense-related patterns
        for keyword in expense_keywords:
            if keyword in text:
                # Look for value near the keyword
                # Simple approach: extract value from same sentence
                sentences = re.split(r"[。！？；]", text)
                for sentence in sentences:
                    if keyword in sentence:
                        value = self._extract_value(sentence)
                        if value:
                            return {"amount": value, "confidence": 0.7}

        return None

    def _extract_risk_preference(self, text: str) -> dict[str, Any] | None:
        """Extract risk preference information"""
        risk_keywords = {
            "conservative": ["保守", "稳健", "安全", "低风险", "保本"],
            "moderate": ["平衡", "中等", "适中", "稳中求进"],
            "aggressive": ["激进", "高风险", "高收益", "冒险", "进取"],
        }

        for preference, keywords in risk_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return {"preference": preference, "confidence": 0.6}

        return None

    def validate_extracted_data(
        self, assets: list[ExtractedAsset], profile: ExtractedUserProfile | None
    ) -> dict[str, Any]:
        """Validate and provide feedback on extracted data quality"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "suggestions": [],
            "completeness_score": 0.0,
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


# Global extractor instance
information_extractor = InformationExtractor()


def extract_information_from_conversation(
    text: str,
) -> tuple[list[ExtractedAsset], ExtractedUserProfile | None, dict[str, Any]]:
    """
    Extract structured information from conversational text

    Returns:
        Tuple of (assets, user_profile, validation_result)
    """
    assets = information_extractor.extract_assets_from_text(text)
    profile = information_extractor.extract_user_profile_from_text(text)
    validation = information_extractor.validate_extracted_data(assets, profile)

    return assets, profile, validation
