"""
User-related data models
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import field_validator
from sqlalchemy import JSON
from sqlmodel import Field, Relationship, SQLModel


class AssetType(str, Enum):
    REAL_ESTATE = "real_estate"  # 房产
    CASH = "cash"  # 现金
    INVESTMENT = "investment"  # 投资
    INSURANCE = "insurance"  # 保险
    LIABILITY = "liability"  # 负债


class RiskLevel(str, Enum):
    # NOTE: Values must be UPPERCASE to match PostgreSQL enum created in initial migration
    # The database enum uses: CONSERVATIVE, MODERATE, AGGRESSIVE
    CONSERVATIVE = "CONSERVATIVE"  # 保守型
    MODERATE = "MODERATE"  # 稳健型
    AGGRESSIVE = "AGGRESSIVE"  # 激进型
    UNKNOWN = "UNKNOWN"  # 未知


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    phone: str = Field(unique=True, index=True, min_length=11, max_length=15)
    device_id: str | None = Field(default=None, index=True, max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    assets: list["UserAsset"] = Relationship(back_populates="user")
    profile: Optional["UserProfile"] = Relationship(back_populates="user")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """验证手机号格式"""
        if not v.isdigit():
            raise ValueError("手机号只能包含数字")
        if len(v) < 11 or len(v) > 15:
            raise ValueError("手机号长度必须在11-15位之间")
        return v


class UserProfile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", unique=True)
    age_range: str = Field(min_length=1, max_length=20)  # "30-40", "40-50", etc.
    family_structure: str = Field(
        min_length=1, max_length=50
    )  # "single", "married", "married_with_kids"
    risk_preference: RiskLevel
    monthly_expense: float | None = Field(default=None, ge=0)
    occupation: str | None = Field(default=None, max_length=100)  # User's occupation
    income_range: str | None = Field(default=None, max_length=50)  # Income range (e.g., "10-20万", "20-50万")

    # 关联关系
    user: User = Relationship(back_populates="profile")

    @field_validator("age_range")
    @classmethod
    def validate_age_range(cls, v: str) -> str:
        """验证年龄段格式"""
        valid_ranges = ["20-30", "30-40", "40-50", "50-60", "60+", "unknown"]  # ✅ Added "unknown"
        if v not in valid_ranges:
            raise ValueError(f"年龄段必须是以下之一: {', '.join(valid_ranges)}")
        return v

    @field_validator("family_structure")
    @classmethod
    def validate_family_structure(cls, v: str) -> str:
        """验证家庭结构"""
        valid_structures = [
            "single",
            "married",
            "married_with_kids",
            "divorced",
            "widowed",
            "unknown",  # ✅ Added "unknown"
        ]
        if v not in valid_structures:
            raise ValueError(f"家庭结构必须是以下之一: {', '.join(valid_structures)}")
        return v


class UserAsset(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    asset_type: AssetType
    name: str = Field(min_length=1, max_length=200)  # 资产名称，如"天通苑北一区"
    value: float = Field(ge=0)  # 资产价值，必须大于等于0
    is_confirmed: bool = Field(default=False)  # 是否经用户确认 - tracks if data came from explicit user input
    extra_data: dict | None = Field(
        sa_type=JSON, default=None
    )  # 额外信息，如面积、位置等
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联关系
    user: User = Relationship(back_populates="assets")

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        """验证资产价值"""
        if v < 0:
            raise ValueError("资产价值必须大于等于0")
        if v > 1e12:  # 1万亿，防止异常大的数值
            raise ValueError("资产价值不能超过1万亿")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证资产名称"""
        if not v.strip():
            raise ValueError("资产名称不能为空")
        return v.strip()
