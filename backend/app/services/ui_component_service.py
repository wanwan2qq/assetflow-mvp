"""
UI Component Generation Service for AssetFlow

This service handles the generation of structured UI component tags
that are embedded in AI responses for dynamic frontend rendering.
"""

import json
import logging
import re
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.models.commercial import CommercialProduct
from app.models.user import UserAsset

logger = logging.getLogger(__name__)


class UIComponentType(str, Enum):
    """Supported UI component types"""

    VALUATION_CARD = "VALUATION_CARD"
    ACTION_CARD = "ACTION_CARD"
    PORTFOLIO_CHART = "PORTFOLIO_CHART"
    ASSET_CARD = "ASSET_CARD"  # For displaying single asset details
    PRODUCT_CARD = "PRODUCT_CARD"  # Specialized commercial product card


class UIComponent(BaseModel):
    """Represents a UI component to be rendered"""

    type: UIComponentType
    data: dict[str, Any]
    position: int = Field(default=0, description="Position in the response text")


class ValuationCardData(BaseModel):
    """Data structure for valuation card"""

    price: float = Field(description="Property price in yuan")
    area: float = Field(description="Property area in square meters")
    location: str = Field(description="Property location")
    price_per_sqm: float = Field(description="Price per square meter")
    confidence: float = Field(default=0.8, description="Confidence level of valuation")


class ActionCardData(BaseModel):
    """Data structure for action card"""

    type: str = Field(description="Action type (insurance, broker, investment, etc.)")
    title: str = Field(description="Action card title")
    description: str = Field(description="Action description")
    priority: str = Field(description="Priority level (high, medium, low)")
    contact_info: dict[str, Any] | None = Field(
        default=None, description="Contact information"
    )
    reason: str | None = Field(
        default=None, description="Why this action is recommended"
    )
    provider_info: str | None = Field(
        default=None, description="Broker/Company name providing the service"
    )


class AssetCardData(BaseModel):
    """Data structure for asset card"""

    name: str = Field(description="Asset name")
    value: float = Field(description="Asset value")
    type: str = Field(description="Asset type (real_estate, cash, investment, etc.)")
    risk_level: str | None = Field(default=None, description="Risk level of the asset")
    tags: list[str] = Field(default=[], description="Asset tags/categories")
    privacy_mode: bool = Field(default=False, description="Whether to mask exact values")


class ProductCardData(BaseModel):
    """Data structure for commercial product card"""

    name: str = Field(description="Product name")
    provider: str = Field(description="Service provider name")
    category: str = Field(description="Product category")
    description: str = Field(description="Product description")
    price: str | None = Field(default=None, description="Product price or fee structure")
    roi: str | None = Field(default=None, description="Expected ROI or benefit")
    buy_now_link: str | None = Field(default=None, description="Purchase/contact link")
    contact_info: dict[str, Any] | None = Field(
        default=None, description="Contact information"
    )
    priority: str = Field(description="Priority level (high, medium, low)")
    reason: str | None = Field(
        default=None, description="Why this product is recommended"
    )


class PortfolioChartData(BaseModel):
    """Data structure for portfolio chart"""

    assets: list[dict[str, Any]] = Field(
        description="List of assets with type, value, percentage"
    )
    total_value: float = Field(description="Total portfolio value")
    chart_type: str = Field(default="pie", description="Chart type (pie, bar, etc.)")


