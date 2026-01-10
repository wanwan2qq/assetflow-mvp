"""
Commercial product data models
"""

from datetime import datetime

from pydantic import field_validator
from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class CommercialProduct(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    category: str = Field(
        min_length=1, max_length=50
    )  # "insurance", "broker", "investment"
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1000)
    provider: str = Field(min_length=1, max_length=200)
    contact_info: dict = Field(sa_type=JSON)  # 联系方式
    priority: int = Field(default=0, ge=0, le=100)  # 推荐优先级 0-100
    target_tags: list[str] = Field(sa_type=JSON, default=[])  # 目标用户标签
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """验证商品类别"""
        valid_categories = ["insurance", "broker", "investment", "loan", "consulting"]
        if v not in valid_categories:
            raise ValueError(f"商品类别必须是以下之一: {', '.join(valid_categories)}")
        return v

    @field_validator("contact_info")
    @classmethod
    def validate_contact_info(cls, v: dict) -> dict:
        """验证联系信息格式"""
        required_fields = ["phone", "name"]
        for field in required_fields:
            if field not in v:
                raise ValueError(f"联系信息必须包含字段: {field}")
        return v

    @field_validator("target_tags")
    @classmethod
    def validate_target_tags(cls, v: list[str]) -> list[str]:
        """验证目标标签"""
        if len(v) > 10:
            raise ValueError("目标标签数量不能超过10个")
        return [tag.strip() for tag in v if tag.strip()]
