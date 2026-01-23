# Phase 2: 房产核心引擎 - 技术方案

> **文档版本**: v1.0  
> **适用范围**: 开发者 & AI Coding Assistant  
> **预计工期**: 3 周 (W5-W7)  
> **依赖**: Phase 1 完成

---

## 0. 文档导读 (How to Use This Document)

### 对于开发者
- 阅读 **Section 1-2** 了解目标与模块设计
- 参考 **Section 3** 的数据模型设计
- 使用 **Section 4** 的代码示例进行开发

### 对于 AI Coding Assistant
- **任务拆解时**: 参考 Section 2 的模块职责定义
- **代码生成时**: 遵循 Section 3 的数据模型和接口契约
- **集成测试时**: 使用 Section 5 的验收清单

---

## 1. Phase 2 目标与原则 (Goals & Principles)

### 1.1 核心目标

| 编号 | 目标 | 说明 |
| :--- | :--- | :--- |
| **G1** | 房产一等数据模型 | 从 `UserAsset.extra_data` 中抽取房产属性为独立模型 |
| **G2** | 房产金融分析能力 | 实现抵押潜力、租售比、贷款压力等专业分析 |
| **G3** | 外部房价数据集成 | 接入第三方估值 API，提供市场参考 |
| **G4** | 房产置换推演 | 模拟以房换房、置换后资产配置变化 |
| **G5** | 四象限模型升级 | 房产从"保本升值"独立为"核心锚点" |

### 1.2 设计原则

| 原则 | 说明 |
| :--- | :--- |
| **房产为锚** | 房产不是"风险集中"，而是"策略起点" |
| **金融属性优先** | 关注抵押价值、现金流潜力，而非仅是估值 |
| **渐进式激活** | 通过 Feature Flag 控制新能力，默认关闭 |
| **向后兼容** | 原有 `PortfolioAnalyzer` 逻辑保留可用 |

---

## 2. 模块设计 (Module Design)

### 2.1 新增模块概览

```
Phase 2 新增模块
│
├── models/
│   └── real_estate.py          # 房产数据模型
│
├── services/
│   ├── real_estate_engine.py   # 房产核心分析引擎
│   ├── property_valuation.py   # 外部估值服务适配器
│   └── swap_simulator.py       # 房产置换推演器
│
└── core/
    └── config.py               # 新增 Feature Flags
```

### 2.2 模块职责详解

#### 2.2.1 RealEstateEngine (房产核心引擎)

**文件**: `backend/app/services/real_estate_engine.py`

**职责**:
- 分析房产金融属性（抵押潜力、租售比、贷款压力）
- 计算房产运用策略（抵押贷款、租赁收益）
- 为 `PortfolioAnalyzer` 提供房产专业分析数据

**关键方法**:
```python
class RealEstateEngine:
    async def analyze_property(
        self, 
        property: RealEstateAsset
    ) -> PropertyAnalysis:
        """分析单个房产的金融属性"""
        
    async def analyze_leverage_potential(
        self, 
        property: RealEstateAsset,
        current_loan: float | None = None
    ) -> LeveragePotential:
        """分析房产抵押潜力"""
        
    async def calculate_rental_yield(
        self, 
        property: RealEstateAsset,
        market_rent: float | None = None
    ) -> RentalYield:
        """计算租售比和租金收益"""
        
    def get_utilization_strategies(
        self, 
        property: RealEstateAsset,
        user_profile: dict
    ) -> list[UtilizationStrategy]:
        """生成房产运用策略建议"""
```

**AI Coding 指引**:
- 所有估值相关计算应使用 `PropertyValuationService`
- 策略建议需考虑用户风险偏好
- 对外不暴露内部计算细节，返回结构化结果

---

#### 2.2.2 PropertyValuationService (多层次估值服务)

**文件**: `backend/app/services/property_valuation.py`

**设计理念**: 采用多层次降级策略，确保无论有无外部 API 都能提供合理估值。

