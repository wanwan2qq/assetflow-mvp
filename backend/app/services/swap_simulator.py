"""
Property Swap Simulator - Property Exchange Analysis

This service simulates property swap scenarios:
- Sell current property, buy target property
- Calculate cash gap and transaction costs
- Project monthly payment changes
- Analyze asset allocation changes

AI Coding Guidance:
- Use PropertyValuationService for market estimates
- Include all transaction costs (taxes, fees)
- Consider loan balance and new loan requirements
"""

import logging
from datetime import datetime
from typing import Any

from app.models.real_estate import (
    RealEstateAsset,
    SwapSimulationResult,
    PropertyUsage,
)
from app.services.property_valuation import get_property_valuation_service

logger = logging.getLogger(__name__)


class PropertySwapSimulator:
    """
    房产置换推演器
    
    模拟"卖旧买新"置换场景，计算资金缺口、
    月供变化和资产配置影响。
    """
    
    # 交易成本参数
    TRANSACTION_COSTS = {
        # 卖方成本
        "sell_agent_fee": 0.01,     # 中介费 1%
        "sell_tax_rate": 0.01,      # 增值税等 (简化) 1%
        
        # 买方成本
        "buy_agent_fee": 0.01,      # 中介费 1%
        "buy_deed_tax": 0.015,      # 契税 1.5% (首套90平以上)
        "buy_other_fees": 0.005,    # 其他费用 0.5%
    }
    
    # 贷款参数
    LOAN_PARAMS = {
        "max_ltv": 0.7,             # 最高贷款比例 70%
        "default_rate": 0.035,      # 默认利率 3.5%
        "default_years": 30,        # 默认贷款年限
        "min_down_payment": 0.3,    # 最低首付 30%
    }
    
    def __init__(self):
        self.valuation_service = get_property_valuation_service()
    
    def simulate_swap(
        self,
        current_property: RealEstateAsset,
        target_property: RealEstateAsset,
        user_assets: list[dict] | None = None,
        user_profile: dict | None = None
    ) -> SwapSimulationResult:
        """
        模拟房产置换
        
        Args:
            current_property: 当前房产 (待售)
            target_property: 目标房产 (待购)
            user_assets: 用户其他资产列表
            user_profile: 用户画像
            
        Returns:
            SwapSimulationResult with comprehensive analysis
        """
        # 计算卖出所得
        sell_result = self._calculate_sell_proceeds(current_property)
        
        # 计算购入成本
        buy_result = self._calculate_buy_cost(target_property)
        
        # 计算资金缺口
        cash_gap_result = self.calculate_cash_gap(
            sell_proceeds=sell_result["net_proceeds"],
            buy_cost=buy_result["total_cost"],
            transaction_costs=sell_result["costs"] + buy_result["costs"]
        )
        
        # 计算新贷款月供
        new_loan_amount = max(0, buy_result["total_cost"] - sell_result["net_proceeds"])
        new_monthly_payment = self._calculate_monthly_payment(new_loan_amount)
        
        # 月供变化
        payment_projection = self.project_monthly_payment_change(
            current_monthly_payment=current_property.monthly_payment,
            new_monthly_payment=new_monthly_payment
        )
        
        # 资产配置变化
        before_allocation, after_allocation = self._analyze_allocation_change(
            current_property=current_property,
            target_property=target_property,
            new_loan=new_loan_amount,
            user_assets=user_assets
        )
        
        # 可行性评估
        is_feasible, risk_warnings, recommendations = self._assess_feasibility(
            cash_gap=cash_gap_result["cash_gap"],
            new_monthly_payment=new_monthly_payment,
            user_profile=user_profile,
            user_assets=user_assets
        )
        
        return SwapSimulationResult(
            is_feasible=is_feasible,
            sell_proceeds=sell_result["net_proceeds"],
            buy_cost=buy_result["total_cost"],
            transaction_costs=sell_result["costs"] + buy_result["costs"],
            cash_gap=cash_gap_result["cash_gap"],
            current_monthly_payment=current_property.monthly_payment,
            new_monthly_payment=new_monthly_payment,
            payment_change=payment_projection["change"],
            before_allocation=before_allocation,
            after_allocation=after_allocation,
            risk_warnings=risk_warnings,
            recommendations=recommendations
        )
    
    def calculate_cash_gap(
        self,
        sell_proceeds: float,
        buy_cost: float,
        transaction_costs: float
    ) -> dict:
        """
        计算置换资金缺口
        
        Args:
            sell_proceeds: 卖出净所得
            buy_cost: 购入总成本
            transaction_costs: 交易成本
            
        Returns:
            Dict with cash_gap and breakdown
        """
        total_needed = buy_cost + transaction_costs
        cash_gap = total_needed - sell_proceeds
        
        return {
            "cash_gap": cash_gap,
            "sell_proceeds": sell_proceeds,
            "buy_cost": buy_cost,
            "transaction_costs": transaction_costs,
            "total_needed": total_needed,
            "needs_additional_funds": cash_gap > 0
        }
    
    def project_monthly_payment_change(
        self,
        current_monthly_payment: float,
        new_monthly_payment: float
    ) -> dict:
        """
        预测月供变化
        
        Args:
            current_monthly_payment: 当前月供
            new_monthly_payment: 新月供
            
        Returns:
            Dict with payment change analysis
        """
        change = new_monthly_payment - current_monthly_payment
        change_percent = (change / current_monthly_payment * 100) if current_monthly_payment > 0 else 0
        
        return {
            "current": current_monthly_payment,
            "new": new_monthly_payment,
            "change": change,
            "change_percent": change_percent,
            "impact": self._assess_payment_impact(change, current_monthly_payment)
        }
    
    def _calculate_sell_proceeds(self, property: RealEstateAsset) -> dict:
        """计算卖出净所得"""
        sell_price = property.current_value
        
        # 交易成本
        agent_fee = sell_price * self.TRANSACTION_COSTS["sell_agent_fee"]
        tax = sell_price * self.TRANSACTION_COSTS["sell_tax_rate"]
        
        # 偿还贷款
        loan_payoff = property.loan_balance
        
        # 净所得
        total_costs = agent_fee + tax + loan_payoff
        net_proceeds = sell_price - total_costs
        
        return {
            "sell_price": sell_price,
            "agent_fee": agent_fee,
            "tax": tax,
            "loan_payoff": loan_payoff,
            "costs": agent_fee + tax,
            "net_proceeds": net_proceeds
        }
    
    def _calculate_buy_cost(self, property: RealEstateAsset) -> dict:
        """计算购入总成本"""
        buy_price = property.current_value
        
        # 交易成本
        agent_fee = buy_price * self.TRANSACTION_COSTS["buy_agent_fee"]
        deed_tax = buy_price * self.TRANSACTION_COSTS["buy_deed_tax"]
        other_fees = buy_price * self.TRANSACTION_COSTS["buy_other_fees"]
        
        total_costs = agent_fee + deed_tax + other_fees
        total_cost = buy_price + total_costs
        
        return {
            "buy_price": buy_price,
            "agent_fee": agent_fee,
            "deed_tax": deed_tax,
            "other_fees": other_fees,
            "costs": total_costs,
            "total_cost": total_cost
        }
    
    def _calculate_monthly_payment(
        self,
        loan_amount: float,
        rate: float | None = None,
        years: int | None = None
    ) -> float:
        """
        计算月供 (等额本息)
        
        Args:
            loan_amount: 贷款金额
            rate: 年利率 (如 3.5 表示 3.5%)
            years: 贷款年限
            
        Returns:
            月供金额
        """
        if loan_amount <= 0:
            return 0
        
        rate = rate or self.LOAN_PARAMS["default_rate"]
        years = years or self.LOAN_PARAMS["default_years"]
        
        # 月利率
        monthly_rate = rate / 100 / 12
        # 总期数
        n = years * 12
        
        # 等额本息公式
        if monthly_rate > 0:
            payment = loan_amount * monthly_rate * (1 + monthly_rate) ** n / ((1 + monthly_rate) ** n - 1)
        else:
            payment = loan_amount / n
        
        return round(payment, 2)
    
    def _analyze_allocation_change(
        self,
        current_property: RealEstateAsset,
        target_property: RealEstateAsset,
        new_loan: float,
        user_assets: list[dict] | None
    ) -> tuple[dict, dict]:
        """分析资产配置变化"""
        # 计算其他资产总值
        other_assets = 0
        cash_assets = 0
        if user_assets:
            for asset in user_assets:
                asset_type = asset.get("type", "other")
                value = asset.get("value", 0)
                if asset_type == "cash":
                    cash_assets += value
                else:
                    other_assets += value
        
        # 置换前
        current_net = current_property.current_value - current_property.loan_balance
        before_total = current_net + other_assets + cash_assets
        
        before_allocation = {
            "real_estate": round(current_net / before_total * 100, 1) if before_total > 0 else 0,
            "cash": round(cash_assets / before_total * 100, 1) if before_total > 0 else 0,
            "other": round(other_assets / before_total * 100, 1) if before_total > 0 else 0,
        }
        
        # 置换后
        target_net = target_property.current_value - new_loan
        # 假设用现金补足差额
        cash_used = max(0, new_loan - (current_property.current_value - current_property.loan_balance))
        after_cash = max(0, cash_assets - cash_used)
        after_total = target_net + other_assets + after_cash
        
        after_allocation = {
            "real_estate": round(target_net / after_total * 100, 1) if after_total > 0 else 0,
            "cash": round(after_cash / after_total * 100, 1) if after_total > 0 else 0,
            "other": round(other_assets / after_total * 100, 1) if after_total > 0 else 0,
        }
        
        return before_allocation, after_allocation
    
    def _assess_feasibility(
        self,
        cash_gap: float,
        new_monthly_payment: float,
        user_profile: dict | None,
        user_assets: list[dict] | None
    ) -> tuple[bool, list[str], list[str]]:
        """评估置换可行性"""
        risk_warnings = []
        recommendations = []
        is_feasible = True
        
        # 检查现金缺口
        if cash_gap > 0:
            # 检查是否有足够现金
            available_cash = 0
            if user_assets:
                for asset in user_assets:
                    if asset.get("type") == "cash":
                        available_cash += asset.get("value", 0)
            
            if cash_gap > available_cash:
                is_feasible = False
                risk_warnings.append(f"资金缺口{cash_gap/10000:.0f}万元，超过可用现金{available_cash/10000:.0f}万元")
                recommendations.append("建议增加首付来源或选择更低价位房产")
            else:
                recommendations.append(f"需要动用{cash_gap/10000:.0f}万元现金储备")
        
        # 检查月供压力
        if user_profile:
            monthly_income = user_profile.get("monthly_income", 0)
            if monthly_income > 0:
                pressure_ratio = new_monthly_payment / monthly_income
                if pressure_ratio > 0.5:
                    risk_warnings.append(f"月供占收入比例达{pressure_ratio:.0%}，可能造成较大压力")
                    if pressure_ratio > 0.7:
                        is_feasible = False
                        recommendations.append("建议降低贷款金额或延长还款期限")
        
        # 正面建议
        if is_feasible and not risk_warnings:
            recommendations.append("置换方案可行，建议与银行确认贷款额度后推进")
        
        return is_feasible, risk_warnings, recommendations
    
    def _assess_payment_impact(self, change: float, current: float) -> str:
        """评估月供变化影响"""
        if current <= 0:
            return "neutral"
        
        change_percent = abs(change / current)
        
        if change < 0:
            return "positive"  # 月供减少
        elif change_percent < 0.1:
            return "minimal"  # 变化小于10%
        elif change_percent < 0.3:
            return "moderate"  # 变化10-30%
        else:
            return "significant"  # 变化超过30%


# ============================================================================
# Singleton Factory
# ============================================================================

_swap_simulator: PropertySwapSimulator | None = None


def get_swap_simulator() -> PropertySwapSimulator:
    """获取 PropertySwapSimulator 单例"""
    global _swap_simulator
    if _swap_simulator is None:
        _swap_simulator = PropertySwapSimulator()
    return _swap_simulator
