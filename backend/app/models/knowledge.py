"""
Knowledge Base Data Models for RAG System

This module defines the data models for the knowledge base:
- PolicyKnowledge: 政策知识 (购房政策、公积金政策、贷款政策)
- FAQKnowledge: 常见问题知识
- ProductKnowledge: 金融产品知识

AI Coding Guidance:
- 使用 prompt_manager.render() 获取 Prompt 模板
- 所有知识入库前需生成 embedding
- 优先使用 active 状态的知识
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON, Index, text
from sqlmodel import Column, Field, SQLModel


# ============================================================================
# Enums
# ============================================================================

class KnowledgeCategory(str, Enum):
    """知识分类"""
    POLICY = "policy"                    # 购房政策
    PROVIDENT_FUND = "provident_fund"    # 公积金政策
    TAX = "tax"                          # 税费政策
    LOAN = "loan"                        # 贷款政策
    FAQ = "faq"                          # 常见问题
    PRODUCT = "product"                  # 产品知识
    GENERAL = "general"                  # 通用知识


class KnowledgeStatus(str, Enum):
    """知识状态"""
    ACTIVE = "active"           # 有效
    DEPRECATED = "deprecated"   # 已废弃
    DRAFT = "draft"             # 草稿


# ============================================================================
# Database Models
# ============================================================================

class PolicyKnowledge(SQLModel, table=True):
    """
    政策知识库
    
    存储结构化的政策规则，用于 RAG 检索和规则引擎。
    
    示例:
        - 北京市购房限购政策
        - 公积金提取条件
        - 首套房贷款利率政策
    """
    __tablename__ = "policy_knowledge"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # 基础信息
    title: str = Field(max_length=200, description="标题")
    category: KnowledgeCategory = Field(
        default=KnowledgeCategory.POLICY,
        description="分类"
    )
    status: KnowledgeStatus = Field(
        default=KnowledgeStatus.ACTIVE,
        description="状态"
    )
    
    # 适用范围
    city: str | None = Field(
        default=None, 
        max_length=50,
        description="适用城市 (None=全国)"
    )
    region: str | None = Field(
        default=None, 
        max_length=50,
        description="适用区域"
    )
    
    # 内容
    content: str = Field(description="主要内容")
    summary: str | None = Field(
        default=None,
        max_length=500,
        description="摘要 (用于检索结果展示)"
    )
    keywords: list[str] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="关键词列表"
    )
    
    # 规则条件 (用于规则引擎)
    conditions: dict | None = Field(
        sa_column=Column(JSON),
        default=None,
        description='规则条件, 如: {"hukou": "local", "properties_owned": {"lt": 2}}'
    )
    
    # 来源与时效
    source: str | None = Field(
        default=None,
        max_length=200,
        description="来源 (如: 北京住建委)"
    )
    source_url: str | None = Field(
        default=None,
        max_length=500,
        description="来源链接"
    )
    effective_date: datetime | None = Field(
        default=None,
        description="生效日期"
    )
    expiry_date: datetime | None = Field(
        default=None,
        description="失效日期"
    )
    
    # 向量索引 (用于语义检索)
    embedding: list[float] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="文本向量 (1024维 BGE)"
    )
    
    # 元数据
    priority: int = Field(
        default=5, 
        ge=1, 
        le=10,
        description="优先级 1-10, 10最高"
    )
    hit_count: int = Field(default=0, description="命中次数")
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="更新时间"
    )
    
    __table_args__ = (
        Index("ix_policy_knowledge_city", "city"),
        Index("ix_policy_knowledge_category", "category"),
        Index("ix_policy_knowledge_status", "status"),
    )


class FAQKnowledge(SQLModel, table=True):
    """
    FAQ 知识库
    
    存储常见问题和答案，用于语义检索。
    
    示例:
        - Q: 首套房首付比例是多少？
        - A: 首套房首付比例通常为30%，部分城市普通住宅20%。
    """
    __tablename__ = "faq_knowledge"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # 问答对
    question: str = Field(max_length=500, description="问题")
    answer: str = Field(description="答案")
    category: KnowledgeCategory = Field(
        default=KnowledgeCategory.FAQ,
        description="分类"
    )
    
    # 检索优化
    keywords: list[str] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="关键词列表"
    )
    embedding: list[float] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="问题向量 (1024维 BGE)"
    )
    
    # 使用统计
    hit_count: int = Field(default=0, description="命中次数")
    helpful_count: int = Field(default=0, description="有用反馈数")
    
    # 元数据
    status: KnowledgeStatus = Field(
        default=KnowledgeStatus.ACTIVE,
        description="状态"
    )
    priority: int = Field(default=5, ge=1, le=10)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_faq_knowledge_category", "category"),
        Index("ix_faq_knowledge_status", "status"),
    )


class ProductKnowledge(SQLModel, table=True):
    """
    金融产品知识库
    
    存储保险、理财等金融产品信息，用于推荐。
    
    示例:
        - 定期寿险产品
        - 货币基金产品
        - 银行理财产品
    """
    __tablename__ = "product_knowledge"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # 产品信息
    name: str = Field(max_length=200, description="产品名称")
    product_type: str = Field(
        max_length=50,
        description="产品类型: insurance/fund/deposit/other"
    )
    provider: str | None = Field(
        default=None,
        max_length=200,
        description="提供商"
    )
    
    # 产品描述
    description: str = Field(description="产品描述")
    features: list[str] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="产品特点列表"
    )
    
    # 适用条件
    suitable_for: dict | None = Field(
        sa_column=Column(JSON),
        default=None,
        description='适用人群, 如: {"risk_preference": ["conservative"], "min_amount": 50000}'
    )
    
    # 向量索引
    embedding: list[float] | None = Field(
        sa_column=Column(JSON),
        default=None,
        description="描述向量"
    )
    
    # 元数据
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE)
    priority: int = Field(default=5, ge=1, le=10)
    hit_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_product_knowledge_type", "product_type"),
        Index("ix_product_knowledge_status", "status"),
    )


# ============================================================================
# Response/Result Models (Pydantic)
# ============================================================================

class KnowledgeChunk(BaseModel):
    """检索返回的知识块"""
    id: int
    category: str
    title: str
    content: str
    score: float                    # 相似度分数 (0-1)
    source: str | None = None       # 来源
    metadata: dict | None = None    # 额外元数据
    
    class Config:
        from_attributes = True


class RuleResult(BaseModel):
    """规则评估结果"""
    rule_id: int
    rule_name: str
    is_matched: bool
    constraint_text: str            # 约束描述文本
    priority: int
    city: str | None = None


class RAGResponse(BaseModel):
    """RAG 查询响应"""
    answer: str                     # LLM 生成的回答
    sources: list[KnowledgeChunk]   # 引用的知识来源
    rules_applied: list[RuleResult] = []  # 应用的规则
    confidence: float               # 置信度 (0-1)
    

class PurchaseRestriction(BaseModel):
    """限购政策结果"""
    city: str
    can_purchase: bool
    max_properties: int | None
    requirements: list[str]         # 购房要求
    restrictions: list[str]         # 限制条件


class LoanPolicy(BaseModel):
    """贷款政策结果"""
    city: str
    max_ltv: float                  # 最高贷款比例
    min_down_payment: float         # 最低首付比例
    base_rate: float                # 基准利率
    notes: list[str]                # 备注说明
