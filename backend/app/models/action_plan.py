"""
Action Plan Data Models for Phase 4

可执行方案数据模型 - 用于存储和管理用户的个性化行动建议

基于用户资产+画像+知识库推理生成的可落地建议
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, JSON, Text, Integer, String, Float, DateTime, ForeignKey
from sqlmodel import Field as SQLField, SQLModel


class ActionPriority(str, Enum):
    """行动优先级"""
    HIGH = "high"       # 立即行动
    MEDIUM = "medium"   # 近期行动 (1-3个月)
    LOW = "low"         # 长期规划


class ActionCategory(str, Enum):
    """行动类别"""
    ASSET_ALLOCATION = "asset_allocation"   # 资产配置
    INSURANCE = "insurance"                 # 保险规划
    REAL_ESTATE = "real_estate"             # 房产相关
    INVESTMENT = "investment"               # 投资建议
    DEBT_MANAGEMENT = "debt_management"     # 负债管理
    TAX_PLANNING = "tax_planning"           # 税务规划
    EMERGENCY_FUND = "emergency_fund"       # 应急金
    EDUCATION = "education"                 # 教育金
    RETIREMENT = "retirement"               # 养老规划


class ActionStep(BaseModel):
    """单个行动步骤"""
    step_number: int
    action: str                             # 具体行动描述
    expected_outcome: str                   # 预期效果
    timeline: str                           # 时间建议
    dependencies: list[str] = []            # 前置条件
    resources: list[str] = []               # 需要的资源/文件


class ActionPlanCreate(BaseModel):
    """创建 ActionPlan 的请求模型"""
    title: str
    category: ActionCategory
    priority: ActionPriority
    summary: str
    steps: list[ActionStep]
    expected_benefits: list[str]
    potential_risks: list[str]
    confidence: float = 0.5


class ActionPlanResponse(BaseModel):
    """ActionPlan 响应模型"""
    id: int
    user_id: int
    title: str
    category: str
    priority: str
    summary: str
    steps: list[dict]
    expected_benefits: list[str]
    potential_risks: list[str]
    status: str
    confidence: float
    created_at: datetime


class ActionPlan(SQLModel, table=True):
    """
    可执行方案
    
    基于用户资产+画像+知识库推理生成的个性化行动建议
    """
    __tablename__ = "action_plan"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(
        sa_column=Column(Integer, ForeignKey("user.id"), index=True, nullable=False)
    )
    
    # 方案基本信息
    title: str = SQLField(sa_column=Column(String(200), nullable=False))
    category: str = SQLField(sa_column=Column(String(50), default="asset_allocation"))
    priority: str = SQLField(sa_column=Column(String(20), default="medium"))
    summary: Optional[str] = SQLField(sa_column=Column(Text))
    
    # 方案内容 (JSON 字段)
    steps: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    expected_benefits: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    potential_risks: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 数据依据 (JSON 字段)
    based_on_assets: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    based_on_knowledge: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 状态跟踪
    status: str = SQLField(sa_column=Column(String(20), default="pending"))
    completed_steps: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 元数据
    confidence: float = SQLField(sa_column=Column(Float, default=0.5))
    created_at: Optional[datetime] = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    updated_at: Optional[datetime] = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