**估值层次 (Valuation Tiers)**:
```
┌─────────────────────────────────────────────────────┐
│ Tier 1: 外部 API (贝壳/链家)  ← 最准确，需网络     │
├─────────────────────────────────────────────────────┤
│ Tier 2: 本地基准数据 + 调整因子  ← 离线可用       │
├─────────────────────────────────────────────────────┤
│ Tier 3: LLM 智能估算  ← 基于位置描述推理           │
├─────────────────────────────────────────────────────┤
│ Tier 4: 用户输入 + 合理性校验  ← 兜底方案          │
└─────────────────────────────────────────────────────┘
```

**职责**:
- Tier 1: 封装外部房价 API 调用（贝壳/链家/安居客）
- Tier 2: 基于本地城市/区域基准数据进行估值
- Tier 3: 利用 LLM 基于位置描述进行智能估算
- Tier 4: 接受用户输入并进行合理性校验

**关键方法**:
```python
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
        self.api_providers = {
            "beike": BeikeAPIProvider(),
            "lianjia": LianjiaAPIProvider(),
        }
    
    async def get_market_value(
        self, 
        location: str,
        area: float,
        property_type: str = "residential",
        year_built: int | None = None,
        bedrooms: int = 2,
        use_tier: int | None = None  # 强制使用指定层级
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
        
    async def get_rental_estimate(
        self, 
        location: str,
        area: float,
        bedrooms: int = 2
    ) -> RentalEstimate:
        """获取租金估价"""
        
    def validate_user_input(
        self,
        location: str,
        area: float,
        user_value: float,
        property_type: str = "residential"
    ) -> ValueValidation:
        """校验用户输入的估值是否合理"""


class CityBenchmarkData:
    """
    本地城市基准数据 (Tier 2)
    
    数据来源: 统计局公开数据 + 定期人工维护
    更新频率: 季度更新
    """
    
    # 主要城市住宅均价 (元/平方米) - 2024Q4 基准
    CITY_AVG_PRICES = {
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
        
        # 二线城市
        "长沙": 11000,
        "郑州": 13000,
        "青岛": 18000,
        "合肥": 18000,
        "厦门": 45000,
        "福州": 22000,
        
        # 默认 (三四线城市)
        "default": 8000,
    }
    
    # 区域调整系数 (热门区域溢价)
    DISTRICT_MULTIPLIERS = {
        "北京": {
            "海淀": 1.3,
            "朝阳": 1.2,
            "西城": 1.4,
            "东城": 1.35,
            "丰台": 0.85,
            "昌平": 0.7,
            "通州": 0.75,
            "大兴": 0.7,
            "default": 1.0,
        },
        "上海": {
            "静安": 1.4,
            "黄浦": 1.5,
            "徐汇": 1.3,
            "浦东": 1.1,
            "闵行": 0.9,
            "宝山": 0.7,
            "default": 1.0,
        },
        # ... 其他城市
    }
    
    # 房龄折旧率 (每年)
    AGE_DEPRECIATION_RATE = 0.005  # 0.5%/年
    
    # 户型调整 (相对于2居)
    BEDROOM_MULTIPLIERS = {
        1: 1.05,   # 小户型溢价
        2: 1.0,    # 基准
        3: 0.98,   # 略低
        4: 0.95,   # 大户型折价
    }
    
    def estimate(
        self,
        city: str,
        district: str | None,
        area: float,
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
            district_multiplier = city_districts.get(district, city_districts.get("default", 1.0))
        
        # 3. 房龄调整
        age_multiplier = 1.0
        if year_built:
            age = 2024 - year_built
            age_multiplier = max(0.7, 1 - age * self.AGE_DEPRECIATION_RATE)
        
        # 4. 户型调整
        bedroom_multiplier = self.BEDROOM_MULTIPLIERS.get(bedrooms, 1.0)
        
        # 计算最终价格
        unit_price = base_price * district_multiplier * age_multiplier * bedroom_multiplier
        total_value = unit_price * area
        
        return ValuationResult(
            value=total_value,
            unit_price=unit_price,
            confidence=0.7,  # 本地数据置信度 70%
            source="local_benchmark",
            breakdown={
                "base_price": base_price,
                "district_multiplier": district_multiplier,
                "age_multiplier": age_multiplier,
                "bedroom_multiplier": bedroom_multiplier,
            }
        )


class LLMPropertyEstimator:
    """
    LLM 智能估值 (Tier 3)
    
    利用 LLM 的知识库对位置进行理解和估价
    适用于没有精确位置数据时的智能推断
    """
    
    ESTIMATION_PROMPT = '''
你是一位资深的房产评估师。请根据以下信息估算房产价值。

位置描述: {location}
面积: {area} 平方米
房产类型: {property_type}
建成年份: {year_built}
卧室数: {bedrooms}

请返回 JSON 格式:
{{
    "estimated_unit_price": <元/平方米>,
    "confidence": <0-1置信度>,
    "reasoning": "<估价理由>",
    "price_range": {{
        "low": <最低估价>,
        "high": <最高估价>
    }}
}}

注意:
1. 根据你对该区域房价的了解进行估算
2. 如果位置不明确，给出保守估计和较低置信度
3. 考虑当地房价水平、地段、交通等因素
'''

    async def estimate(
        self,
        location: str,
        area: float,
        property_type: str = "住宅",
        year_built: int | None = None,
        bedrooms: int = 2
    ) -> ValuationResult:
        """使用 LLM 进行智能估值"""
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
        
        if result:
            unit_price = result.get("estimated_unit_price", 20000)
            return ValuationResult(
                value=unit_price * area,
                unit_price=unit_price,
                confidence=min(0.6, result.get("confidence", 0.5)),  # LLM 最高 60% 置信度
                source="llm_estimation",
                reasoning=result.get("reasoning"),
                price_range=result.get("price_range")
            )
        
        # LLM 失败时返回保守估计
        return ValuationResult(
            value=area * 15000,  # 保守均价
            unit_price=15000,
            confidence=0.3,
            source="llm_fallback",
            reasoning="LLM 估值失败，使用保守默认值"
        )


class ValueValidation:
    """用户输入值校验结果"""
    is_reasonable: bool
    deviation_percent: float  # 与估算值偏差百分比
    suggested_range: tuple[float, float]
    warnings: list[str]


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
    # 获取参考估值
    benchmark = self.benchmark_data.estimate(
        city=self._extract_city(location),
        district=self._extract_district(location),
        area=area
    )
    
    estimated_value = benchmark.value
    user_unit_price = user_value / area
    
    # 计算偏差
    deviation = (user_value - estimated_value) / estimated_value
    
    warnings = []
    if abs(deviation) > 0.5:  # 偏差超过 50%
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
```