class UIComponentService:
    """Service for generating structured UI components"""

    def __init__(self):
        self.widget_pattern = re.compile(r'<WIDGET:(\w+)(?:\s+data="([^"]*)")?\s*>')

    def generate_valuation_card(
        self, price: float, area: float, location: str, confidence: float = 0.8
    ) -> str:
        """Generate valuation card UI component tag"""
        try:
            price_per_sqm = price / area if area > 0 else 0

            card_data = ValuationCardData(
                price=price,
                area=area,
                location=location,
                price_per_sqm=price_per_sqm,
                confidence=confidence,
            )

            # Convert to JSON string for embedding, escape quotes for HTML attribute
            data_json = json.dumps(card_data.model_dump(), ensure_ascii=False)
            escaped_json = data_json.replace('"', "&quot;")
            return f'<WIDGET:VALUATION_CARD data="{escaped_json}">'

        except Exception as e:
            logger.error(f"Error generating valuation card: {e}")
            return ""

    def generate_action_card(
        self,
        action_type: str,
        title: str,
        description: str,
        priority: str = "medium",
        contact_info: dict[str, Any] | None = None,
        reason: str | None = None,
        provider_info: str | None = None,
    ) -> str:
        """Generate action card UI component tag"""
        try:
            card_data = ActionCardData(
                type=action_type,
                title=title,
                description=description,
                priority=priority,
                contact_info=contact_info,
                reason=reason,
                provider_info=provider_info,
            )

            # Convert to JSON string for embedding, escape quotes for HTML attribute
            data_json = json.dumps(card_data.model_dump(), ensure_ascii=False)
            escaped_json = data_json.replace('"', "&quot;")
            return f'<WIDGET:ACTION_CARD data="{escaped_json}">'

        except Exception as e:
            logger.error(f"Error generating action card: {e}")
            return ""

    def generate_portfolio_chart(
        self, assets: list[UserAsset], chart_type: str = "pie"
    ) -> str:
        """Generate portfolio chart UI component tag"""
        try:
            # Calculate total value
            total_value = sum(asset.value for asset in assets if asset.value > 0)

            if total_value <= 0:
                return ""

            # Prepare asset data for chart
            chart_assets = []
            for asset in assets:
                if asset.value > 0:
                    percentage = (asset.value / total_value) * 100
                    chart_assets.append(
                        {
                            "type": asset.asset_type.value,
                            "name": asset.name,
                            "value": asset.value,
                            "percentage": round(percentage, 1),
                        }
                    )

            chart_data = PortfolioChartData(
                assets=chart_assets, total_value=total_value, chart_type=chart_type
            )

            # Convert to JSON string for embedding, escape quotes for HTML attribute
            data_json = json.dumps(chart_data.model_dump(), ensure_ascii=False)
            escaped_json = data_json.replace('"', "&quot;")
            return f'<WIDGET:PORTFOLIO_CHART data="{escaped_json}">'

        except Exception as e:
            logger.error(f"Error generating portfolio chart: {e}")
            return ""

    def generate_asset_card(
        self,
        name: str,
        value: float,
        asset_type: str,
        risk_level: str | None = None,
        tags: list[str] | None = None,
        privacy_mode: bool = False,
    ) -> str:
        """Generate asset card widget"""
        try:
            # Mask value if privacy mode is enabled
            display_value = value
            if privacy_mode:
                # Mask exact value, show only magnitude
                if value >= 10000000:  # >= 1000万
                    display_value = 10000000  # Show as "1000万+"
                elif value >= 1000000:  # >= 100万
                    display_value = 1000000  # Show as "100万+"
                elif value >= 100000:  # >= 10万
                    display_value = 100000  # Show as "10万+"

            card_data = AssetCardData(
                name=name,
                value=display_value,
                type=asset_type,
                risk_level=risk_level,
                tags=tags or [],
                privacy_mode=privacy_mode,
            )

            # Convert to JSON string for embedding, escape quotes for HTML attribute
            data_json = json.dumps(card_data.model_dump(), ensure_ascii=False)
            escaped_json = data_json.replace('"', "&quot;")
            return f'<WIDGET:ASSET_CARD data="{escaped_json}">'

        except Exception as e:
            logger.error(f"Error generating asset card: {e}")
            return ""

    def generate_product_card(
        self,
        name: str,
        provider: str,
        category: str,
        description: str,
        priority: str = "medium",
        price: str | None = None,
        roi: str | None = None,
        buy_now_link: str | None = None,
        contact_info: dict[str, Any] | None = None,
        reason: str | None = None,
    ) -> str:
        """Generate commercial product card widget"""
        try:
            card_data = ProductCardData(
                name=name,
                provider=provider,
                category=category,
                description=description,
                price=price,
                roi=roi,
                buy_now_link=buy_now_link,
                contact_info=contact_info,
                priority=priority,
                reason=reason,
            )

            # Convert to JSON string for embedding, escape quotes for HTML attribute
            data_json = json.dumps(card_data.model_dump(), ensure_ascii=False)
            escaped_json = data_json.replace('"', "&quot;")
            return f'<WIDGET:PRODUCT_CARD data="{escaped_json}">'

        except Exception as e:
            logger.error(f"Error generating product card: {e}")
            return ""

    def generate_components_from_context(
        self, 
        chat_context: dict[str, Any],
        user_profile: dict[str, Any] | None = None,
        privacy_mode: bool = False
    ) -> list[str]:
        """
        Generate UI components based on chat context data instead of regex matching.
        This is the new deterministic approach replacing regex-based triggers.
        
        Args:
            chat_context: Contains extracted_assets, portfolio_analysis, recommendations, etc.
            user_profile: User profile information
            privacy_mode: Whether to mask exact values in cards
            
        Returns:
            List of UI component strings ready for embedding
        """
        components = []
        
        try:
            # 1. Generate VALUATION_CARD for real estate assets (most important for user experience)
            extracted_assets = chat_context.get("extracted_assets", [])
            real_estate_assets = [
                asset for asset in extracted_assets 
                if asset.get("asset_type") == "real_estate" and asset.get("value", 0) > 0
            ]
            
            if real_estate_assets:
                # Generate valuation card for the most recent/valuable property
                asset = max(real_estate_assets, key=lambda x: x.get("value", 0))
                valuation_card = self.generate_valuation_card(
                    price=asset.get("value", 0),
                    area=asset.get("area", 100),  # Default area if not provided
                    location=asset.get("location", asset.get("name", "房产")),
                    confidence=asset.get("confidence", 0.8)
                )
                if valuation_card:
                    components.append(valuation_card)
            
            # 2. Generate PRODUCT_CARD or ACTION_CARD from recommendations
            recommendations = chat_context.get("recommendations", [])
            for rec in recommendations:
                if isinstance(rec, dict):
                    # Check if this is a commercial product recommendation
                    if rec.get("product_info") and rec.get("buy_now_link"):
                        # Generate PRODUCT_CARD for commercial products
                        product_card = self.generate_product_card(
                            name=rec.get("name", "推荐产品"),
                            provider=rec.get("provider", ""),
                            category=rec.get("category", ""),
                            description=rec.get("description", ""),
                            priority=rec.get("priority", "medium"),
                            price=rec.get("price"),
                            roi=rec.get("roi"),
                            buy_now_link=rec.get("buy_now_link"),
                            contact_info=rec.get("contact_info"),
                            reason=rec.get("reason")
                        )
                        if product_card:
                            components.append(product_card)
                    else:
                        # Generate ACTION_CARD for general recommendations
                        action_card = self.generate_action_card(
                            action_type=rec.get("type", "general"),
                            title=rec.get("title", "建议"),
                            description=rec.get("description", ""),
                            priority=rec.get("priority", "medium"),
                            contact_info=rec.get("contact_info"),
                            reason=rec.get("reason"),
                            provider_info=rec.get("provider")
                        )
                        if action_card:
                            components.append(action_card)
            
            # 3. Generate ASSET_CARD for newly added assets
            newly_added_asset = chat_context.get("newly_added_asset")
            if newly_added_asset:
                asset_card = self.generate_asset_card(
                    name=newly_added_asset.get("name", "新资产"),
                    value=newly_added_asset.get("value", 0),
                    asset_type=newly_added_asset.get("asset_type", "unknown"),
                    risk_level=newly_added_asset.get("risk_level"),
                    tags=newly_added_asset.get("tags", []),
                    privacy_mode=privacy_mode
                )
                if asset_card:
                    components.append(asset_card)
            
            # 4. Generate PORTFOLIO_CHART if portfolio analysis is fresh
            portfolio_analysis = chat_context.get("portfolio_analysis")
            if portfolio_analysis and portfolio_analysis.get("is_fresh", False):
                if len(extracted_assets) >= 2:
                    # Convert dict assets to UserAsset-like objects for chart generation
                    asset_objects = []
                    for asset_data in extracted_assets:
                        # Create a simple object with the required attributes
                        class AssetObj:
                            def __init__(self, data):
                                self.name = data.get("name", "")
                                self.value = data.get("value", 0)
                                self.asset_type = type('AssetType', (), {
                                    'value': data.get("asset_type", "unknown")
                                })()
                        
                        if asset_data.get("value", 0) > 0:
                            asset_objects.append(AssetObj(asset_data))
                    
                    if asset_objects:
                        portfolio_chart = self.generate_portfolio_chart(asset_objects)
                        if portfolio_chart:
                            components.append(portfolio_chart)
            
            # 5. Generate ACTION_CARDs from portfolio analysis risk warnings
            if portfolio_analysis:
                risk_warnings = portfolio_analysis.get("risk_warnings", [])
                for warning in risk_warnings:
                    action_card = self.generate_action_card(
                        action_type=warning.get("type", "risk"),
                        title=warning.get("title", "风险提醒"),
                        description=warning.get("recommendation", ""),
                        priority=self._map_severity_to_priority(warning.get("severity", "medium")),
                        reason=warning.get("description")
                    )
                    if action_card:
                        components.append(action_card)
                        
        except Exception as e:
            logger.error(f"Error generating components from context: {e}")
            
        return components

    def generate_action_cards_from_risks(
        self,
        risk_warnings: list[dict[str, Any]],
        commercial_products: list[CommercialProduct] | None = None,
    ) -> list[str]:
        """Generate action cards based on risk warnings and commercial products"""
        cards = []

        try:
            for warning in risk_warnings:
                risk_type = warning.get("type", "general")
                title = warning.get("title", "风险提醒")
                description = warning.get("recommendation", "建议采取相应措施")
                priority = self._map_severity_to_priority(
                    warning.get("severity", "medium")
                )

                # Find matching commercial product if available
                contact_info = None
                if commercial_products:
                    matching_product = self._find_matching_product(
                        risk_type, commercial_products
                    )
                    if matching_product:
                        contact_info = matching_product.contact_info
                        description = (
                            f"{description}\n\n推荐服务商: {matching_product.provider}"
                        )

                card = self.generate_action_card(
                    action_type=risk_type,
                    title=title,
                    description=description,
                    priority=priority,
                    contact_info=contact_info,
                )

                if card:
                    cards.append(card)

        except Exception as e:
            logger.error(f"Error generating action cards from risks: {e}")

        return cards

    def _map_severity_to_priority(self, severity: str) -> str:
        """Map risk severity to action card priority"""
        severity_mapping = {
            "high": "high",
            "medium": "medium",
            "low": "low",
            "critical": "high",
        }
        return severity_mapping.get(severity.lower(), "medium")

    def _find_matching_product(
        self, risk_type: str, products: list[CommercialProduct]
    ) -> CommercialProduct | None:
        """Find commercial product matching the risk type"""
        # Risk type to product category mapping
        risk_to_category = {
            "HIGH_RE_CONCENTRATION": "broker",
            "LIQUIDITY_CRISIS": "investment",
            "INSURANCE_GAP": "insurance",
            "DEBT_RISK": "loan",
            "diversification": "broker",
            "liquidity": "investment",
            "insurance": "insurance",
            # Add mappings for portfolio analyzer risk types
            "real_estate_concentration": "broker",  # Real estate concentration -> broker services
            "liquidity_risk": "investment",         # Liquidity risk -> investment products
            "insurance_gap": "insurance",           # Insurance gap -> insurance products
            "debt_burden": "loan",                  # Debt burden -> loan products
            "investment_risk": "investment",        # Investment risk -> investment products
        }

        target_category = risk_to_category.get(risk_type, "consulting")

        # Find active products in the target category, sorted by priority
        matching_products = [
            p for p in products if p.category == target_category and p.is_active
        ]

        if matching_products:
            # Return highest priority product
            return max(matching_products, key=lambda p: p.priority)

        return None

    def extract_ui_components(self, response: str) -> list[UIComponent]:
        """Extract UI component tags from AI response"""
        components = []

        try:
            for match in self.widget_pattern.finditer(response):
                widget_type = match.group(1)
                widget_data_str = match.group(2) or "{}"

                try:
                    # Unescape HTML entities in the JSON data
                    unescaped_json = widget_data_str.replace("&quot;", '"')
                    # Parse the data
                    widget_data = json.loads(unescaped_json)

                    component = UIComponent(
                        type=UIComponentType(widget_type),
                        data=widget_data,
                        position=match.start(),
                    )
                    components.append(component)

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse widget data: {widget_data_str}, error: {e}"
                    )

        except Exception as e:
            logger.error(f"Error extracting UI components: {e}")

        return components

    def enhance_response_with_components(
        self, response: str, components: list[str]
    ) -> str:
        """Enhance AI response by appending UI components"""
        if not components:
            return response

        enhanced_response = response
        for component in components:
            if component.strip():
                enhanced_response += f"\n\n{component}"

        return enhanced_response

    def should_generate_valuation_card(
        self, response: str, extracted_assets: list[dict[str, Any]]
    ) -> bool:
        """Determine if valuation card should be generated"""
        # Check if we have property info and response mentions valuation
        has_property = any(
            asset.get("asset_type") == "real_estate" for asset in extracted_assets
        )

        valuation_keywords = ["估值", "价值", "价格", "万元", "评估"]
        mentions_valuation = any(keyword in response for keyword in valuation_keywords)

        return has_property and mentions_valuation

    def should_generate_portfolio_chart(
        self, response: str, extracted_assets: list[dict[str, Any]], current_stage: str
    ) -> bool:
        """Determine if portfolio chart should be generated"""
        # Check if we have multiple assets and response mentions analysis
        has_multiple_assets = len(extracted_assets) >= 2

        analysis_keywords = ["分析", "配置", "分布", "占比", "组合", "四象限"]
        mentions_analysis = any(keyword in response for keyword in analysis_keywords)

        return has_multiple_assets and mentions_analysis and current_stage == "analysis"

    def should_generate_action_cards(self, response: str, current_stage: str) -> bool:
        """Determine if action cards should be generated"""
        # Generate action cards during analysis stage or when risks are mentioned
        risk_keywords = ["风险", "建议", "改善", "优化", "不足", "过高", "偏低"]
        mentions_risks = any(keyword in response for keyword in risk_keywords)

        return current_stage == "analysis" or mentions_risks


# Global service instance
ui_component_service = UIComponentService()


def get_ui_component_service() -> UIComponentService:
    """Get UI component service instance"""
    return ui_component_service
