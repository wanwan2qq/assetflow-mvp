"""
Real Estate Engine - Core Property Analysis Service

This service provides comprehensive property analysis including:
- Financial attribute analysis (equity, mortgage potential)
- Leverage potential calculation
- Rental yield analysis
- Property utilization strategies

AI Coding Guidance:
- Use PropertyValuationService for all valuation operations
- Call update_financial_attributes() after any value changes
- Include user profile for personalized strategy suggestions
"""

import logging
from typing import Any

from app.core.config import settings
from app.models.real_estate import (
    LeveragePotential,
    PropertyAnalysis,
    PropertyUsage,
    RealEstateAsset,
    RentalYield,
    UtilizationStrategy,
)
from app.services.property_valuation import get_property_valuation_service

logger = logging.getLogger(__name__)


class RealEstateEngine:
    """
    房产核心分析引擎
    
    提供房产金融属性分析、抵押潜力评估、
    租售比计算和运用策略建议。
    """
    
    # 银行常见抵押率上限
    MAX_LTV_RATIO = 0.7  # 70%
    
    # 月供压力阈值
    LOAN_PRESSURE_THRESHOLDS = {
        "low": 0.3,      # 低于30%
        "medium": 0.5,   # 30%-50%
        "high": 1.0,     # 高于50%
    }
    
    # 租售比评级阈值 (年化)
    RENTAL_YIELD_THRESHOLDS = {
        "low": 0.015,    # 低于1.5%
        "medium": 0.025, # 1.5%-2.5%
        "high": 0.04,    # 高于4%
    }
    
    def __init__(self):
        self.valuation_service = get_property_valuation_service()
    
    async def analyze_property(
        self, 
        property: RealEstateAsset,
        monthly_income: float | None = None
    ) -> PropertyAnalysis:
        """
        分析单个房产的金融属性
        
        Args:
            property: 房产资产
            monthly_income: 用户月收入 (用于计算月供压力)
            
        Returns:
            PropertyAnalysis with comprehensive analysis
        """
        # 确保计算字段已更新
        property.update_financial_attributes()
        
        # 计算抵押利用率
        max_mortgage = property.current_value * self.MAX_LTV_RATIO
        mortgage_utilization = property.loan_balance / max_mortgage if max_mortgage > 0 else 0
        
        # 计算月供压力
        loan_pressure = 0.0
        if monthly_income and monthly_income > 0:
            loan_pressure = property.monthly_payment / monthly_income
        
        # 评估集中风险
        concentration_risk = "low"  # 单个房产分析中暂不评估
        
        # 计算综合评分 (0-100)
        financial_score = self._calculate_financial_score(
            net_equity=property.net_equity or 0,
            mortgage_utilization=mortgage_utilization,
            rental_yield=property.rental_yield,
            loan_pressure=loan_pressure,
            appreciation_rate=property.get_appreciation_rate()
        )
        
        # 生成洞察
        insights = self._generate_property_insights(
            property=property,
            mortgage_utilization=mortgage_utilization,
            loan_pressure=loan_pressure
        )
        
        return PropertyAnalysis(
            property_id=property.id or 0,
            property_name=property.name,
            current_value=property.current_value,
            net_equity=property.net_equity or 0,
            value_appreciation=property.get_appreciation_rate(),
            mortgage_potential=property.mortgage_potential or 0,
            mortgage_utilization=mortgage_utilization,
            rental_yield=property.rental_yield,
            rental_income_potential=self._estimate_rental_potential(property),
            loan_pressure_ratio=loan_pressure,
            concentration_risk=concentration_risk,
            financial_score=financial_score,
            insights=insights
        )
    
    async def analyze_leverage_potential(
        self, 
        property: RealEstateAsset,
        current_loan: float | None = None
    ) -> LeveragePotential:
        """
        分析房产抵押潜力
        
        Args:
            property: 房产资产
            current_loan: 当前贷款余额 (可覆盖property中的值)
            
        Returns:
            LeveragePotential with mortgage analysis
        """
        property.update_financial_attributes()
        
        loan_balance = current_loan if current_loan is not None else property.loan_balance
        
        # 计算最大可贷额度
        max_mortgage = property.current_value * self.MAX_LTV_RATIO
        available_mortgage = max(0, max_mortgage - loan_balance)
        utilization_rate = loan_balance / max_mortgage if max_mortgage > 0 else 0
        
        # 生成策略建议
        strategies = []
        warnings = []
        
        if available_mortgage > 500000:  # 50万以上
            strategies.append(f"可申请约{available_mortgage/10000:.0f}万元抵押贷款")
            
            if property.usage == PropertyUsage.SELF_OCCUPIED:
                strategies.append("自住房抵押可用于子女教育、创业资金等长期规划")
            
            if utilization_rate < 0.3:
                strategies.append("当前杠杆使用率较低，有充足的资金腾挪空间")
        
        elif available_mortgage > 100000:  # 10-50万
            strategies.append(f"可申请约{available_mortgage/10000:.0f}万元抵押贷款")
            strategies.append("可用于应急资金储备或小额投资")
        
        else:
            strategies.append("当前抵押空间有限")
            if utilization_rate > 0.6:
                warnings.append("抵押率较高，建议逐步降低负债")
        
        # 风险提示
        if loan_balance > property.current_value * 0.5:
            warnings.append("贷款余额超过房产价值的50%，需关注还款压力")
        
        return LeveragePotential(
            property_value=property.current_value,
            current_loan=loan_balance,
            max_mortgage=max_mortgage,
            available_mortgage=available_mortgage,
            utilization_rate=utilization_rate,
            suggested_strategies=strategies,
            warnings=warnings
        )
    
    async def calculate_rental_yield(
        self, 
        property: RealEstateAsset,
        market_rent: float | None = None
    ) -> RentalYield:
        """
        计算租售比和租金收益
        
        Args:
            property: 房产资产
            market_rent: 市场租金 (如提供则与当前租金比较)
            
        Returns:
            RentalYield with rental analysis
        """
        property.update_financial_attributes()
        
        current_rent = property.monthly_rent
        
        # 估算市场租金 (如未提供)
        if market_rent is None:
            location = f"{property.city}{property.district or ''}"
            rent_estimate = await self.valuation_service.get_rental_estimate(
                location=location,
                area=property.area,
                bedrooms=property.bedrooms
            )
            market_rent = rent_estimate.monthly_rent
            city_avg_yield = rent_estimate.city_avg_yield
        else:
            city_avg_yield = None
        
        # 计算毛租金回报率
        gross_yield = 0.0
        if property.current_value > 0:
            rent_for_calc = current_rent or market_rent or 0
            gross_yield = (rent_for_calc * 12) / property.current_value
        
        # 计算净租金回报率 (扣除维护成本，约为毛租金的15%)
        net_yield = gross_yield * 0.85 if gross_yield > 0 else None
        
        # 评级
        yield_rating = "unknown"
        if gross_yield > 0:
            if gross_yield < self.RENTAL_YIELD_THRESHOLDS["low"]:
                yield_rating = "below_average"
            elif gross_yield > self.RENTAL_YIELD_THRESHOLDS["medium"]:
                yield_rating = "above_average"
            else:
                yield_rating = "average"
        
        return RentalYield(
            current_rent=current_rent,
            market_rent=market_rent,
            property_value=property.current_value,
            gross_yield=gross_yield,
            net_yield=net_yield,
            city_average_yield=city_avg_yield,
            yield_rating=yield_rating
        )
    
    def get_utilization_strategies(
        self, 
        property: RealEstateAsset,
        user_profile: dict | None = None
    ) -> list[UtilizationStrategy]:
        """
        生成房产运用策略建议
        
        Args:
            property: 房产资产
            user_profile: 用户画像 (风险偏好、收入等)
            
        Returns:
            List of UtilizationStrategy recommendations
        """
        property.update_financial_attributes()
        strategies = []
        
        risk_preference = (user_profile or {}).get("risk_preference", "moderate")
        
        # 策略1: 抵押贷款
        if (property.mortgage_potential or 0) > 500000:
            strategies.append(UtilizationStrategy(
                strategy_type="mortgage",
                title="抵押融资",
                description=f"可抵押约{(property.mortgage_potential or 0)/10000:.0f}万元，"
                           "用于投资理财或家庭规划",
                expected_benefit=property.mortgage_potential or 0,
                risk_level="low" if risk_preference == "conservative" else "medium",
                prerequisites=["需评估还款能力", "需银行审批"]
            ))
        
        # 策略2: 出租收益
        if property.usage == PropertyUsage.VACANT:
            estimated_annual_rent = property.current_value * 0.02  # 假设2%租售比
            strategies.append(UtilizationStrategy(
                strategy_type="rent",
                title="出租获取收益",
                description=f"预计年租金收入约{estimated_annual_rent/10000:.1f}万元",
                expected_benefit=estimated_annual_rent,
                risk_level="low",
                prerequisites=["需要装修整理", "需寻找租客"]
            ))
        
        # 策略3: 转按揭/换贷
        if property.loan_rate and property.loan_rate > 4.5:  # 利率较高
            current_interest = property.loan_balance * property.loan_rate / 100
            potential_interest = property.loan_balance * 3.5 / 100  # 假设新利率3.5%
            savings = current_interest - potential_interest
            if savings > 10000:
                strategies.append(UtilizationStrategy(
                    strategy_type="refinance",
                    title="转按揭降息",
                    description=f"转换到较低利率可每年节省约{savings/10000:.1f}万元利息",
                    expected_benefit=savings,
                    risk_level="low",
                    prerequisites=["需评估转按成本", "需银行审批新贷款"]
                ))
        
        # 策略4: 变现 (如果是投资房)
        if property.usage != PropertyUsage.SELF_OCCUPIED:
            appreciation = property.get_appreciation_rate()
            if appreciation and appreciation > 0.3:  # 增值超过30%
                strategies.append(UtilizationStrategy(
                    strategy_type="sell",
                    title="获利变现",
                    description=f"房产增值{appreciation:.0%}，可考虑择机变现锁定收益",
                    expected_benefit=property.net_equity or 0,
                    risk_level="medium",
                    prerequisites=["需评估税费成本", "需考虑再投资方向"]
                ))
        
        return strategies
    
    def _calculate_financial_score(
        self,
        net_equity: float,
        mortgage_utilization: float,
        rental_yield: float | None,
        loan_pressure: float,
        appreciation_rate: float | None
    ) -> float:
        """计算房产金融属性综合评分 (0-100)"""
        score = 50.0  # 基础分
        
        # 净值评分 (+0-20分)
        if net_equity > 3000000:
            score += 20
        elif net_equity > 1000000:
            score += 15
        elif net_equity > 500000:
            score += 10
        elif net_equity > 0:
            score += 5
        
        # 抵押利用率 (+0-15分，低利用率加分)
        if mortgage_utilization < 0.3:
            score += 15
        elif mortgage_utilization < 0.5:
            score += 10
        elif mortgage_utilization < 0.7:
            score += 5
        
        # 租售比 (+0-15分)
        if rental_yield:
            if rental_yield > 0.025:
                score += 15
            elif rental_yield > 0.015:
                score += 10
            elif rental_yield > 0.01:
                score += 5
        
        # 月供压力 (+0-15分，低压力加分)
        if loan_pressure < 0.2:
            score += 15
        elif loan_pressure < 0.3:
            score += 10
        elif loan_pressure < 0.5:
            score += 5
        
        # 增值率 (+0-10分)
        if appreciation_rate:
            if appreciation_rate > 0.3:
                score += 10
            elif appreciation_rate > 0.1:
                score += 5
        
        return min(100, max(0, score))
    
    def _generate_property_insights(
        self,
        property: RealEstateAsset,
        mortgage_utilization: float,
        loan_pressure: float
    ) -> list[dict]:
        """生成房产分析洞察"""
        insights = []
        
        # 净值洞察
        if (property.net_equity or 0) > 3000000:
            insights.append({
                "type": "positive",
                "title": "净值充足",
                "description": f"房产净值{(property.net_equity or 0)/10000:.0f}万元，是资产配置的重要锚点"
            })
        
        # 抵押潜力洞察
        if (property.mortgage_potential or 0) > 500000:
            insights.append({
                "type": "opportunity",
                "title": "抵押潜力可观",
                "description": f"可用抵押空间约{(property.mortgage_potential or 0)/10000:.0f}万元"
            })
        
        # 月供压力洞察
        if loan_pressure > 0.5:
            insights.append({
                "type": "warning",
                "title": "月供压力较大",
                "description": f"月供占收入{loan_pressure:.0%}，建议关注现金流管理"
            })
        
        # 租售比洞察
        if property.rental_yield:
            if property.rental_yield < 0.015:
                insights.append({
                    "type": "info",
                    "title": "租金收益偏低",
                    "description": "当前租售比低于市场平均水平"
                })
            elif property.rental_yield > 0.025:
                insights.append({
                    "type": "positive",
                    "title": "租金收益良好",
                    "description": "租售比高于市场平均水平"
                })
        
        return insights
    
    def _estimate_rental_potential(self, property: RealEstateAsset) -> float | None:
        """估算租金收益潜力"""
        if property.usage != PropertyUsage.RENTED:
            # 未出租的房产，估算潜在租金
            return property.current_value * 0.02  # 假设2%年租金回报
        return None


# ============================================================================
# Singleton Factory
# ============================================================================

_real_estate_engine: RealEstateEngine | None = None


def get_real_estate_engine() -> RealEstateEngine:
    """获取 RealEstateEngine 单例"""
    global _real_estate_engine
    if _real_estate_engine is None:
        _real_estate_engine = RealEstateEngine()
    return _real_estate_engine