**估值结果模型**:
```python
class ValuationResult(BaseModel):
    """估值结果"""
    value: float                    # 总估值
    unit_price: float               # 单价 (元/平方米)
    confidence: float               # 置信度 0-1
    source: str                     # 数据来源
    reasoning: str | None = None    # 估价理由 (LLM)
    price_range: dict | None = None # 价格区间
    breakdown: dict | None = None   # 计算分解 (本地基准)


class MarketValuation(BaseModel):
    """市场估值完整结果"""
    value: float
    unit_price: float
    confidence: float
    source: str                     # "api" / "local_benchmark" / "llm" / "user_input"
    
    # 多数据源比较
    tier_results: list[ValuationResult] = []  # 各层级估值结果 (可用于 UI 展示)
    
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
    city_avg_yield: float | None = None  # 城市平均租售比
```

**AI Coding 指引**:
- 估值时自动按 Tier 1→4 降级，首个成功的层级返回结果
- 本地基准数据应定期维护（建议季度更新）
- LLM 估值置信度上限为 0.6，仅作参考
- 用户输入必须经过 `validate_user_input` 校验

---

#### 2.2.3 PropertySwapSimulator (置换推演器)

**文件**: `backend/app/services/swap_simulator.py`

**职责**:
- 模拟"卖旧买新"置换场景
- 计算置换后资产配置变化
- 生成置换可行性评估报告

