"""
Family Profile Data Models for Phase 4

家庭画像数据模型 - 用于存储和管理用户的家庭成员图谱和生命周期事件

支持家庭成员关系建模和生命周期事件追踪
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, JSON, Text, Integer, String, Float, DateTime, ForeignKey
from sqlmodel import Field as SQLField, SQLModel


class FamilyRelation(str, Enum):
    """家庭成员关系"""
    SELF = "self"           # 本人
    SPOUSE = "spouse"       # 配偶
    CHILD = "child"         # 子女
    PARENT = "parent"       # 父母
    SIBLING = "sibling"     # 兄弟姐妹
    OTHER = "other"         # 其他亲属


class LifecycleEventType(str, Enum):
    """生命周期事件类型"""
    MARRIAGE = "marriage"           # 结婚
    CHILD_BIRTH = "child_birth"     # 生育
    RETIREMENT = "retirement"       # 退休
    EDUCATION = "education"         # 子女教育
    PROPERTY_PURCHASE = "property_purchase"   # 购房
    JOB_CHANGE = "job_change"       # 工作变动
    MEDICAL = "medical"             # 重大医疗
    INHERITANCE = "inheritance"     # 遗产规划


class FamilyMember(BaseModel):
    """家庭成员"""
    relation: FamilyRelation
    name: str | None = None
    age: int | None = None
    occupation: str | None = None
    income: float | None = None
    insurance_coverage: list[str] = []
    special_needs: list[str] = []
    health_status: str | None = None


class LifecycleEvent(BaseModel):
    """生命周期事件"""
    event_type: LifecycleEventType
    expected_date: str | None = None
    financial_impact: float | None = None
    priority: str = "medium"
    notes: str | None = None


class FamilyProfileCreate(BaseModel):
    """创建家庭画像的请求模型"""
    members: list[FamilyMember]
    lifecycle_events: list[LifecycleEvent] = []
    total_income: float | None = None
    total_expenses: float | None = None
    financial_goals: list[str] = []


class FamilyProfileResponse(BaseModel):
    """家庭画像响应模型"""
    id: int
    user_id: int
    members: list[dict]
    lifecycle_events: list[dict]
    total_income: float | None
    total_expenses: float | None
    financial_goals: list[str]
    created_at: datetime
    updated_at: datetime


class FamilyProfile(SQLModel, table=True):
    """
    家庭画像
    
    存储用户的家庭成员图谱和生命周期规划
    """
    __tablename__ = "family_profile"
    
    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(
        sa_column=Column(Integer, ForeignKey("user.id"), unique=True, index=True, nullable=False)
    )
    
    # 家庭成员 (JSON 字段)
    members: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 生命周期事件 (JSON 字段)
    lifecycle_events: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 家庭财务概况
    total_income: Optional[float] = SQLField(sa_column=Column(Float, default=None))
    total_expenses: Optional[float] = SQLField(sa_column=Column(Float, default=None))
    
    # 家庭财务目标 (JSON 字段)
    financial_goals: Optional[list] = SQLField(sa_column=Column(JSON, default=[]))
    
    # 备注
    notes: Optional[str] = SQLField(sa_column=Column(Text, default=None))
    
    # 时间戳
    created_at: Optional[datetime] = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow)
    )
    updated_at: Optional[datetime] = SQLField(
        sa_column=Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    )
