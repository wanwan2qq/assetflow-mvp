"""
Search tools for property valuation using Tavily API and mock data
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PropertySearchResult(BaseModel):
    """Result from property search"""

    success: bool
    estimated_price: float | None = None
    price_per_sqm: float | None = None
    source: str
    confidence: float = 0.0
    error: str | None = None
    fallback_to_manual: bool = False


class BasePropertySearchTool(BaseTool, ABC):
    """Base class for property search tools"""

    name: str = "property_search"
    description: str = "搜索房产市场价格信息"

    class Args(BaseModel):
        city: str = Field(description="城市名称，如'北京'、'上海'")
        community: str = Field(description="小区名称，如'天通苑'、'望京'")
        area: float = Field(description="房屋面积，单位平方米")

    args_schema = Args

    def _run(self, city: str, community: str, area: float) -> dict[str, Any]:
        """Execute property search"""
        try:
            result = self._search_property(city, community, area)
            return result.model_dump()
        except Exception as e:
            logger.error(f"Property search error: {e}")
            return PropertySearchResult(
                success=False, source="error", error=str(e), fallback_to_manual=True
            ).model_dump()

    @abstractmethod
    def _search_property(
        self, city: str, community: str, area: float
    ) -> PropertySearchResult:
        """Implement the actual search logic"""
        pass


class MockSearchTool(BasePropertySearchTool):
    """Mock search tool for development environment"""

    def __init__(self):
        super().__init__()
        # Use object.__setattr__ to bypass Pydantic validation for mock_data
        object.__setattr__(
            self,
            "mock_data",
            {
                "天通苑": {"price_per_sqm": 38000, "area": "昌平区"},
                "望京": {"price_per_sqm": 65000, "area": "朝阳区"},
                "国贸": {"price_per_sqm": 120000, "area": "朝阳区"},
                "陆家嘴": {"price_per_sqm": 150000, "area": "浦东新区"},
                "徐家汇": {"price_per_sqm": 90000, "area": "徐汇区"},
                "中关村": {"price_per_sqm": 80000, "area": "海淀区"},
                "三里屯": {"price_per_sqm": 110000, "area": "朝阳区"},
                "静安寺": {"price_per_sqm": 130000, "area": "静安区"},
            },
        )

    def _search_property(
        self, city: str, community: str, area: float
    ) -> PropertySearchResult:
        """Return mock property data"""
        logger.info(f"Mock search for {city} {community}, area: {area}sqm")

        # Find matching community data
        result_data = None
        for key, data in self.mock_data.items():
            if key in community or community in key:
                result_data = data
                break

        # Use default data if no match found
        if not result_data:
            result_data = {"price_per_sqm": 45000, "area": "未知"}

        # Apply conservative estimation (0.95 factor)
        price_per_sqm = result_data["price_per_sqm"]
        estimated_price = price_per_sqm * area * 0.95

        return PropertySearchResult(
            success=True,
            estimated_price=estimated_price,
            price_per_sqm=price_per_sqm,
            source="mock_data",
            confidence=0.8,
        )


class TavilySearchTool(BasePropertySearchTool):
    """Real Tavily API search tool for production"""

    def __init__(self, api_key: str):
        super().__init__()
        object.__setattr__(self, "api_key", api_key)

        # Import tavily only when needed
        try:
            from tavily import TavilyClient

            object.__setattr__(self, "client", TavilyClient(api_key=api_key))
        except ImportError:
            logger.error(
                "Tavily client not available. Install with: pip install tavily-python"
            )
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Tavily client: {e}")
            raise

    def _search_property(
        self, city: str, community: str, area: float
    ) -> PropertySearchResult:
        """Search property prices using Tavily API"""
        try:
            # Construct search query
            current_month = datetime.now().strftime("%Y年%m月")
            query = f"{city} {community} 二手房 挂牌均价 {current_month}"

            logger.info(f"Tavily search query: {query}")

            # Execute search
            search_results = self.client.search(
                query=query, search_depth="basic", max_results=5
            )

            if not search_results.get("results"):
                return PropertySearchResult(
                    success=False,
                    source="tavily_api",
                    error="No search results found",
                    fallback_to_manual=True,
                )

            # Extract price information from results
            price_info = self._extract_price_from_results(search_results["results"])

            if not price_info:
                return PropertySearchResult(
                    success=False,
                    source="tavily_api",
                    error="Could not extract price information",
                    fallback_to_manual=True,
                )

            # Apply conservative estimation (0.95 factor)
            estimated_price = price_info["price_per_sqm"] * area * 0.95

            return PropertySearchResult(
                success=True,
                estimated_price=estimated_price,
                price_per_sqm=price_info["price_per_sqm"],
                source="tavily_api",
                confidence=price_info.get("confidence", 0.7),
            )

        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return PropertySearchResult(
                success=False,
                source="tavily_api",
                error=str(e),
                fallback_to_manual=True,
            )

    def _extract_price_from_results(self, results: list) -> dict[str, Any] | None:
        """Extract price information from Tavily search results"""
        # This is a simplified extraction - in production, you'd want more sophisticated parsing
        for result in results:
            content = result.get("content", "").lower()

            # Look for price patterns (simplified)
            import re

            # Pattern for prices like "3.8万/平", "38000元/平"
            price_patterns = [
                r"(\d+\.?\d*)\s*万\s*/\s*平",  # X.X万/平
                r"(\d+)\s*元\s*/\s*平",  # X元/平
                r"均价\s*(\d+\.?\d*)\s*万",  # 均价X.X万
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    try:
                        price = float(matches[0])
                        # Convert to yuan per sqm if needed
                        if "万" in pattern:
                            price = price * 10000

                        return {"price_per_sqm": price, "confidence": 0.7}
                    except ValueError:
                        continue

        return None


def create_search_tool(
    use_mock: bool = True, tavily_api_key: str | None = None
) -> BasePropertySearchTool:
    """Factory function to create appropriate search tool"""
    if use_mock:
        logger.info("Using mock search tool for development")
        return MockSearchTool()
    else:
        if not tavily_api_key:
            logger.warning("No Tavily API key provided, falling back to mock")
            return MockSearchTool()

        logger.info("Using Tavily API search tool")
        return TavilySearchTool(tavily_api_key)