**关键方法**:
```python
class PropertySwapSimulator:
    def simulate_swap(
        self,
        current_property: RealEstateAsset,
        target_property: RealEstateAsset,
        user_assets: list[UserAsset],
        user_profile: dict
    ) -> SwapSimulationResult:
        """模拟房产置换"""
        
    def calculate_cash_gap(
        self,
        sell_price: float,
        buy_price: float,
        transaction_costs: float
    ) -> CashGapAnalysis:
        """计算置换资金缺口"""
        
    def project_monthly_payment_change(
        self,
        current_loan: LoanInfo | None,
        new_loan: LoanInfo
    ) -> PaymentChangeProjection:
        """预测月供变化"""
```

---

## 3. 数据模型设计 (Data Model Design)

### 3.1 RealEstateAsset (房产资产模型)

**文件**: `backend/app/models/real_estate.py`

```python
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import field_validator
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel


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


class RealEstateAsset(SQLModel, table=True):
    """
    房产资产一等模型
    
    从 UserAsset.extra_data 中抽取为独立表，
    提供房产专属的金融属性建模。
    """
    __tablename__ = "real_estate_asset"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    
    # 基础信息
    name: str = Field(max_length=200)              # 房产名称/小区名
    property_type: PropertyType                     # 房产类型
    usage: PropertyUsage                           # 使用状态
    
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
    value_source: str = Field(default="user_input")  # 估值来源 (user_input/api/manual)
    value_updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 贷款信息
    loan_type: LoanType = Field(default=LoanType.NONE)
    loan_balance: float = Field(default=0, ge=0)   # 贷款余额
    monthly_payment: float = Field(default=0, ge=0)  # 月供
    loan_rate: float | None = Field(default=None)  # 贷款利率
    loan_remaining_months: int | None = Field(default=None)  # 剩余还款月数
    
    # 租赁信息
    monthly_rent: float | None = Field(default=None, ge=0)  # 月租金收入
    rental_yield: float | None = Field(default=None)        # 租售比 (年租金/房价)
    
    # 金融属性 (计算字段，存储缓存)
    mortgage_potential: float | None = Field(default=None)   # 可抵押潜力 (估值*70% - 贷款余额)
    net_equity: float | None = Field(default=None)           # 净值 (估值 - 贷款余额)
    
    # 扩展数据
    extra_data: dict | None = Field(sa_type=JSON, default=None)
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 关联原 UserAsset (可选，用于数据迁移)
    legacy_asset_id: int | None = Field(default=None)
    
    def update_financial_attributes(self) -> None:
        """更新计算字段"""
        # 净值 = 当前估值 - 贷款余额
        self.net_equity = self.current_value - self.loan_balance
        
        # 可抵押潜力 = 估值 * 70% - 贷款余额, 最小值为 0
        self.mortgage_potential = max(0, self.current_value * 0.7 - self.loan_balance)
        
        # 租售比 = 年租金 / 当前估值
        if self.monthly_rent and self.monthly_rent > 0:
            self.rental_yield = (self.monthly_rent * 12) / self.current_value
    
    @field_validator('area')
    @classmethod
    def validate_area(cls, v: float) -> float:
        if v <= 0 or v > 10000:
            raise ValueError("面积必须在 0-10000 平方米之间")
        return v


class LoanInfo(SQLModel):
    """贷款信息（嵌套模型，非独立表）"""
    loan_type: LoanType
    balance: float
    monthly_payment: float
    rate: float
    remaining_months: int
```

### 3.2 分析结果模型

