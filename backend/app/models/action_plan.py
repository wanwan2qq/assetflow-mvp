"""
Action Plan Data Models for Phase 4

可执行方案数据模型 - 用于存储和管理用户的个性化行动建议

基于用户资产+画像+知识库推理生成的可落地建议
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional, List

from pydantic import BaseModel, Field
from sqlalchemy import Column, JSON, Text, Integer, String, Float, DateTime, ForeignKey
from sqlmodel import Field as SQLField, SQLModel, Relationship


class ActionPriority(str, Enum):
    """行动优先级"""
    HIGH = "high"       # 立即行动
    MEDIUM = "medium"   # 近期行动 (1-3个月)
    LOW = "low"         # 长期规划


class ActionCategory(str, Enum):
    """行动类别 (精简为5大核心域)"""
    WEALTH_PROTECTION = "wealth_protection" # 财富保障 (保险、应急金)
    WEALTH_GROWTH = "wealth_growth"         # 财富增值 (资产配置、投资)
    REAL_ESTATE = "real_estate"             # 房产规划 (买卖、置换、贷款)
    LIFE_PLANNING = "life_planning"         # 人生规划 (教育、养老、税务)
    DEBT_OPTIMIZATION = "debt_optimization" # 负债优化 (债务管理)


class ActionStatus(str, Enum):
    """计划状态"""
    DRAFT = "draft"             # 草稿
    PENDING = "pending"         # 待决策 (已生成，未采纳)
    IN_PROGRESS = "in_progress" # 执行中 (已采纳)
    COMPLETED = "completed"     # 已完成
    DISMISSED = "dismissed"     # 已忽略/暂不需要
    ARCHIVED = "archived"       # 已归档


class ActionStepStatus(str, Enum):
    """步骤状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class ActionPlanStep(SQLModel, table=True):
    """
    行动计划步骤 (独立表，支持精细化跟踪)
    """
    __tablename__ = "action_plan_step"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    plan_id: int = SQLField(
        sa_column=Column(Integer, ForeignKey("action_plan.id", ondelete="CASCADE"), index=True, nullable=False)
    )
    step_number: int = SQLField(description="步骤序号")
    action: str = SQLField(sa_column=Column(String(500), nullable=False), description="步骤标题")
    description: Optional[str] = SQLField(sa_column=Column(Text), description="详细描述")
    expected_outcome: Optional[str] = SQLField(sa_column=Column(String(500)), description="预期结果")
    timeline: Optional[str] = SQLField(sa_column=Column(String(200)), description="建议时间")
    
    # 跟踪字段
    status: str = SQLField(sa_column=Column(String(20), default="pending"))
    completed_at: Optional[datetime] = SQLField(sa_column=Column(DateTime))
    user_notes: Optional[str] = SQLField(sa_column=Column(Text), description="用户备注")
    
    # Relationship
    plan: Optional["ActionPlan"] = Relationship(back_populates="steps_list")


class ActionPlanCreate(BaseModel):
    """创建 ActionPlan 的请求模型"""
    title: str
    category: ActionCategory
    priority: ActionPriority
    summary: str
    steps: list[dict] # 此时还是 dict 列表
    expected_benefits: list[str]
    potential_risks: list[str]
    confidence: float = 0.5


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
    category: str = SQLField(sa_column=Column(String(50), default="wealth_growth")) 
    priority: str = SQLField(sa_column=Column(String(20), default="medium"))
    summary: Optional[str] = SQLField(sa_column=Column(Text))
    
    # 方案内容 (JSON 字段 - 保留作为快照，实际执行跟踪用 ActionPlanStep)
    original_steps_snapshot: Optional[list] = SQLField(sa_column=Column(JSON, default=[]), description="原始步骤快照")
    
    expected_benefits: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    potential_risks: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 数据依据 (JSON 字段)
    based_on_assets: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    based_on_knowledge: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 状态跟踪
    status: str = SQLField(sa_column=Column(String(20), default="pending"))
    
    # 时间戳
    created_at: Optional[datetime] = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    updated_at: Optional[datetime] = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
    adopted_at: Optional[datetime] = SQLField(sa_column=Column(DateTime), description="采纳时间")
    completed_at: Optional[datetime] = SQLField(sa_column=Column(DateTime), description="完成时间")
    dismiss_reason: Optional[str] = SQLField(sa_column=Column(Text), description="忽略原因")
    
    # 元数据
    confidence: float = SQLField(sa_column=Column(Float, default=0.5))
    
    # Relationship
    steps_list: List[ActionPlanStep] = Relationship(back_populates="plan", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class ActionPlanRead(BaseModel):
    """
    ActionPlan with steps_list included for API response.
    Inherits from BaseModel to explicitly define fields for serialization.
    """
    id: int
    user_id: int
    title: str
    category: str
    priority: str
    summary: Optional[str] = None
    original_steps_snapshot: Optional[list] = []
    expected_benefits: Optional[list] = []
    potential_risks: Optional[list] = []
    based_on_assets: Optional[list] = []
    based_on_knowledge: Optional[list] = []
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    adopted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dismiss_reason: Optional[str] = None
    confidence: float
    
    # Include the relationship
    steps_list: List[ActionPlanStep] = []
    
    class Config:
        from_attributes = True
