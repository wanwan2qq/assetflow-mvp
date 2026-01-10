"""
Property-based tests for UI component generation service

**Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**
"""

import json
import re
from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from app.models.user import AssetType
from app.services.ui_component_service import UIComponentService, UIComponentType


class TestUIComponentGenerationProperties:
    """Property-based tests for UI component generation correctness"""

    def setup_method(self):
        """Set up test fixtures"""
        self.ui_service = UIComponentService()

    @given(
        price=st.floats(min_value=100000, max_value=50000000),
        area=st.floats(min_value=30, max_value=500),
        location=st.text(min_size=1, max_size=50),
        confidence=st.floats(min_value=0.1, max_value=1.0),
    )
    def test_valuation_card_generation_correctness(
        self, price: float, area: float, location: str, confidence: float
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any valid property valuation data, the generated valuation card
        should contain properly formatted widget tag with correct data structure.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Generate valuation card
        card_tag = self.ui_service.generate_valuation_card(
            price=price, area=area, location=location, confidence=confidence
        )

        # Verify tag format
        assert card_tag.startswith('<WIDGET:VALUATION_CARD data="')
        assert card_tag.endswith('">')

        # Extract and parse data
        data_match = re.search(r'data="([^"]*)"', card_tag)
        assert data_match is not None

        data_json = data_match.group(1)
        # Unescape HTML entities
        unescaped_json = data_json.replace("&quot;", '"')
        data = json.loads(unescaped_json)

        # Verify data structure and values
        assert "price" in data
        assert "area" in data
        assert "location" in data
        assert "price_per_sqm" in data
        assert "confidence" in data

        assert data["price"] == price
        assert data["area"] == area
        assert data["location"] == location
        assert data["confidence"] == confidence

        # Verify calculated price per square meter
        expected_price_per_sqm = price / area if area > 0 else 0
        assert abs(data["price_per_sqm"] - expected_price_per_sqm) < 0.01

    @given(
        action_type=st.text(min_size=1, max_size=20),
        title=st.text(min_size=1, max_size=100),
        description=st.text(min_size=1, max_size=500),
        priority=st.sampled_from(["high", "medium", "low"]),
    )
    def test_action_card_generation_correctness(
        self, action_type: str, title: str, description: str, priority: str
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any valid action card parameters, the generated action card
        should contain properly formatted widget tag with correct data structure.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Generate action card
        card_tag = self.ui_service.generate_action_card(
            action_type=action_type,
            title=title,
            description=description,
            priority=priority,
        )

        # Verify tag format
        assert card_tag.startswith('<WIDGET:ACTION_CARD data="')
        assert card_tag.endswith('">')

        # Extract and parse data
        data_match = re.search(r'data="([^"]*)"', card_tag)
        assert data_match is not None

        data_json = data_match.group(1)
        # Unescape HTML entities
        unescaped_json = data_json.replace("&quot;", '"')
        data = json.loads(unescaped_json)

        # Verify data structure and values
        assert "type" in data
        assert "title" in data
        assert "description" in data
        assert "priority" in data

        assert data["type"] == action_type
        assert data["title"] == title
        assert data["description"] == description
        assert data["priority"] == priority

    @given(
        assets_data=st.lists(
            st.tuples(
                st.sampled_from(
                    [AssetType.REAL_ESTATE, AssetType.CASH, AssetType.INVESTMENT]
                ),
                st.text(min_size=1, max_size=50),
                st.floats(min_value=1000, max_value=10000000),
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_portfolio_chart_generation_correctness(
        self, assets_data: list[tuple[AssetType, str, float]]
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any valid asset portfolio, the generated portfolio chart
        should contain properly formatted widget tag with correct data structure.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Create mock assets
        mock_assets = []
        for asset_type, name, value in assets_data:

            class MockAsset:
                def __init__(self, asset_type, name, value):
                    self.asset_type = asset_type
                    self.name = name
                    self.value = value

            mock_assets.append(MockAsset(asset_type, name, value))

        # Generate portfolio chart
        chart_tag = self.ui_service.generate_portfolio_chart(mock_assets)

        # Verify tag format
        assert chart_tag.startswith('<WIDGET:PORTFOLIO_CHART data="')
        assert chart_tag.endswith('">')

        # Extract and parse data
        data_match = re.search(r'data="([^"]*)"', chart_tag)
        assert data_match is not None

        data_json = data_match.group(1)
        # Unescape HTML entities
        unescaped_json = data_json.replace("&quot;", '"')
        data = json.loads(unescaped_json)

        # Verify data structure
        assert "assets" in data
        assert "total_value" in data
        assert "chart_type" in data

        # Verify total value calculation
        expected_total = sum(value for _, _, value in assets_data)
        assert abs(data["total_value"] - expected_total) < 0.01

        # Verify asset data
        assert len(data["assets"]) == len(assets_data)

        for i, (asset_type, name, value) in enumerate(assets_data):
            asset_data = data["assets"][i]
            assert asset_data["type"] == asset_type.value
            assert asset_data["name"] == name
            assert asset_data["value"] == value

            # Verify percentage calculation
            expected_percentage = (value / expected_total) * 100
            assert abs(asset_data["percentage"] - expected_percentage) < 0.1

    @given(response_text=st.text(min_size=10, max_size=1000))
    def test_ui_component_extraction_correctness(self, response_text: str):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any text containing valid widget tags, the extraction should
        correctly identify and parse all UI components.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Generate some valid widget tags with proper escaping
        valuation_tag = '<WIDGET:VALUATION_CARD data="{&quot;price&quot;: 1000000, &quot;area&quot;: 100}">'
        action_tag = '<WIDGET:ACTION_CARD data="{&quot;type&quot;: &quot;test&quot;, &quot;title&quot;: &quot;Test&quot;}">'
        chart_tag = '<WIDGET:PORTFOLIO_CHART data="{&quot;assets&quot;: [], &quot;total_value&quot;: 0}">'

        # Insert tags into response text
        test_text = f"{response_text[: len(response_text) // 3]}{valuation_tag}{response_text[len(response_text) // 3 : 2 * len(response_text) // 3]}{action_tag}{response_text[2 * len(response_text) // 3 :]}{chart_tag}"

        # Extract components
        components = self.ui_service.extract_ui_components(test_text)

        # Verify extraction
        assert len(components) == 3

        # Verify component types
        component_types = [comp.type for comp in components]
        assert UIComponentType.VALUATION_CARD in component_types
        assert UIComponentType.ACTION_CARD in component_types
        assert UIComponentType.PORTFOLIO_CHART in component_types

        # Verify positions are in order
        positions = [comp.position for comp in components]
        assert positions == sorted(positions)

    @given(
        base_response=st.text(min_size=10, max_size=500),
        components=st.lists(st.text(min_size=10, max_size=100), min_size=0, max_size=5),
    )
    def test_response_enhancement_correctness(
        self, base_response: str, components: list[str]
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any base response and list of UI components, the enhanced response
        should contain the original response plus all components.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Enhance response
        enhanced = self.ui_service.enhance_response_with_components(
            base_response, components
        )

        # Verify original response is preserved
        assert enhanced.startswith(base_response)

        # Verify all components are included
        for component in components:
            if component.strip():  # Only non-empty components should be included
                assert component in enhanced

        # If no components, response should be unchanged
        if not any(comp.strip() for comp in components):
            assert enhanced == base_response

    @given(
        extracted_assets=st.lists(
            st.fixed_dictionaries(
                {
                    "asset_type": st.sampled_from(
                        ["real_estate", "cash", "investment"]
                    ),
                    "name": st.text(min_size=1, max_size=50),
                    "value": st.floats(min_value=1000, max_value=10000000),
                }
            ),
            min_size=0,
            max_size=10,
        ),
        response_keywords=st.lists(
            st.sampled_from(["估值", "价值", "价格", "万元", "评估"]),
            min_size=0,
            max_size=3,
        ),
    )
    def test_valuation_card_decision_correctness(
        self, extracted_assets: list[dict[str, Any]], response_keywords: list[str]
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any combination of extracted assets and response content,
        the decision to generate valuation card should be consistent.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Create response with keywords
        response = f"测试响应 {' '.join(response_keywords)} 内容"

        # Check decision
        should_generate = self.ui_service.should_generate_valuation_card(
            response, extracted_assets
        )

        # Verify logic
        has_property = any(
            asset.get("asset_type") == "real_estate" for asset in extracted_assets
        )
        mentions_valuation = any(
            keyword in response for keyword in ["估值", "价值", "价格", "万元", "评估"]
        )

        expected_decision = has_property and mentions_valuation
        assert should_generate == expected_decision

    @given(
        extracted_assets=st.lists(
            st.fixed_dictionaries(
                {
                    "asset_type": st.sampled_from(
                        ["real_estate", "cash", "investment"]
                    ),
                    "name": st.text(min_size=1, max_size=50),
                    "value": st.floats(min_value=1000, max_value=10000000),
                }
            ),
            min_size=0,
            max_size=10,
        ),
        response_keywords=st.lists(
            st.sampled_from(["分析", "配置", "分布", "占比", "组合", "四象限"]),
            min_size=0,
            max_size=3,
        ),
        current_stage=st.sampled_from(
            ["initial", "property_collection", "asset_collection", "analysis"]
        ),
    )
    def test_portfolio_chart_decision_correctness(
        self,
        extracted_assets: list[dict[str, Any]],
        response_keywords: list[str],
        current_stage: str,
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any combination of assets, response content, and conversation stage,
        the decision to generate portfolio chart should be consistent.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Create response with keywords
        response = f"测试响应 {' '.join(response_keywords)} 内容"

        # Check decision
        should_generate = self.ui_service.should_generate_portfolio_chart(
            response, extracted_assets, current_stage
        )

        # Verify logic
        has_multiple_assets = len(extracted_assets) >= 2
        mentions_analysis = any(
            keyword in response
            for keyword in ["分析", "配置", "分布", "占比", "组合", "四象限"]
        )
        is_analysis_stage = current_stage == "analysis"

        expected_decision = (
            has_multiple_assets and mentions_analysis and is_analysis_stage
        )
        assert should_generate == expected_decision

    @given(
        response_keywords=st.lists(
            st.sampled_from(["风险", "建议", "改善", "优化", "不足", "过高", "偏低"]),
            min_size=0,
            max_size=3,
        ),
        current_stage=st.sampled_from(
            ["initial", "property_collection", "asset_collection", "analysis"]
        ),
    )
    def test_action_cards_decision_correctness(
        self, response_keywords: list[str], current_stage: str
    ):
        """
        **Feature: asset-flow-mvp, Property 5: UI组件标签生成正确性**

        For any response content and conversation stage,
        the decision to generate action cards should be consistent.

        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        # Create response with keywords
        response = f"测试响应 {' '.join(response_keywords)} 内容"

        # Check decision
        should_generate = self.ui_service.should_generate_action_cards(
            response, current_stage
        )

        # Verify logic
        mentions_risks = any(
            keyword in response
            for keyword in ["风险", "建议", "改善", "优化", "不足", "过高", "偏低"]
        )
        is_analysis_stage = current_stage == "analysis"

        expected_decision = is_analysis_stage or mentions_risks
        assert should_generate == expected_decision