```python
# backend/app/models/real_estate.py (续)

from pydantic import BaseModel


class PropertyAnalysis(BaseModel):
    """房产分析结果"""
    property_id: int
    property_name: str
    
    # 价值分析
    current_value: float
    net_equity: float
    value_appreciation: float | None = None  # 增值幅度
    
    # 金融潜力
    mortgage_potential: float
    mortgage_utilization: float = 0.0  # 已使用抵押比例
    
    # 收益分析
    rental_yield: float | None = None
    rental_income_potential: float | None = None
    
    # 风险评估
    loan_pressure_ratio: float = 0.0  # 月供/收入 比例
    concentration_risk: str = "low"   # 资产集中风险
    
    # 综合评分
    financial_score: float = 0.0      # 金融属性综合评分 0-100


class LeveragePotential(BaseModel):
    """抵押潜力分析"""
    property_value: float
    current_loan: float
    max_mortgage: float          # 最大可贷额度 (估值*70%)
    available_mortgage: float    # 可用额度 (max - current)
    utilization_rate: float      # 使用率
    
    suggested_strategies: list[str]


class RentalYield(BaseModel):
    """租售比分析"""
    current_rent: float | None
    market_rent: float | None
    property_value: float
    gross_yield: float           # 毛租金回报率
    net_yield: float | None      # 净租金回报率（扣除维护成本）
    
    city_average_yield: float | None
    yield_rating: str            # "高于平均" / "低于平均" / "接近平均"


class UtilizationStrategy(BaseModel):
    """房产运用策略"""
    strategy_type: str           # "mortgage" / "rent" / "refinance" / "sell"
    title: str
    description: str
    expected_benefit: float
    risk_level: str
    prerequisites: list[str]
    
    
class SwapSimulationResult(BaseModel):
    """置换模拟结果"""
    is_feasible: bool
    
    # 资金分析
    sell_proceeds: float         # 卖出所得
    buy_cost: float              # 购入成本
    transaction_costs: float     # 交易成本
    cash_gap: float              # 资金缺口
    
    # 贷款变化
    current_monthly_payment: float
    new_monthly_payment: float
    payment_change: float
    
    # 资产配置变化
    before_allocation: dict[str, float]
    after_allocation: dict[str, float]
    
    # 风险评估
    risk_warnings: list[str]
    recommendations: list[str]
```

---

## 4. PortfolioAnalyzer 升级 (Quadrant Model Upgrade)

### 4.1 新增 "核心锚点" 概念

**修改**: `backend/app/services/portfolio_analyzer.py`

```python
class SPQuadrant(str, Enum):
    """Standard & Poor's Four Quadrant Model - 升级版"""
    SPENDING_MONEY = "spending"        # 要花的钱
    LIFE_MONEY = "life"                # 保命的钱
    GROWTH_MONEY = "growth"            # 生钱的钱
    PRESERVATION_MONEY = "preservation" # 保本升值的钱
    
    # Phase 2 新增
    ANCHOR_ASSET = "anchor"            # 核心锚点资产 (自住房)


class PortfolioAnalyzer:
    
    # 新增配置
    ANCHOR_ASSET_CONFIG = {
        "include_self_occupied_property": True,  # 自住房是否计入锚点
        "anchor_ratio_warning": 0.7,  # 锚点资产占比警告阈值
        "enable_leverage_suggestion": True,  # 是否启用抵押建议
    }
    
    def _classify_real_estate(
        self, 
        property: RealEstateAsset
    ) -> SPQuadrant:
        """房产分类逻辑（新）"""
        if property.usage == PropertyUsage.SELF_OCCUPIED:
            return SPQuadrant.ANCHOR_ASSET  # 自住房归入锚点
        elif property.usage == PropertyUsage.RENTED:
            return SPQuadrant.GROWTH_MONEY  # 出租房归入生钱
        else:
            return SPQuadrant.PRESERVATION_MONEY  # 其他归入保值
    
    def _generate_anchor_insights(
        self,
        anchor_assets: list[RealEstateAsset],
        total_net_worth: float
    ) -> dict:
        """生成锚点资产洞察"""
        anchor_value = sum(p.net_equity for p in anchor_assets)
        anchor_ratio = anchor_value / total_net_worth if total_net_worth > 0 else 0
        
        insights = {
            "anchor_value": anchor_value,
            "anchor_ratio": anchor_ratio,
            "leverage_potential": sum(p.mortgage_potential for p in anchor_assets),
            "insights": []
        }
        
        # 生成洞察建议
        if anchor_ratio > 0.5:
            insights["insights"].append({
                "type": "opportunity",
                "title": "锚点资产充足",
                "description": f"您的自住房净值占总资产的{anchor_ratio:.0%}，"
                              "可考虑适度运用房产金融属性优化配置。"
            })
        
        total_leverage = insights["leverage_potential"]
        if total_leverage > 500000:  # 50万以上可抵押
            insights["insights"].append({
                "type": "suggestion",
                "title": "抵押潜力可观",
                "description": f"您的房产仍有约{total_leverage/10000:.0f}万元抵押空间，"
                              "可用于教育金/创业资金等长期规划。"
            })
        
        return insights
```

