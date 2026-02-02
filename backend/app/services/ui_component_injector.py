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
from app.models.action_plan import ActionCategory

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
        
        # Initialize lists to avoid UnboundLocalError
        plan_cards = []
        
        try:
            # STRIP HALLUCINATED TAGS
            import re
            # Remove any <WIDGET...> tags to prevent ID-less duplicates/hallucinations
            # 1. Match standard self-closing tags with DOTALL (handles newlines and inner > if ends with />)
            # Use IGNORECASE and \b to handle <Widget... or <WIDGET ...
            response = re.sub(r'<WIDGET\b.*?/>', '', response, flags=re.DOTALL | re.IGNORECASE)
            
            # 2. Match tag pairs <WIDGET...>...</WIDGET>
            response = re.sub(r'<WIDGET\b.*?</WIDGET\s*>', '', response, flags=re.DOTALL | re.IGNORECASE)

            # 3. Cleanup HTML entity versions
            response = re.sub(r'&lt;WIDGET\b.*?/&gt;', '', response, flags=re.DOTALL | re.IGNORECASE)
            
            # 4. Match non-self-closing tags: <WIDGET:TYPE data="..."> 
            # The data attribute uses &quot; for inner quotes, so we can safely match to the closing ">
            # Pattern: <WIDGET:WORD optional_space data="anything_except_unescaped_quote">
            response = re.sub(r'<WIDGET:\w+\s+data="[^"]*">', '', response, flags=re.IGNORECASE)
            
            # 5. Match tags with single-quoted JSON (LLM sometimes uses single quotes)
            response = re.sub(r"<WIDGET:\w+\s+data='[^']*'>", '', response, flags=re.IGNORECASE)
            
            # 6. Match tags ending with /> (self-closing) - covers more formats
            response = re.sub(r'<WIDGET:\w+\s+data="[^"]*"\s*/>', '', response, flags=re.IGNORECASE)
            
            # 7. Match tags with HTML entity quotes: data="{&quot;...&quot;}" />
            # This catches LLM output like: <WIDGET:VALUATION_CARD data="{&quot;id&quot;: 88, ...}" />
            response = re.sub(r'<WIDGET:\w+\s+data="\{[^}]*\}"\s*/>', '', response, flags=re.IGNORECASE)
            
            # 8. Catch-all: Match any remaining <WIDGET:TYPE ...> patterns
            # Use non-greedy match to first /> or >
            response = re.sub(r'<WIDGET:\w+[^>]*/>', '', response, flags=re.IGNORECASE)
            
            # NOTE: We removed the aggressive <WIDGET[^>]+> cleanup because it breaks tags with inner > in JSON data.
            
            enhanced_response = response

            # 1. Check for valuation card triggers
            try:
                if self._should_show_valuation_card(response, context):
                    valuation_cards = await self._generate_valuation_cards(context, user_id, response)
                    ui_components.extend(valuation_cards)
            except Exception as e:
                logger.error(f"Error generating valuation cards: {e}")

            # 2. Check for action plan card triggers (INDEPENDENT CHECK)
            try:
                if self._should_show_action_plan_card(response, context):
                    plan_cards = await self._generate_action_plan_cards(context, user_id)
                    ui_components.extend(plan_cards)
            except Exception as e:
                logger.error(f"Error generating action plan cards: {e}")
            
            # 3. Check for simple action card triggers (Only if NO plan card was generated)
            try:
                if not plan_cards and self._should_show_action_cards(response, context):
                    action_cards = await self._generate_action_cards(context, user_id)
                    ui_components.extend(action_cards)
            except Exception as e:
                logger.error(f"Error generating simple action cards: {e}")
            
            # 4. Check for portfolio chart triggers
            try:
                if self._should_show_portfolio_chart(response, context):
                    chart = await self._generate_portfolio_chart(context, user_id)
                    if chart:
                        ui_components.append(chart)
            except Exception as e:
                logger.error(f"Error generating portfolio chart: {e}")

            # 5. Check for asset card triggers (Modification/Details context)
            try:
                if self._should_show_asset_card(response, context):
                    asset_cards = await self._generate_asset_cards(context, user_id, response)
                    ui_components.extend(asset_cards)
            except Exception as e:
                logger.error(f"Error generating asset cards: {e}")
            
            # Append UI component JSON to response if any
            if ui_components:
                import json
                # Format as XML tags for frontend
                # <WIDGET:TYPE data="{json_data}" />
                widgets_str = ""
                for comp in ui_components:
                    c_type = comp["type"]
                    # Serialize data to JSON and escape for HTML attribute
                    # We use json.dumps ensures it's a valid JSON string
                    # Then we replace " with &quot; to fit in the attribute
                    c_data_json = json.dumps(comp["data"], ensure_ascii=False, default=str)
                    c_data_escaped = c_data_json.replace('"', '&quot;')
                    widgets_str += f'\n\n<WIDGET:{c_type} data="{c_data_escaped}" />'
                
                enhanced_response = response + widgets_str
                
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
    
    def _should_show_action_plan_card(
        self, 
        response: str, 
        context: ConversationContext
    ) -> bool:
        """Determine if action PLAN card should be shown."""
        # Keywords specifically for the full plan - MUST match orchestrator pattern
        plan_keywords = [
            # Common patterns
            "行动方案", "执行方案", "理财计划", "规划建议", "具体方案", "Action Plan",
            "生成方案", "看看我的方案", "我的方案",
            # Protection / Insurance
            "保障方案", "家庭保障", "财富保障", "保险方案",
            # Investment / Growth
            "投资方案", "增值方案", "财富增值",
            # Planning / General
            "规划方案", "做个方案", "制定方案", "给我一个方案",
            # Debt
            "负债优化", "债务方案",
            # Real estate
            "房产方案", "房产规划"
        ]
        
        # Check ALL sources: response OR user's last message
        check_text = response
        if context.get_recent_messages(1):
            last_user_msg = context.get_recent_messages(1)[0]['content']
            check_text += " " + last_user_msg
            
        matches = [kw for kw in plan_keywords if kw in check_text]
        should_show = len(matches) > 0
        
        if should_show:
            logger.info(f"👀 [UI_INJECTOR] ActionPlanCard trigger matched: {matches}")
        else:
            logger.debug(f"👀 [UI_INJECTOR] ActionPlanCard NOT matched. Text len: {len(check_text)}")
            
        return should_show

    def _should_show_action_cards(
        self, 
        response: str, 
        context: ConversationContext
    ) -> bool:
        """Determine if simple action cards should be shown."""
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
        user_id: int,
        response: str
    ) -> list[dict[str, Any]]:
        """Generate valuation cards for real estate assets."""
        cards = []
        
        for asset in context.extracted_assets:
            if asset.get("type") == "real_estate":
                # FILTER: Only show card if asset name is mentioned OR asset is NOT confirmed
                # This prevents showing all cards repeatedly
                name = asset.get("name", "房产")
                data_location = asset.get("extra_data", {}).get("location", "")
                
                is_mentioned = (name in response) or (data_location and data_location in response)
                is_unconfirmed = not asset.get("is_confirmed", False)
                
                if not (is_mentioned or is_unconfirmed):
                    continue

                # Calculate derived data locally since we need raw dict
                price = asset.get("value", 0)
                area = asset.get("extra_data", {}).get("area", 0)
                location = data_location if data_location else name
                price_per_sqm = price / area if area > 0 else 0
                
                # Heuristic: Fix unit mismatch (Wan vs Yuan)
                # If unit price is unreasonably low (< 2000) AND total value is small (< 100000),
                # it's definitely "Wan" units.
                # e.g. 560 (Wan) / 80 = 7. 560 < 100000. -> Scale to 5,600,000
                # e.g. 150,000 (Yuan) / 100 = 1500. 150,000 > 100000. -> Don't scale.
                if price_per_sqm > 0 and price_per_sqm < 2000 and price < 100000:
                    price = price * 10000
                    price_per_sqm = price_per_sqm * 10000
                
                card_data = {
                    "id": asset.get("id"),
                    "price": price,
                    "area": area,
                    "location": location,
                    "price_per_sqm": price_per_sqm,
                    "confidence": 0.8,  # Default
                    "status": "completed" if asset.get("is_confirmed") else "active"
                }
                
                cards.append({
                    "type": "VALUATION_CARD",
                    "data": card_data
                })
        
        return cards
    
    async def _generate_action_plan_cards(
        self, 
        context: ConversationContext,
        user_id: int,
        focus_area: str | None = None
    ) -> list[dict[str, Any]]:
        """Generate action PLAN card by fetching latest plan or generating a new one."""
        cards = []
        try:
            from app.services.action_reasoner import get_action_reasoner
            action_reasoner = get_action_reasoner()
            
            # Convert string to Enum if provided
            category_enum = None
            if focus_area:
                try:
                    category_enum = ActionCategory(focus_area)
                except ValueError:
                    logger.warning(f"Invalid focus_area: {focus_area}")
            
            # Fetch or Generate plan
            # generate_plan will check for existing active plans first if check_existing=True
            plans, status = await action_reasoner.generate_plan(
                user_id=user_id, 
                focus_area=category_enum,
                check_existing=True
            )
            
            if plans:
                # Use the returned plan (either existing or newly generated)
                latest_plan = plans[0]
                
                # Convert to dictionary format expected by frontend
                plan_data = latest_plan.model_dump()
                
                # Ensure enums are converted to strings
                if hasattr(latest_plan, 'category') and hasattr(latest_plan.category, 'value'):
                     plan_data['category'] = latest_plan.category.value
                if hasattr(latest_plan, 'priority') and hasattr(latest_plan.priority, 'value'):
                     plan_data['priority'] = latest_plan.priority.value
                
                cards.append({
                    "type": "ACTION_PLAN_CARD",
                    "data": plan_data
                })
                logger.info(f"✅ Injected ACTION_PLAN_CARD for user {user_id} (status={status})")
                
        except Exception as e:
            logger.error(f"Error generating action plan cards: {e}")
            
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
                # Construct dict directly
                card_data = {
                    "type": warning.get("type", "general"),
                    "title": warning.get("title", "建议"),
                    "description": warning.get("recommendation", ""),
                    "priority": self._map_severity(warning.get("severity", "medium")),
                    "reason": warning.get("description", ""),
                    "contact_info": None,
                    "provider_info": None
                }
                
                cards.append({
                    "type": "ACTION_CARD",
                    "data": card_data
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

    def _should_show_asset_card(
        self, 
        response: str, 
        context: ConversationContext
    ) -> bool:
        """Determine if individual asset cards should be shown."""
        # Show when discussing specific assets updates or details
        keywords = ["修改", "更新", "调整", "确认", "资产信息", "资产详情"]
        return any(kw in response for kw in keywords)

    async def _generate_asset_cards(
        self, 
        context: ConversationContext,
        user_id: int,
        response: str
    ) -> list[dict[str, Any]]:
        """Generate asset cards for relevant assets in context."""
        cards = []
        
        # Simple heuristic: If response mentions an asset name, show its card
        # Or if it's a general "update asset" context, maybe show recently added/modified ones?
        # For now, let's match asset names in response or last user message
        
        check_text = response
        if context.get_recent_messages(1):
             check_text += " " + context.get_recent_messages(1)[0]['content']
             
        for asset in context.extracted_assets:
            if asset.get("name") and asset.get("name") in check_text:
                # Avoid duplicates if ValuationCard already handled it (Real Estate)
                # But ValuationCard is special. ASSET_CARD is generic.
                # If it is real_estate, prefer ValuationCard?
                # The requirements say ValuationCard for Real Estate.
                if asset.get("type") == "real_estate" and "估值" in check_text:
                    continue
                
                card_data = {
                    "id": asset.get("id"),
                    "name": asset.get("name"),
                    "value": asset.get("value"),
                    "type": asset.get("type", "unknown"),
                    "risk_level": "medium", # Placeholder or derived
                    "tags": [],
                    "privacy_mode": False
                }
                
                cards.append({
                    "type": "ASSET_CARD",
                    "data": card_data
                })
        
        return cards
    
    async def generate_widgets_from_tool(
        self,
        tool_call: dict[str, Any],
        context: ConversationContext,
        user_id: int
    ) -> list[dict[str, Any]]:
        """
        Generate widgets based on explicit tool call from LLM.
        
        Args:
            tool_call: Dictionary with 'name' and 'args'
            context: Conversation context
            user_id: User ID
            
        Returns:
            List of component data dicts
        """
        tool_name = tool_call.get("name")
        args = tool_call.get("args", {})
        
        components = []
        logger.info(f"🛠️ Handling Tool Call: {tool_name} args={args}")
        
        try:
            if tool_name == "ShowValuationCard":
                # Reuse logic but ignore response-text matching
                # Pass explicit 'True' to force generation? 
                # _generate_valuation_cards relies on context.extracted_assets
                # We can just call it and filter results.
                # Passing response="" will skip the "mentioned" check?
                # Wait, _generate_valuation_cards creates cards for asserted assets.
                # Logic: is_mentioned = (name in response) ...
                # If response is empty, is_mentioned is False.
                # But we want to FORCE show it.
                # Update: Use a special flag or just duplicate the valid logic for tools.
                # Let's clean up _generate_valuation_cards to take an optional 'force' flag?
                # Or just implement specific logic here.
                
                for asset in context.extracted_assets:
                    if asset.get("type") == "real_estate":
                        # Check ID filter
                        if args.get("asset_id") is not None and asset.get("id") != args["asset_id"]:
                            continue
                        
                        # Generate data manually to ensure it works without text matching
                        data_location = asset.get("extra_data", {}).get("location", "")
                        name = asset.get("name", "房产")
                        
                        price = asset.get("value", 0)
                        area = asset.get("extra_data", {}).get("area", 0)
                        location = data_location if data_location else name
                        price_per_sqm = price / area if area > 0 else 0
                        
                        # Unit heuristic
                        if price_per_sqm > 0 and price_per_sqm < 2000 and price < 100000:
                            price = price * 10000
                            price_per_sqm = price_per_sqm * 10000
                        
                        card_data = {
                            "id": asset.get("id"),
                            "price": price,
                            "area": area,
                            "location": location,
                            "price_per_sqm": price_per_sqm,
                            "confidence": 0.8,
                            "status": "completed" if asset.get("is_confirmed") else "active"
                        }
                        
                        components.append({
                            "type": "VALUATION_CARD",
                            "data": card_data
                        })

            elif tool_name == "ShowActionPlan":
                # Handle dynamic generation with focus area
                focus_area = args.get("focus_area")
                plan_cards = await self._generate_action_plan_cards(context, user_id, focus_area)
                components.extend(plan_cards)
                
            elif tool_name == "ShowPortfolioChart":
                chart = await self._generate_portfolio_chart(context, user_id)
                if chart:
                    components.append(chart)
                    
            elif tool_name == "ShowActionCard":
                # Filter risks based on tool args
                target_type = args.get("action_type")
                target_risk = args.get("risk_type")
                
                if context.portfolio_analysis:
                    risk_warnings = context.portfolio_analysis.get("risk_warnings", [])
                    for warning in risk_warnings:
                        # Match logic
                        # If risk_type specified, match it
                        if target_risk and warning.get("type") != target_risk:
                            continue
                            
                        # If action_type specified, loose match?
                        # Warning doesn't have action_type, it has 'type' (risk type).
                        # We map severity/type to action card.
                        
                        card_data = {
                            "type": warning.get("type", "general"),
                            "title": warning.get("title", "建议"),
                            "description": warning.get("recommendation", ""),
                            "priority": self._map_severity(warning.get("severity", "medium")),
                            "reason": warning.get("description", ""),
                            "contact_info": None,
                            "provider_info": None
                        }
                        components.append({
                             "type": "ACTION_CARD",
                             "data": card_data
                        })
                        
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}")
            
        return components


# Singleton instance
_ui_injector: UIComponentInjector | None = None


def get_ui_component_injector() -> UIComponentInjector:
    """Get or create UIComponentInjector instance."""
    global _ui_injector
    if _ui_injector is None:
        _ui_injector = UIComponentInjector()
    return _ui_injector
