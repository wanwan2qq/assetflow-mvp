"""
Real Estate Data Models

This module defines the first-class data models for real estate assets,
replacing the generic extra_data JSON field in UserAsset.

Includes:
- RealEstateAsset: Main property model with financial attributes
- PropertyAnalysis: Analysis result structure
- LeveragePotential: Mortgage potential analysis
- RentalYield: Rental income analysis
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field as PydanticField, field_validator
from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


# ============================================================================
# Enums
# ============================================================================

class PropertyType(str, Enum):
    """房产类型"""
    RESIDENTIAL = "residential"       # 住宅
    COMMERCIAL = "commercial"         # 商业
    OFFICE = "office"                 # 办公
    VILLA = "villa"                   # 别墅
    APARTMENT = "apartment"           # 公寓


class PropertyUsage(str, Enum):
    """房产用途"""
    SELF_OCCUPIED = "self_occupied"   # 自住
    RENTED = "rented"                 # 出租
    VACANT = "vacant"                 # 空置
    MIXED = "mixed"                   # 混合


class LoanType(str, Enum):
    """贷款类型"""
    COMMERCIAL = "commercial"         # 商业贷款
    PROVIDENT_FUND = "provident_fund" # 公积金贷款
    MIXED = "mixed"                   # 组合贷款
    NONE = "none"                     # 无贷款


# ============================================================================
# Database Model
# ============================================================================

class RealEstateAsset(SQLModel, table=True):
    """
    房产资产一等模型
    
    从 UserAsset.extra_data 中抽取为独立表，
    提供房产专属的金融属性建模。
    
    AI Coding Guidance:
    - 使用 update_financial_attributes() 更新计算字段
    - value_source 记录估值来源 (user_input/api/local_benchmark/llm)
    - legacy_asset_id 用于数据迁移追溯
    """
    __tablename__ = "real_estate_asset"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    # 基础信息
    name: str = Field(max_length=200)              # 房产名称/小区名
    # NOTE: Using str instead of Enum because database uses varchar columns
    property_type: str = Field(default="residential", max_length=20)
    usage: str = Field(default="self_occupied", max_length=20)
    
    # 位置信息
    city: str = Field(max_length=50)               # 城市
    district: str | None = Field(default=None, max_length=50)  # 区域
    address: str | None = Field(default=None, max_length=500)  # 详细地址
    
    # 物理属性
    area: float = Field(gt=0)                      # 建筑面积 (平方米)
    bedrooms: int = Field(default=2, ge=0)         # 卧室数
    year_built: int | None = Field(default=None)   # 建成年份
    
    # 价值信息
    purchase_price: float | None = Field(default=None)   # 购入价格
    purchase_date: datetime | None = Field(default=None) # 购入日期
    current_value: float = Field(gt=0)             # 当前估值
    value_source: str = Field(default="user_input")  # 估值来源
    value_confidence: float = Field(default=0.5, ge=0, le=1)  # 估值置信度
    value_updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 贷款信息
    # NOTE: Using str instead of Enum because database uses varchar columns
    loan_type: str = Field(default="none", max_length=20)
    loan_balance: float = Field(default=0, ge=0)   # 贷款余额
    monthly_payment: float = Field(default=0, ge=0)  # 月供
    loan_rate: float | None = Field(default=None)  # 贷款利率 (如 4.2 表示 4.2%)
    loan_remaining_months: int | None = Field(default=None)  # 剩余还款月数
    
    # 租赁信息
    monthly_rent: float | None = Field(default=None, ge=0)  # 月租金收入
    rental_yield: float | None = Field(default=None)        # 租售比 (年租金/房价)
    
    # 金融属性 (计算字段，存储缓存)
    mortgage_potential: float | None = Field(default=None)   # 可抵押潜力
    net_equity: float | None = Field(default=None)           # 净值
    
    # 扩展数据
    extra_data: dict | None = Field(sa_type=JSON, default=None)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关联原 UserAsset (用于数据迁移)
    legacy_asset_id: int | None = Field(default=None)
    
    def update_financial_attributes(self) -> None:
        """
        更新计算字段
        
        应在以下情况调用:
        - 创建新记录后
        - 估值变更后
        - 贷款余额变更后
        """
        # 净值 = 当前估值 - 贷款余额
        self.net_equity = self.current_value - self.loan_balance
        
        # 可抵押潜力 = 估值 * 70% - 贷款余额, 最小值为 0
        # 70% 是银行常见的抵押率上限
        max_mortgage = self.current_value * 0.7
        self.mortgage_potential = max(0, max_mortgage - self.loan_balance)
        
        # 租售比 = 年租金 / 当前估值
        if self.monthly_rent and self.monthly_rent > 0:
            self.rental_yield = (self.monthly_rent * 12) / self.current_value
        
        self.updated_at = datetime.utcnow()
    
    def get_loan_pressure_ratio(self, monthly_income: float | None = None) -> float:
        """
        计算月供压力比
        
        Args:
            monthly_income: 月收入，如不提供则返回 0
            
        Returns:
            月供占月收入的比例
        """
        if not monthly_income or monthly_income <= 0:
            return 0.0
        return self.monthly_payment / monthly_income
    
    def get_appreciation_rate(self) -> float | None:
        """
        计算增值率
        
        Returns:
            从购入到现在的增值率，如无购入价则返回 None
        """
        if not self.purchase_price or self.purchase_price <= 0:
            return None
        return (self.current_value - self.purchase_price) / self.purchase_price


# ============================================================================
# Analysis Result Models (Pydantic)
# ============================================================================

class ValuationResult(BaseModel):
    """估值结果"""
    value: float                    # 总估值
    unit_price: float               # 单价 (元/平方米)
    confidence: float               # 置信度 0-1
    source: str                     # 数据来源 (api/local_benchmark/llm/user_input)
    reasoning: str | None = None    # 估价理由 (LLM)
    price_range: dict | None = None # 价格区间 {"low": x, "high": y}
    breakdown: dict | None = None   # 计算分解 (本地基准)


class MarketValuation(BaseModel):
    """市场估值完整结果"""
    value: float
    unit_price: float
    confidence: float
    source: str
    
    # 多数据源比较
    tier_results: list[ValuationResult] = []
    
    # 租金相关
    estimated_rent: float | None = None
    rental_yield: float | None = None
    
    # 趋势
    yoy_change: float | None = None  # 同比变化


class RentalEstimate(BaseModel):
    """租金估价"""
    monthly_rent: float
    confidence: float
    source: str
    city_avg_yield: float | None = None


class PropertyAnalysis(BaseModel):
    """房产分析结果"""
    property_id: int
    property_name: str
    
    # 价值分析
    current_value: float
    net_equity: float
    value_appreciation: float | None = None
    
    # 金融潜力
    mortgage_potential: float
    mortgage_utilization: float = 0.0  # 已使用抵押比例
    
    # 收益分析
    rental_yield: float | None = None
    rental_income_potential: float | None = None
    
    # 风险评估
    loan_pressure_ratio: float = 0.0
    concentration_risk: str = "low"
    
    # 综合评分 (0-100)
    financial_score: float = 0.0
    
    # 建议
    insights: list[dict] = []


class LeveragePotential(BaseModel):
    """抵押潜力分析"""
    property_value: float
    current_loan: float
    max_mortgage: float          # 最大可贷额度 (估值*70%)
    available_mortgage: float    # 可用额度 (max - current)
    utilization_rate: float      # 使用率 (0-1)
    
    # 策略建议
    suggested_strategies: list[str] = []
    
    # 风险提示
    warnings: list[str] = []


class RentalYield(BaseModel):
    """租售比分析"""
    current_rent: float | None
    market_rent: float | None
    property_value: float
    gross_yield: float           # 毛租金回报率
    net_yield: float | None      # 净租金回报率
    
    city_average_yield: float | None = None
    yield_rating: str = "unknown"  # "above_average" / "below_average" / "average"


class UtilizationStrategy(BaseModel):
    """房产运用策略"""
    strategy_type: str           # "mortgage" / "rent" / "refinance" / "sell"
    title: str
    description: str
    expected_benefit: float
    risk_level: str              # "low" / "medium" / "high"
    prerequisites: list[str] = []


class SwapSimulationResult(BaseModel):
    """置换模拟结果"""
    is_feasible: bool
    
    # 资金分析
    sell_proceeds: float
    buy_cost: float
    transaction_costs: float
    cash_gap: float
    
    # 贷款变化
    current_monthly_payment: float
    new_monthly_payment: float
    payment_change: float
    
    # 资产配置变化
    before_allocation: dict[str, float] = {}
    after_allocation: dict[str, float] = {}
    
    # 风险评估
    risk_warnings: list[str] = []
    recommendations: list[str] = []


class ValueValidation(BaseModel):
    """用户输入估值校验结果"""
    is_reasonable: bool
    deviation_percent: float     # 与估算值偏差百分比
    suggested_range: tuple[float, float]
    warnings: list[str] = []