### 4.2 风险预警规则调整

```python
# 原规则：房产集中 = 风险
# 新规则：区分自住房与投资房

def _generate_risk_warnings(
    self,
    analysis: PortfolioAnalysis,
    anchor_insights: dict
) -> list[dict]:
    """生成风险预警（升级版）"""
    warnings = []
    
    # 移除：单纯的"房产占比过高"警告
    # 新增：区分性预警
    
    # 1. 投资房集中警告（仍然保留）
    investment_property_ratio = analysis.quadrant_allocations.get(
        SPQuadrant.PRESERVATION_MONEY, 0
    )
    if investment_property_ratio > 0.4:
        warnings.append({
            "type": "concentration",
            "level": "medium",
            "title": "投资性房产集中",
            "description": "投资房产占比较高，建议分散至其他资产类别",
            "action": "考虑部分变现或抵押运用"
        })
    
    # 2. 锚点资产无杠杆运用提示（新增，非警告）
    if anchor_insights["leverage_potential"] > 1000000:
        warnings.append({
            "type": "opportunity",
            "level": "info",
            "title": "资产运用空间",
            "description": f"您的自住房有{anchor_insights['leverage_potential']/10000:.0f}万抵押空间",
            "action": "了解抵押贷款如何优化资产配置"
        })
    
    # 3. 流动性不足警告（保留）
    if analysis.liquidity_ratio < 3:
        warnings.append({
            "type": "liquidity",
            "level": "high",
            "title": "流动性紧张",
            "description": "现金储备不足3个月支出，建议增加应急资金",
            "action": "优先补充现金类资产"
        })
    
    return warnings
```

---

## 5. 数据迁移方案 (Data Migration)

### 5.1 从 UserAsset 迁移到 RealEstateAsset

```python
# migration script: scripts/migrate_real_estate.py

async def migrate_real_estate_assets():
    """从 UserAsset.extra_data 迁移房产数据"""
    async for session in get_db_session():
        # 查询所有 real_estate 类型资产
        stmt = select(UserAsset).where(UserAsset.asset_type == AssetType.REAL_ESTATE)
        result = await session.execute(stmt)
        legacy_assets = result.scalars().all()
        
        for asset in legacy_assets:
            extra = asset.extra_data or {}
            
            # 创建新的 RealEstateAsset
            new_property = RealEstateAsset(
                user_id=asset.user_id,
                name=asset.name,
                property_type=PropertyType.RESIDENTIAL,  # 默认住宅
                usage=PropertyUsage.SELF_OCCUPIED,       # 默认自住
                city=extra.get("city", "未知"),
                district=extra.get("district"),
                address=extra.get("location"),
                area=extra.get("area", 100),             # 默认100平米
                current_value=asset.value,
                value_source="migration",
                loan_balance=extra.get("loan_balance", 0),
                monthly_payment=extra.get("monthly_payment", 0),
                monthly_rent=extra.get("monthly_rent"),
                legacy_asset_id=asset.id
            )
            new_property.update_financial_attributes()
            session.add(new_property)
        
        await session.commit()
```

