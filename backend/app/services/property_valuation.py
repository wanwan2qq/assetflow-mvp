"""
Property Valuation Service - Multi-tier Valuation Strategy

This service provides property valuation with automatic fallback:
- Tier 1: External API (Beike/Lianjia) - Most accurate, requires network
- Tier 2: Local benchmark data - Offline available
- Tier 3: LLM estimation - Based on location description
- Tier 4: User input validation - Fallback with reasonableness checks

AI Coding Guidance:
- Valuation automatically falls back from Tier 1 to Tier 4
- Local benchmark data should be updated quarterly
- LLM estimation confidence is capped at 0.6
- User input must pass validate_user_input
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

from app.core.config import settings
from app.models.real_estate import (
    MarketValuation,
    RentalEstimate,
    ValuationResult,
    ValueValidation,
)

logger = logging.getLogger(__name__)


# ============================================================================
# City Benchmark Data (Tier 2)
# ============================================================================

class CityBenchmarkData:
    """
    本地城市基准数据 (Tier 2)
    
    数据来源: 统计局公开数据 + 定期人工维护
    更新频率: 季度更新
    """
    
    # 主要城市住宅均价 (元/平方米) - 2024Q4 基准
    CITY_AVG_PRICES: dict[str, int] = {
        # 一线城市
        "北京": 65000,
        "上海": 62000,
        "深圳": 68000,
        "广州": 42000,
        
        # 准一线/新一线
        "杭州": 38000,
        "南京": 32000,
        "苏州": 28000,
        "成都": 18000,
        "武汉": 18000,
        "西安": 15000,
        "重庆": 12000,
        "天津": 22000,
        "宁波": 25000,
        "东莞": 25000,
        "佛山": 18000,
        "无锡": 20000,
        "合肥": 18000,
        "郑州": 13000,
        "长沙": 11000,
        "沈阳": 10000,
        "大连": 15000,
        "济南": 16000,
        
        # 二线城市
        "青岛": 18000,
        "厦门": 45000,
        "福州": 22000,
        "哈尔滨": 8000,
        "石家庄": 12000,
        "南昌": 12000,
        "昆明": 13000,
        "贵阳": 10000,
        "南宁": 11000,
        "海口": 18000,
        "三亚": 28000,
        
        # 默认 (三四线城市)
        "default": 8000,
    }
    
    # 区域调整系数 (热门区域溢价)
    DISTRICT_MULTIPLIERS: dict[str, dict[str, float]] = {
        "北京": {
            "海淀": 1.3,
            "朝阳": 1.2,
            "西城": 1.4,
            "东城": 1.35,
            "丰台": 0.85,
            "昌平": 0.7,
            "通州": 0.75,
            "大兴": 0.7,
            "顺义": 0.65,
            "房山": 0.55,
            "石景山": 0.9,
            "default": 1.0,
        },
        "上海": {
            "静安": 1.4,
            "黄浦": 1.5,
            "徐汇": 1.3,
            "长宁": 1.25,
            "浦东": 1.1,
            "闵行": 0.9,
            "宝山": 0.7,
            "嘉定": 0.65,
            "松江": 0.6,
            "青浦": 0.55,
            "default": 1.0,
        },
        "深圳": {
            "南山": 1.4,
            "福田": 1.3,
            "罗湖": 1.0,
            "宝安": 0.85,
            "龙岗": 0.7,
            "龙华": 0.8,
            "光明": 0.65,
            "坪山": 0.55,
            "default": 1.0,
        },
        "广州": {
            "天河": 1.4,
            "越秀": 1.3,
            "海珠": 1.1,
            "荔湾": 0.95,
            "白云": 0.8,
            "番禺": 0.75,
            "黄埔": 0.85,
            "default": 1.0,
        },
        "杭州": {
            "西湖": 1.4,
            "上城": 1.2,
            "拱墅": 1.0,
            "滨江": 1.15,
            "萧山": 0.8,
            "余杭": 0.75,
            "default": 1.0,
        },
    }
    
    # 房龄折旧率 (每年)
    AGE_DEPRECIATION_RATE: float = 0.005  # 0.5%/年
    
    # 户型调整 (相对于2居)
    BEDROOM_MULTIPLIERS: dict[int, float] = {
        1: 1.05,   # 小户型溢价
        2: 1.0,    # 基准
        3: 0.98,   # 略低
        4: 0.95,   # 大户型折价
        5: 0.92,
    }
    
    # 城市平均租售比 (年租金/房价)
    CITY_RENTAL_YIELDS: dict[str, float] = {
        "北京": 0.015,
        "上海": 0.015,
        "深圳": 0.012,
        "广州": 0.018,
        "杭州": 0.016,
        "成都": 0.022,
        "武汉": 0.020,
        "default": 0.02,
    }
    
    def estimate(
        self,
        city: str,
        district: str | None = None,
        area: float = 100,
        year_built: int | None = None,
        bedrooms: int = 2
    ) -> ValuationResult:
        """基于本地基准数据估值"""
        
        # 1. 获取城市基准价
        base_price = self.CITY_AVG_PRICES.get(city, self.CITY_AVG_PRICES["default"])
        
        # 2. 区域调整
        district_multiplier = 1.0
        if city in self.DISTRICT_MULTIPLIERS and district:
            city_districts = self.DISTRICT_MULTIPLIERS[city]
            district_multiplier = city_districts.get(
                district, 
                city_districts.get("default", 1.0)
            )
        
        # 3. 房龄调整
        age_multiplier = 1.0
        if year_built:
            age = datetime.now().year - year_built
            if age > 0:
                age_multiplier = max(0.7, 1 - age * self.AGE_DEPRECIATION_RATE)
        
        # 4. 户型调整
        bedroom_multiplier = self.BEDROOM_MULTIPLIERS.get(bedrooms, 1.0)
        
        # 计算最终价格
        unit_price = int(base_price * district_multiplier * age_multiplier * bedroom_multiplier)
        total_value = unit_price * area
        
        return ValuationResult(
            value=total_value,
            unit_price=unit_price,
            confidence=0.7,  # 本地数据置信度 70%
            source="local_benchmark",
            breakdown={
                "base_price": base_price,
                "district_multiplier": round(district_multiplier, 2),
                "age_multiplier": round(age_multiplier, 2),
                "bedroom_multiplier": bedroom_multiplier,
                "city": city,
                "district": district,
            }
        )
    
    def estimate_rent(
        self,
        city: str,
        area: float,
        bedrooms: int = 2
    ) -> RentalEstimate:
        """估算租金"""
        # 获取城市均价和租售比
        unit_price = self.CITY_AVG_PRICES.get(city, self.CITY_AVG_PRICES["default"])
        rental_yield = self.CITY_RENTAL_YIELDS.get(city, self.CITY_RENTAL_YIELDS["default"])
        
        # 计算月租金
        property_value = unit_price * area
        annual_rent = property_value * rental_yield
        monthly_rent = annual_rent / 12
        
        return RentalEstimate(
            monthly_rent=monthly_rent,
            confidence=0.65,
            source="local_benchmark",
            city_avg_yield=rental_yield
        )


# ============================================================================
# LLM Property Estimator (Tier 3)
# ============================================================================

class LLMPropertyEstimator:
    """
    LLM 智能估值 (Tier 3)
    
    利用 LLM 的知识库对位置进行理解和估价
    适用于没有精确位置数据时的智能推断
    """
    
    ESTIMATION_PROMPT = '''你是一位资深的房产评估师。请根据以下信息估算房产价值。

位置描述: {location}
面积: {area} 平方米
房产类型: {property_type}
建成年份: {year_built}
卧室数: {bedrooms}

请返回 JSON 格式:
{{
    "estimated_unit_price": <元/平方米，整数>,
    "confidence": <0-1置信度，保留2位小数>,
    "reasoning": "<估价理由，简短说明>",
    "price_range": {{
        "low": <最低总价>,
        "high": <最高总价>
    }}
}}

注意:
1. 根据你对该区域房价的了解进行估算
2. 如果位置不明确，给出保守估计和较低置信度
3. 考虑当地房价水平、地段、交通等因素
4. 只返回JSON，不要其他内容'''

    async def estimate(
        self,
        location: str,
        area: float,
        property_type: str = "住宅",
        year_built: int | None = None,
        bedrooms: int = 2
    ) -> ValuationResult:
        """使用 LLM 进行智能估值"""
        try:
            from app.core.dependencies import get_llm_provider
            from app.models.structured_output import parse_json_safely
            
            llm = get_llm_provider()
            prompt = self.ESTIMATION_PROMPT.format(
                location=location,
                area=area,
                property_type=property_type,
                year_built=year_built or "未知",
                bedrooms=bedrooms
            )
            
            response = await llm.generate([{"role": "user", "content": prompt}], "")
            result = parse_json_safely(response)
            
            if result and "estimated_unit_price" in result:
                unit_price = result.get("estimated_unit_price", 20000)
                return ValuationResult(
                    value=unit_price * area,
                    unit_price=unit_price,
                    confidence=min(0.6, result.get("confidence", 0.5)),  # LLM 最高 60% 置信度
                    source="llm_estimation",
                    reasoning=result.get("reasoning"),
                    price_range=result.get("price_range")
                )
            
        except Exception as e:
            logger.warning(f"LLM estimation failed: {e}")
        
        # LLM 失败时返回保守估计
        return ValuationResult(
            value=area * 15000,  # 保守均价
            unit_price=15000,
            confidence=0.3,
            source="llm_fallback",
            reasoning="LLM 估值失败，使用保守默认值"
        )


# ============================================================================
# Property Valuation Service (Main Entry)
# ============================================================================

class PropertyValuationService:
    """
    多层次房产估值服务
    
    估值策略优先级:
    1. 外部 API (如可用)
    2. 本地基准数据 (城市/区/小区级别)
    3. LLM 智能估算
    4. 用户输入校验
    """
    
    def __init__(self):
        self.benchmark_data = CityBenchmarkData()
        self.llm_estimator = LLMPropertyEstimator()
        self._cache: dict[str, tuple[MarketValuation, datetime]] = {}
    
    async def get_market_value(
        self, 
        location: str,
        area: float,
        property_type: str = "residential",
        year_built: int | None = None,
        bedrooms: int = 2,
        use_tier: int | None = None
    ) -> MarketValuation:
        """
        获取市场估值 (自动降级)
        
        Args:
            location: 位置描述 (如 "北京市朝阳区望京")
            area: 面积 (平方米)
            property_type: 房产类型
            year_built: 建成年份 (用于折旧调整)
            bedrooms: 卧室数
            use_tier: 强制使用指定层级 (1-4)
            
        Returns:
            MarketValuation with value, confidence, and source
        """
        # 检查缓存
        cache_key = f"{location}:{area}:{property_type}"
        if cache_key in self._cache:
            cached, timestamp = self._cache[cache_key]
            if datetime.utcnow() - timestamp < timedelta(seconds=settings.PROPERTY_VALUATION_CACHE_TTL):
                logger.debug(f"Using cached valuation for {location}")
                return cached
        
        tier_results: list[ValuationResult] = []
        final_result: ValuationResult | None = None
        
        # 提取城市和区域
        city = self._extract_city(location)
        district = self._extract_district(location)
        
        # Tier 1: 外部 API (如启用)
        if (use_tier is None or use_tier == 1) and settings.ENABLE_PROPERTY_VALUATION_API:
            api_result = await self._call_external_api(location, area, property_type)
            if api_result:
                tier_results.append(api_result)
                if final_result is None:
                    final_result = api_result
        
        # Tier 2: 本地基准数据
        if use_tier is None or use_tier == 2:
            benchmark_result = self.benchmark_data.estimate(
                city=city,
                district=district,
                area=area,
                year_built=year_built,
                bedrooms=bedrooms
            )
            tier_results.append(benchmark_result)
            if final_result is None:
                final_result = benchmark_result
        
        # Tier 3: LLM 智能估算 (如果 Tier 2 置信度较低或强制使用)
        if use_tier == 3 or (final_result and final_result.confidence < 0.5):
            llm_result = await self.llm_estimator.estimate(
                location=location,
                area=area,
                property_type=property_type,
                year_built=year_built,
                bedrooms=bedrooms
            )
            tier_results.append(llm_result)
            if use_tier == 3:
                final_result = llm_result
        
        # 确保有结果
        if final_result is None:
            final_result = ValuationResult(
                value=area * 15000,
                unit_price=15000,
                confidence=0.3,
                source="default_fallback",
                reasoning="无法获取估值，使用默认值"
            )
        
        # 获取租金估算
        rent_estimate = self.benchmark_data.estimate_rent(city, area, bedrooms)
        
        # 构建完整结果
        market_valuation = MarketValuation(
            value=final_result.value,
            unit_price=final_result.unit_price,
            confidence=final_result.confidence,
            source=final_result.source,
            tier_results=tier_results,
            estimated_rent=rent_estimate.monthly_rent,
            rental_yield=rent_estimate.city_avg_yield
        )
        
        # 缓存结果
        self._cache[cache_key] = (market_valuation, datetime.utcnow())
        
        return market_valuation
    
    async def get_rental_estimate(
        self, 
        location: str,
        area: float,
        bedrooms: int = 2
    ) -> RentalEstimate:
        """获取租金估价"""
        city = self._extract_city(location)
        return self.benchmark_data.estimate_rent(city, area, bedrooms)
    
    def validate_user_input(
        self,
        location: str,
        area: float,
        user_value: float,
        property_type: str = "residential"
    ) -> ValueValidation:
        """
        校验用户输入估值 (Tier 4)
        
        接受用户输入，但进行合理性校验
        """
        city = self._extract_city(location)
        district = self._extract_district(location)
        
        # 获取参考估值
        benchmark = self.benchmark_data.estimate(
            city=city,
            district=district,
            area=area
        )
        
        estimated_value = benchmark.value
        user_unit_price = user_value / area if area > 0 else 0
        
        # 计算偏差
        deviation = (user_value - estimated_value) / estimated_value if estimated_value > 0 else 0
        
        warnings = []
        if abs(deviation) > 0.5:
            warnings.append(f"您输入的估值与市场参考值偏差较大 ({deviation:+.0%})")
        
        if user_unit_price < 3000:
            warnings.append("单价低于 3000 元/平米，请确认是否正确")
        
        if user_unit_price > 200000:
            warnings.append("单价超过 20 万/平米，请确认是否正确")
        
        # 合理范围: 估算值的 ±50%
        reasonable_low = estimated_value * 0.5
        reasonable_high = estimated_value * 1.5
        
        return ValueValidation(
            is_reasonable=reasonable_low <= user_value <= reasonable_high,
            deviation_percent=deviation * 100,
            suggested_range=(reasonable_low, reasonable_high),
            warnings=warnings
        )
    
    async def _call_external_api(
        self,
        location: str,
        area: float,
        property_type: str
    ) -> ValuationResult | None:
        """调用外部 API (Tier 1)"""
        # TODO: 实现贝壳/链家 API 集成
        # 目前返回 None，表示 API 不可用
        logger.debug(f"External API not implemented for {location}")
        return None
    
    def _extract_city(self, location: str) -> str:
        """从位置描述中提取城市"""
        # 常见城市名称
        cities = list(CityBenchmarkData.CITY_AVG_PRICES.keys())
        cities.remove("default")
        
        for city in cities:
            if city in location:
                return city
        
        # 尝试匹配 "XX市" 格式
        match = re.search(r'(\w{2,4})市', location)
        if match:
            city_name = match.group(1)
            if city_name in cities:
                return city_name
            # 返回匹配到的城市名（可能不在列表中）
            return city_name
        
        return "default"
    
    def _extract_district(self, location: str) -> str | None:
        """从位置描述中提取区域"""
        # 尝试匹配 "XX区" 格式
        match = re.search(r'(\w{2,4})区', location)
        if match:
            return match.group(1)
        return None


# ============================================================================
# Singleton Factory
# ============================================================================

_valuation_service: PropertyValuationService | None = None


def get_property_valuation_service() -> PropertyValuationService:
    """获取 PropertyValuationService 单例"""
    global _valuation_service
    if _valuation_service is None:
        _valuation_service = PropertyValuationService()
    return _valuation_service
