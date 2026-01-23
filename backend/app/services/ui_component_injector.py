"""
UI Component Injector - Extract and inject UI components into responses

This module handles:
1. Detecting when UI components should be shown
2. Calling UIComponentService to generate components
3. Injecting component data into responses

AI Coding Guidance:
- This module decides WHEN to inject, UIComponentService decides HOW to generate
- Keep detection logic simple and rule-based
"""

import logging
from typing import Any

from app.models.context import ConversationContext
from app.services.ui_component_service import get_ui_component_service

logger = logging.getLogger(__name__)


class UIComponentInjector:
    """
    Handles extraction and injection of UI components into LLM responses.
    
    Extracted from the original ChatAgent._enhance_response_with_ui_components
    for better separation of concerns.
    """
    
    def __init__(self):
        self.ui_service = get_ui_component_service()
    
    async def extract_and_inject(
        self, 
        response: str, 
        context: ConversationContext,
        user_id: int
    ) -> tuple[str, list[dict[str, Any]]]:
        """
        Extract UI component triggers from response and generate components.
        
        Args:
            response: LLM response text
            context: Current conversation context
            user_id: User ID for database lookups
            
        Returns:
            tuple: (enhanced_response, ui_components)
                - enhanced_response: Original response with UI component markers
                - ui_components: List of component data dicts for frontend
        """
        ui_components = []
        enhanced_response = response
        
        try:
            # Check for valuation card triggers
            if self._should_show_valuation_card(response, context):
                valuation_cards = await self._generate_valuation_cards(context, user_id)
                ui_components.extend(valuation_cards)
            
            # Check for action card triggers
            if self._should_show_action_cards(response, context):
                action_cards = await self._generate_action_cards(context, user_id)
                ui_components.extend(action_cards)
            
            # Check for portfolio chart triggers
            if self._should_show_portfolio_chart(response, context):
                chart = await self._generate_portfolio_chart(context, user_id)
                if chart:
                    ui_components.append(chart)
            
            # Append UI component JSON to response if any
            if ui_components:
                import json
                components_json = json.dumps(ui_components, ensure_ascii=False)
                enhanced_response = f"{response}\n\n<!-- UI_COMPONENTS: {components_json} -->"
                
        except Exception as e:
            logger.error(f"Error injecting UI components: {e}")
        
        return enhanced_response, ui_components
    
    def _should_show_valuation_card(
        self, 
        response: str, 
        context: ConversationContext
    ) -> bool:
        """Determine if valuation card should be shown."""
        # Show when we have real estate assets and response mentions valuation
        has_real_estate = any(
            asset.get("type") == "real_estate" 
            for asset in context.extracted_assets
        )
        
        valuation_keywords = ["估值", "市值", "价值", "市场价", "均价"]
        mentions_valuation = any(kw in response for kw in valuation_keywords)
        
        return has_real_estate and mentions_valuation
    
    def _should_show_action_cards(
        self, 
        response: str, 
        context: ConversationContext
    ) -> bool:
        """Determine if action cards should be shown."""
        # Show when response contains recommendation keywords
        recommendation_keywords = ["建议", "推荐", "应该", "需要", "可以考虑"]
        return any(kw in response for kw in recommendation_keywords)
    
    def _should_show_portfolio_chart(
        self, 
        response: str, 
        context: ConversationContext
    ) -> bool:
        """Determine if portfolio chart should be shown."""
        # Show when analyzing portfolio or mentioning quadrant model
        chart_keywords = ["四象限", "资产配置", "配置比例", "投资组合"]
        has_enough_assets = len(context.extracted_assets) >= 2
        
        return has_enough_assets and any(kw in response for kw in chart_keywords)
    
    async def _generate_valuation_cards(
        self, 
        context: ConversationContext,
        user_id: int
    ) -> list[dict[str, Any]]:
        """Generate valuation cards for real estate assets."""
        cards = []
        
        for asset in context.extracted_assets:
            if asset.get("type") == "real_estate":
                card = self.ui_service.generate_valuation_card(
                    property_name=asset.get("name", "房产"),
                    estimated_value=asset.get("value", 0),
                    value_range=(
                        asset.get("value", 0) * 0.9,
                        asset.get("value", 0) * 1.1
                    ),
                    area=asset.get("extra_data", {}).get("area"),
                    location=asset.get("extra_data", {}).get("location"),
                )
                cards.append({
                    "type": "VALUATION_CARD",
                    "data": card
                })
        
        return cards
    
    async def _generate_action_cards(
        self, 
        context: ConversationContext,
        user_id: int
    ) -> list[dict[str, Any]]:
        """Generate action cards based on portfolio analysis."""
        cards = []
        
        # Get portfolio analysis if available
        if context.portfolio_analysis:
            risk_warnings = context.portfolio_analysis.get("risk_warnings", [])
            
            for warning in risk_warnings[:3]:  # Limit to top 3
                card = self.ui_service.generate_action_card(
                    action_type=warning.get("type", "general"),
                    title=warning.get("title", "建议"),
                    description=warning.get("recommendation", ""),
                    priority=self._map_severity(warning.get("severity", "medium")),
                    reason=warning.get("description", ""),
                )
                cards.append({
                    "type": "ACTION_CARD",
                    "data": card
                })
        
        return cards
    
    async def _generate_portfolio_chart(
        self, 
        context: ConversationContext,
        user_id: int
    ) -> dict[str, Any] | None:
        """Generate portfolio chart data."""
        if not context.portfolio_analysis:
            return None
        
        quadrant_data = context.portfolio_analysis.get("quadrant_analysis", {})
        if not quadrant_data:
            return None
        
        return {
            "type": "PORTFOLIO_CHART",
            "data": {
                "quadrants": quadrant_data.get("quadrants", {}),
                "summary": quadrant_data.get("summary", {}),
                "net_worth": context.portfolio_analysis.get("net_worth", 0),
            }
        }
    
    def _map_severity(self, severity: str) -> str:
        """Map warning severity to card priority."""
        mapping = {
            "high": "high",
            "medium": "medium", 
            "low": "low",
            "critical": "high",
        }
        return mapping.get(severity.lower(), "medium")


# Singleton instance
_ui_injector: UIComponentInjector | None = None


def get_ui_component_injector() -> UIComponentInjector:
    """Get or create UIComponentInjector instance."""
    global _ui_injector
    if _ui_injector is None:
        _ui_injector = UIComponentInjector()
    return _ui_injector