### 5.2 数据库迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "add_real_estate_asset_table"

# 执行迁移
alembic upgrade head

# 运行数据迁移脚本
python -m scripts.migrate_real_estate
```

---

## 6. Feature Flag 配置

**文件**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # ... 现有配置 ...
    
    # Phase 2 Feature Flags
    ENABLE_REAL_ESTATE_ENGINE: bool = False      # 启用房产引擎
    ENABLE_PROPERTY_VALUATION_API: bool = False  # 启用外部估值 API
    ENABLE_SWAP_SIMULATOR: bool = False          # 启用置换模拟
    ENABLE_ANCHOR_QUADRANT: bool = False         # 启用锚点象限
    
    # 外部 API 配置
    PROPERTY_API_PROVIDER: str = "mock"          # mock / beike / lianjia
    PROPERTY_API_KEY: str | None = None
```

---

## 7. 验收清单 (Acceptance Checklist)

### Week 5 验收
- [ ] `RealEstateAsset` 数据模型创建
- [ ] 数据库迁移完成
- [ ] `RealEstateEngine.analyze_property()` 实现
- [ ] `RealEstateEngine.analyze_leverage_potential()` 实现

### Week 6 验收
- [ ] `PropertyValuationService` 实现（含 Mock）
- [ ] 外部 API 集成（至少一个提供商）
- [ ] `PropertySwapSimulator` 实现
- [ ] 置换模拟结果 UI 组件设计

### Week 7 验收
- [ ] `PortfolioAnalyzer` 升级完成
- [ ] "锚点象限" 分析逻辑实现
- [ ] 风险预警规则调整完成
- [ ] Feature Flag 全量测试
- [ ] 端到端测试通过

---

## 8. 风险与注意事项

| 风险 | 影响 | 缓解措施 |
| :--- | :--- | :--- |
| 外部房价 API 不稳定 | 高 | 实现多提供商 fallback + 用户手动输入降级 |
| 房产数据迁移丢失 | 中 | 保留 `legacy_asset_id` 关联，支持数据回滚 |
| 用户对新概念困惑 | 低 | 增加引导文案，渐进式解释"锚点资产" |

---

## 附录: AI Coding 快速参考

### 关键导入
```python
from app.models.real_estate import (
    RealEstateAsset, PropertyType, PropertyUsage, LoanType,
    PropertyAnalysis, LeveragePotential, RentalYield
)
from app.services.real_estate_engine import RealEstateEngine
from app.services.property_valuation import PropertyValuationService
from app.services.swap_simulator import PropertySwapSimulator
```

### 文件组织
```
backend/app/
├── models/
│   ├── real_estate.py      # 新建: 房产数据模型
│   └── user.py             # 保留: 兼容现有代码
├── services/
│   ├── real_estate_engine.py   # 新建: 房产分析引擎
│   ├── property_valuation.py   # 新建: 估值服务
│   ├── swap_simulator.py       # 新建: 置换模拟
│   └── portfolio_analyzer.py   # 修改: 新增锚点象限
└── core/
    └── config.py               # 修改: 新增 Feature Flags
```

### 单元测试模板
```python
# tests/test_real_estate_engine.py

import pytest
from app.models.real_estate import RealEstateAsset, PropertyType, PropertyUsage

@pytest.fixture
def sample_property():
    return RealEstateAsset(
        user_id=1,
        name="测试小区",
        property_type=PropertyType.RESIDENTIAL,
        usage=PropertyUsage.SELF_OCCUPIED,
        city="北京",
        area=100,
        current_value=5000000,
        loan_balance=2000000,
        monthly_payment=12000
    )

def test_leverage_potential(sample_property):
    sample_property.update_financial_attributes()
    # 预期: 500万 * 70% - 200万 = 150万
    assert sample_property.mortgage_potential == 1500000

def test_net_equity(sample_property):
    sample_property.update_financial_attributes()
    # 预期: 500万 - 200万 = 300万
    assert sample_property.net_equity == 3000000
```
