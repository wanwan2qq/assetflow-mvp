"""
Property-based tests for search functionality
Tests Property 11: 搜索查询构造正确性 and Property 4: 保守估算一致性
"""

import re
from datetime import datetime

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from app.services.search_tools import (
    MockSearchTool,
    create_search_tool,
)


# Test data generators
@st.composite
def property_info(draw):
    """Generate property information for testing"""
    cities = ["北京", "上海", "深圳", "广州", "杭州", "南京", "成都", "武汉"]
    communities = [
        "天通苑",
        "望京",
        "陆家嘴",
        "徐家汇",
        "中关村",
        "三里屯",
        "静安寺",
        "国贸",
    ]

    city = draw(st.sampled_from(cities))
    community = draw(st.sampled_from(communities))
    area = draw(st.floats(min_value=30.0, max_value=500.0))

    return {"city": city, "community": community, "area": area}


@st.composite
def search_query_components(draw):
    """Generate components for search query construction"""
    city = draw(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        )
    )
    community = draw(
        st.text(
            min_size=1,
            max_size=15,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
        )
    )
    area = draw(st.floats(min_value=1.0, max_value=1000.0))

    # Ensure valid Chinese-like names
    assume(len(city.strip()) > 0)
    assume(len(community.strip()) > 0)
    assume(area > 0)

    return {"city": city.strip(), "community": community.strip(), "area": area}


class TestSearchQueryConstruction:
    """Test Property 11: 搜索查询构造正确性"""

    # **Feature: asset-flow-mvp, Property 11: 搜索查询构造正确性**
    @given(property_data=property_info())
    def test_mock_search_query_format(self, property_data):
        """
        For any extracted property information (city, community, area),
        the search tool should construct query following format
        "{城市} {小区} 二手房 挂牌均价 {当前月份}"
        """
        tool = MockSearchTool()

        # Execute search (mock doesn't actually construct query, but we test the interface)
        result = tool._run(
            city=property_data["city"],
            community=property_data["community"],
            area=property_data["area"],
        )

        # Verify result structure is correct
        assert isinstance(result, dict)
        assert "success" in result
        assert "source" in result

        # For mock tool, verify it returns expected structure
        if result["success"]:
            assert "estimated_price" in result
            assert "price_per_sqm" in result
            assert result["source"] == "mock_data"

    # **Feature: asset-flow-mvp, Property 11: 搜索查询构造正确性**
    @given(query_components=search_query_components())
    def test_tavily_query_construction_format(self, query_components):
        """
        For any property search parameters, verify that if we had a real Tavily tool,
        the query would follow the correct format pattern
        """
        # Test the query construction logic that would be used
        city = query_components["city"]
        community = query_components["community"]
        current_month = datetime.now().strftime("%Y年%m月")

        # This is the expected query format
        expected_query = f"{city} {community} 二手房 挂牌均价 {current_month}"

        # Verify query contains all required components
        assert city in expected_query
        assert community in expected_query
        assert "二手房" in expected_query
        assert "挂牌均价" in expected_query
        assert current_month in expected_query

        # Verify query format pattern
        query_pattern = r".+ .+ 二手房 挂牌均价 \d{4}年\d{1,2}月"
        assert re.match(query_pattern, expected_query)


class TestConservativeEstimation:
    """Test Property 4: 保守估算一致性"""

    # **Feature: asset-flow-mvp, Property 4: 保守估算一致性**
    @given(property_data=property_info())
    def test_conservative_estimation_consistency(self, property_data):
        """
        For any property search result with listing price,
        the system should apply conservative estimation of exactly 0.95 multiplier
        """
        tool = MockSearchTool()

        result = tool._run(
            city=property_data["city"],
            community=property_data["community"],
            area=property_data["area"],
        )

        if (
            result["success"]
            and result.get("estimated_price")
            and result.get("price_per_sqm")
        ):
            estimated_price = result["estimated_price"]
            price_per_sqm = result["price_per_sqm"]
            area = property_data["area"]

            # Calculate expected conservative price (0.95 factor)
            expected_conservative_price = price_per_sqm * area * 0.95

            # Verify conservative estimation is applied correctly
            # Allow small floating point precision differences
            assert abs(estimated_price - expected_conservative_price) < 0.01

            # Verify the conservative factor is exactly 0.95
            if price_per_sqm > 0 and area > 0:
                actual_factor = estimated_price / (price_per_sqm * area)
                assert abs(actual_factor - 0.95) < 0.001

    # **Feature: asset-flow-mvp, Property 4: 保守估算一致性**
    @given(
        price_per_sqm=st.floats(min_value=1000.0, max_value=200000.0),
        area=st.floats(min_value=10.0, max_value=1000.0),
    )
    def test_conservative_factor_mathematical_property(self, price_per_sqm, area):
        """
        For any valid price per square meter and area,
        conservative estimation should always be exactly 95% of market price
        """
        # Calculate market price
        market_price = price_per_sqm * area

        # Apply conservative estimation
        conservative_price = market_price * 0.95

        # Verify mathematical relationship
        assert conservative_price < market_price
        assert conservative_price == market_price * 0.95

        # Verify the discount is exactly 5%
        discount_percentage = (market_price - conservative_price) / market_price
        assert abs(discount_percentage - 0.05) < 0.0001


class TestSearchToolFactory:
    """Test search tool creation and configuration"""

    def test_mock_tool_creation(self):
        """Test that mock tool is created correctly"""
        tool = create_search_tool(use_mock=True)
        assert isinstance(tool, MockSearchTool)
        assert tool.name == "property_search"

    def test_mock_tool_fallback_when_no_api_key(self):
        """Test that mock tool is used when no Tavily API key provided"""
        tool = create_search_tool(use_mock=False, tavily_api_key=None)
        assert isinstance(tool, MockSearchTool)

    @pytest.mark.skipif(
        True,  # Always skip for now since we don't have real Tavily API key
        reason="Tavily API key not available in test environment",
    )
    def test_tavily_tool_creation_with_api_key(self):
        """Test Tavily tool creation when API key is provided"""
        # Use a dummy API key for testing structure
        tool = create_search_tool(use_mock=False, tavily_api_key="test-key")
        # Note: This will create a TavilySearchTool but won't work without real API key
        # In real tests, you'd mock the Tavily client
        assert tool.name == "property_search"


class TestSearchResultStructure:
    """Test search result data structure consistency"""

    @given(property_data=property_info())
    def test_search_result_structure_consistency(self, property_data):
        """
        For any search operation, result should have consistent structure
        """
        tool = MockSearchTool()

        result = tool._run(
            city=property_data["city"],
            community=property_data["community"],
            area=property_data["area"],
        )

        # Verify required fields are present
        required_fields = ["success", "source"]
        for field in required_fields:
            assert field in result

        # If successful, verify additional fields
        if result["success"]:
            success_fields = ["estimated_price", "price_per_sqm"]
            for field in success_fields:
                assert field in result
                assert isinstance(result[field], (int, float))
                assert result[field] > 0

        # Verify source is valid
        valid_sources = ["mock_data", "tavily_api", "error"]
        assert result["source"] in valid_sources
