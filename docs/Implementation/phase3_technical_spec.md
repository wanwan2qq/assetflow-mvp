# Phase 3: RAG 知识引擎 - 技术方案

> **文档版本**: v1.0  
> **适用范围**: 开发者 & AI Coding Assistant  
> **预计工期**: 4 周 (W8-W11)  
> **依赖**: Phase 1-2 完成

---

## 0. 文档导读 (How to Use This Document)

### 对于开发者
- 阅读 **Section 1-2** 了解目标与模块设计
- 参考 **Section 3** 的数据模型设计
- 使用 **Section 4** 的 RAG Pipeline 实现

### 对于 AI Coding Assistant
- **任务拆解时**: 参考 Section 2 的模块职责定义
- **代码生成时**: 遵循 Section 3 的数据模型和接口契约
- **集成测试时**: 使用 Section 6 的验收清单

---

## 1. Phase 3 目标与原则 (Goals & Principles)

### 1.1 核心目标

| 编号 | 目标 | 说明 |
| :--- | :--- | :--- |
| **G1** | 政策知识结构化存储 | 购房政策、限购规则、公积金政策等结构化入库 |
| **G2** | 房产 FAQ 语义检索 | 基于向量相似度的问答召回 |
| **G3** | 规则引擎硬约束 | 政策规则作为硬约束，不被 LLM 覆盖 |
| **G4** | Hybrid Search | Keyword + Vector + BM25 混合搜索 |
| **G5** | RAG 增强对话 | 知识召回增强 LLM 回答准确性 |

### 1.2 设计原则

| 原则 | 说明 |
| :--- | :--- |
| **有则增强，无则降级** | 知识库为空不影响系统运行 |
| **规则优先** | 政策硬约束优先于 LLM 生成 |
| **来源可追溯** | 每条知识标注来源和更新时间 |
| **增量扩充** | 支持动态添加知识，无需重启 |

---

## 2. 模块设计 (Module Design)

### 2.1 新增模块概览

```
Phase 3 新增模块
│
├── models/
│   └── knowledge.py            # 知识库数据模型
│
├── services/
│   ├── rag_engine.py           # RAG 核心引擎
│   ├── knowledge_retriever.py  # 知识检索器
│   └── rule_engine.py          # 规则引擎
│
├── prompts/                    # 新增子目录 (复用现有 prompt_manager)
│   ├── rag/                    # RAG 相关 Prompt
│   ├── rule/                   # 规则引擎 Prompt
│   └── valuation/              # 房产估值 Prompt
│
└── scripts/
    └── init_knowledge_base.py  # 知识库初始化脚本
```

### 2.2 复用现有 PromptManager

> ✅ **评估结论**: 现有 `core/prompt_manager.py` 已完整实现所需功能，无需新建管理器。

**现有实现**: `backend/app/core/prompt_manager.py`

**已有功能**:
- ✅ YAML 文件加载 + LRU 缓存
- ✅ Jinja2 模板渲染
- ✅ 分类/子目录组织 (category/filename)
- ✅ 配置文件支持 (config/)
- ✅ 缓存清理 (热加载)

**现有 Prompts 目录结构**:
```
backend/app/prompts/
├── chat/          # 对话相关
├── config/        # 配置文件
├── extraction/    # 信息提取
└── insight/       # 洞察分析
```

---

### 2.3 Phase 3 新增 Prompt 文件

**新增子目录**: `prompts/rag/`  
**新增子目录**: `prompts/rule/`

```
backend/app/prompts/
├── chat/
├── config/
├── extraction/
├── insight/
│
├── rag/                          # Phase 3 新增: RAG 相关
│   ├── knowledge_query.yaml      # 知识问答 Prompt
│   └── no_knowledge_fallback.yaml # 无知识降级 Prompt
│
├── rule/                         # Phase 3 新增: 规则引擎
│   └── policy_constraint.yaml    # 政策约束 Prompt
│
└── valuation/                    # Phase 2 补充: 房产估值
    └── property_valuation.yaml   # 房产估值 Prompt
```

---

### 2.4 新增 Prompt 文件内容

#### `prompts/rag/knowledge_query.yaml`

```yaml
# RAG 知识问答 Prompt
# 用于将检索到的知识注入 LLM 上下文

system_instruction: |
  你是一位专业的购房顾问。请基于以下参考知识回答用户问题。

  ## 参考知识
  {{ knowledge_context }}

  ## 政策约束
  {{ rule_constraints }}

  ## 用户问题
  {{ question }}

  ## 回答要求
  1. 优先使用参考知识中的信息
  2. 政策约束是硬性规定，必须遵守
  3. 如果知识不足以回答，请明确说明
  4. 引用具体政策时标注来源

metadata:
  version: "1.0"
  category: "rag"
  description: "RAG 知识增强问答"
```

#### `prompts/rag/no_knowledge_fallback.yaml`

```yaml
# 无知识时的降级回答 Prompt

system_instruction: |
  你是一位专业的购房顾问。用户询问了一个问题，但知识库中没有直接相关的内容。
  
  ## 用户问题
  {{ question }}
  
  ## 回答要求
  1. 基于你的专业知识尽量回答
  2. 明确说明这是一般性建议，具体情况需咨询当地部门
  3. 不要编造具体政策细节

metadata:
  version: "1.0"
  category: "rag"
  description: "无知识命中时的降级回答"
```

#### `prompts/rule/policy_constraint.yaml`

```yaml
# 政策规则约束 Prompt

constraint_template: |
  根据{{ city }}的购房政策：
  {{ constraint_text }}

purchase_limit_description: |
  【限购政策】{{ city }}
  - 户籍要求：{{ hukou_requirement }}
  - 最多可购：{{ max_properties }}套
  - 特殊要求：{{ special_requirements }}

loan_policy_description: |
  【贷款政策】{{ city }}
  - 首付比例：{{ down_payment_ratio }}
  - 贷款利率：{{ loan_rate }}
  - 公积金额度：{{ provident_fund_limit }}

metadata:
  version: "1.0"
  category: "rule"
  description: "政策规则约束模板"
```

#### `prompts/valuation/property_valuation.yaml`

```yaml
# 房产智能估值 Prompt

system_instruction: |
  你是一位资深的房产评估师。请根据以下信息估算房产价值。

  位置描述: {{ location }}
  面积: {{ area }} 平方米
  房产类型: {{ property_type }}
  建成年份: {{ year_built }}
  卧室数: {{ bedrooms }}

  请返回 JSON 格式:
  {
      "estimated_unit_price": <元/平方米>,
      "confidence": <0-1置信度>,
      "reasoning": "<估价理由>",
      "price_range": {
          "low": <最低估价>,
          "high": <最高估价>
      }
  }

  注意:
  1. 根据你对该区域房价的了解进行估算
  2. 如果位置不明确，给出保守估计和较低置信度
  3. 考虑当地房价水平、地段、交通等因素

metadata:
  version: "1.0"
  category: "valuation"
  description: "房产 LLM 估值"
```

---

### 2.5 使用示例

```python
from app.core.prompt_manager import prompt_manager

# 获取 RAG Prompt (使用 Jinja2 渲染)
prompt = prompt_manager.render(
    category="rag",
    filename="knowledge_query",
    key="system_instruction",
    knowledge_context="...",
    rule_constraints="...",
    question="首套房首付多少？"
)

# 获取规则约束描述
constraint = prompt_manager.render(
    category="rule",
    filename="policy_constraint",
    key="constraint_template",
    city="北京",
    constraint_text="非京籍需连续60个月社保"
)

# 清理缓存（热加载）
prompt_manager.clear_cache()
```

### 2.3 模块职责详解

#### 2.2.1 RAGEngine (RAG 核心引擎)

**文件**: `backend/app/services/rag_engine.py`

**职责**:
- 协调知识检索与 LLM 生成
- 构建 RAG Prompt
- 管理知识召回融合

**关键方法**:
```python
class RAGEngine:
    async def query(
        self, 
        question: str,
        user_context: dict | None = None,
        top_k: int = 5
    ) -> RAGResponse:
        """RAG 查询入口"""
        
    async def augment_prompt(
        self, 
        original_prompt: str,
        retrieved_knowledge: list[KnowledgeChunk]
    ) -> str:
        """将检索知识注入 Prompt"""
        
    def apply_rules(
        self,
        query: str,
        user_profile: dict
    ) -> list[RuleResult]:
        """应用规则引擎"""
```

---

#### 2.2.2 KnowledgeRetriever (知识检索器)

**文件**: `backend/app/services/knowledge_retriever.py`

**职责**:
- 实现 Hybrid Search (Vector + Keyword + BM25)
- 知识分块与索引
- 相似度排序与过滤

**关键方法**:
```python
class KnowledgeRetriever:
    async def search(
        self, 
        query: str,
        category: str | None = None,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> list[KnowledgeChunk]:
        """混合搜索"""
        
    async def vector_search(
        self, 
        query: str,
        top_k: int = 10
    ) -> list[KnowledgeChunk]:
        """向量相似度搜索"""
        
    async def keyword_search(
        self, 
        query: str,
        top_k: int = 10
    ) -> list[KnowledgeChunk]:
        """关键词搜索"""
        
    def rerank(
        self,
        results: list[KnowledgeChunk],
        query: str
    ) -> list[KnowledgeChunk]:
        """结果重排序 (BM25)"""
```

---

#### 2.2.3 RuleEngine (规则引擎)

**文件**: `backend/app/services/rule_engine.py`

**职责**:
- 解析政策规则条件
- 评估用户是否匹配规则
- 生成规则约束文本

**关键方法**:
```python
class RuleEngine:
    def evaluate(
        self,
        user_profile: dict,
        city: str
    ) -> list[RuleResult]:
        """评估用户适用的规则"""
        
    def get_purchase_restrictions(
        self,
        city: str,
        hukou: str,
        properties_owned: int
    ) -> PurchaseRestriction:
        """获取限购政策"""
        
    def get_loan_policy(
        self,
        city: str,
        is_first_home: bool,
        loan_type: str
    ) -> LoanPolicy:
        """获取贷款政策"""
```

---

## 3. 数据模型设计 (Data Model Design)

### 3.1 Knowledge 知识库模型

**文件**: `backend/app/models/knowledge.py`

```python
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from sqlalchemy import JSON
from sqlmodel import Field, SQLModel


class KnowledgeCategory(str, Enum):
    """知识分类"""
    POLICY = "policy"           # 购房政策
    PROVIDENT_FUND = "provident_fund"  # 公积金政策
    TAX = "tax"                 # 税费政策
    LOAN = "loan"               # 贷款政策
    FAQ = "faq"                 # 常见问题
    PRODUCT = "product"         # 产品知识
    GENERAL = "general"         # 通用知识


class KnowledgeStatus(str, Enum):
    """知识状态"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


class PolicyKnowledge(SQLModel, table=True):
    """
    政策知识库
    
    存储结构化的政策规则，用于 RAG 检索和规则引擎。
    """
    __tablename__ = "policy_knowledge"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # 基础信息
    title: str = Field(max_length=200)              # 标题
    category: KnowledgeCategory                     # 分类
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE)
    
    # 适用范围
    city: str | None = Field(default=None, max_length=50)  # 适用城市 (None=全国)
    region: str | None = Field(default=None, max_length=50)  # 适用区域
    
    # 内容
    content: str                                    # 主要内容
    summary: str | None = Field(default=None)       # 摘要 (用于检索)
    keywords: list[str] | None = Field(sa_type=JSON, default=None)  # 关键词
    
    # 规则条件 (用于规则引擎)
    conditions: dict | None = Field(sa_type=JSON, default=None)
    # 例如: {"hukou": "local", "properties_owned": {"lt": 2}}
    
    # 来源与时效
    source: str | None = Field(default=None)        # 来源 (如: 住建委)
    source_url: str | None = Field(default=None)    # 来源链接
    effective_date: datetime | None = Field(default=None)  # 生效日期
    expiry_date: datetime | None = Field(default=None)     # 失效日期
    
    # 向量索引
    embedding: list[float] | None = Field(sa_type=JSON, default=None)
    
    # 元数据
    priority: int = Field(default=5, ge=1, le=10)   # 优先级 1-10
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FAQKnowledge(SQLModel, table=True):
    """
    FAQ 知识库
    
    存储常见问题和答案，用于语义检索。
    """
    __tablename__ = "faq_knowledge"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # 问答对
    question: str                                   # 问题
    answer: str                                     # 答案
    category: KnowledgeCategory
    
    # 检索优化
    keywords: list[str] | None = Field(sa_type=JSON, default=None)
    embedding: list[float] | None = Field(sa_type=JSON, default=None)
    
    # 使用统计
    hit_count: int = Field(default=0)               # 命中次数
    helpful_count: int = Field(default=0)           # 有用反馈
    
    # 元数据
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProductKnowledge(SQLModel, table=True):
    """
    产品知识库
    
    存储金融产品信息，用于推荐。
    """
    __tablename__ = "product_knowledge"
    
    id: int | None = Field(default=None, primary_key=True)
    
    # 产品信息
    name: str = Field(max_length=200)
    product_type: str                               # insurance/fund/deposit
    provider: str | None = Field(default=None)      # 提供商
    
    # 产品描述
    description: str
    features: list[str] | None = Field(sa_type=JSON, default=None)
    
    # 适用条件
    suitable_for: dict | None = Field(sa_type=JSON, default=None)
    # 例如: {"risk_preference": ["conservative"], "min_amount": 50000}
    
    # 向量索引
    embedding: list[float] | None = Field(sa_type=JSON, default=None)
    
    # 元数据
    status: KnowledgeStatus = Field(default=KnowledgeStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Response Models
# ============================================================================

class KnowledgeChunk(BaseModel):
    """检索返回的知识块"""
    id: int
    category: str
    title: str
    content: str
    score: float                # 相似度分数
    source: str | None = None
    metadata: dict | None = None


class RuleResult(BaseModel):
    """规则评估结果"""
    rule_id: int
    rule_name: str
    is_matched: bool
    constraint_text: str        # 约束描述
    priority: int
    

class RAGResponse(BaseModel):
    """RAG 查询响应"""
    answer: str
    sources: list[KnowledgeChunk]
    rules_applied: list[RuleResult] = []
    confidence: float


class PurchaseRestriction(BaseModel):
    """限购政策结果"""
    city: str
    can_purchase: bool
    max_properties: int | None
    requirements: list[str]
    restrictions: list[str]


class LoanPolicy(BaseModel):
    """贷款政策结果"""
    city: str
    max_ltv: float              # 最高贷款比例
    min_down_payment: float     # 最低首付
    base_rate: float            # 基准利率
    notes: list[str]
```

---

## 4. RAG Pipeline 设计

### 4.1 Pipeline 架构

```
用户查询
    │
    ▼
┌─────────────────┐
│  Query Rewrite  │  ← 查询重写/扩展
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ Vector │ │Keyword │  ← Hybrid Search
│ Search │ │ Search │
└────┬───┘ └───┬────┘
     │         │
     └────┬────┘
          ▼
┌─────────────────┐
│    Re-Ranking   │  ← BM25 + 相关性
│    (Top-K)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Rule Engine    │  ← 政策硬约束
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Prompt Compose  │  ← 知识注入
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   LLM Generate  │  ← 生成回答
└─────────────────┘
```

### 4.2 核心实现

```python
# backend/app/services/rag_engine.py

from app.core.prompt_manager import prompt_manager

class RAGEngine:
    """
    RAG 核心引擎
    
    协调知识检索、规则引擎和 LLM 生成。
    使用 core/prompt_manager 管理 Prompt 模板。
    """

    def __init__(self):
        self.retriever = KnowledgeRetriever()
        self.rule_engine = RuleEngine()
    
    async def query(
        self, 
        question: str,
        user_context: dict | None = None,
        top_k: int = 5
    ) -> RAGResponse:
        """执行 RAG 查询"""
        
        # 1. 检索相关知识
        knowledge = await self.retriever.search(
            query=question,
            top_k=top_k
        )
        
        # 2. 应用规则引擎
        rules = []
        if user_context:
            rules = self.rule_engine.evaluate(
                user_profile=user_context.get("profile", {}),
                city=user_context.get("city", "")
            )
        
        # 3. 构建增强 Prompt (使用 prompt_manager.render)
        prompt = self._build_prompt(
            question=question,
            knowledge=knowledge,
            rules=rules
        )
        
        # 4. 调用 LLM 生成
        from app.core.dependencies import get_llm_provider
        llm = get_llm_provider()
        answer = await llm.generate(
            [{"role": "user", "content": prompt}], 
            ""
        )
        
        return RAGResponse(
            answer=answer,
            sources=knowledge,
            rules_applied=rules,
            confidence=self._calculate_confidence(knowledge, rules)
        )
    
    def _build_prompt(
        self, 
        question: str,
        knowledge: list[KnowledgeChunk],
        rules: list[RuleResult]
    ) -> str:
        """使用 prompt_manager.render() 构建增强 Prompt"""
        
        # 格式化知识上下文
        knowledge_context = "\n\n".join([
            f"【{k.category}】{k.title}\n{k.content}"
            for k in knowledge
        ]) if knowledge else "无相关参考知识"
        
        # 格式化规则约束
        rule_constraints = "\n".join([
            f"- {r.constraint_text}" 
            for r in rules if r.is_matched
        ]) if rules else "无特殊政策约束"
        
        # 根据知识是否命中选择不同 Prompt 文件
        if knowledge:
            return prompt_manager.render(
                category="rag",
                filename="knowledge_query",
                key="system_instruction",
                knowledge_context=knowledge_context,
                rule_constraints=rule_constraints,
                question=question
            )
        else:
            return prompt_manager.render(
                category="rag",
                filename="no_knowledge_fallback",
                key="system_instruction",
                question=question
            )
    
    def _calculate_confidence(
        self,
        knowledge: list[KnowledgeChunk],
        rules: list[RuleResult]
    ) -> float:
        """计算回答置信度"""
        base = 0.5
        
        # 知识命中加分
        if knowledge:
            avg_score = sum(k.score for k in knowledge) / len(knowledge)
            base += avg_score * 0.3
        
        # 规则匹配加分
        if rules and any(r.is_matched for r in rules):
            base += 0.1
        
        return min(1.0, base)
```

---

## 5. 初始知识数据

### 5.1 首批知识录入计划

| 类别 | 数量 | 优先级 | 示例 |
| :--- | :--- | :--- | :--- |
| 购房政策 | 20+ | 高 | 各城市限购政策 |
| 公积金政策 | 15+ | 高 | 提取条件、贷款额度 |
| 房产 FAQ | 100+ | 中 | 购房流程、税费计算 |
| 金融产品 | 50+ | 中 | 保险、理财产品 |

### 5.2 知识录入脚本

```python
# scripts/init_knowledge_base.py

INITIAL_POLICIES = [
    {
        "title": "北京市购房限购政策",
        "category": "policy",
        "city": "北京",
        "content": """
        1. 京籍家庭：限购2套住房
        2. 非京籍家庭：需连续60个月社保或纳税，限购1套
        3. 通州区：京籍限购1套，非京籍需在通州3年社保
        """,
        "conditions": {
            "hukou": "local",
            "properties_owned": {"lt": 2}
        },
        "source": "北京住建委",
        "priority": 10
    },
    {
        "title": "上海市购房限购政策",
        "category": "policy",
        "city": "上海",
        "content": """
        1. 沪籍单身：限购1套
        2. 沪籍家庭：限购2套
        3. 非沪籍：需5年社保，限购1套
        """,
        "conditions": {
            "hukou": "local"
        },
        "source": "上海房管局",
        "priority": 10
    },
    # ... 更多政策
]

INITIAL_FAQS = [
    {
        "question": "首套房首付比例是多少？",
        "answer": "首套房首付比例通常为30%，部分城市（如北京）普通住宅20%。公积金贷款最低20%。",
        "category": "faq",
        "keywords": ["首付", "首套房", "比例"]
    },
    {
        "question": "房产证办理需要多长时间？",
        "answer": "新房一般交房后1-2年内办理；二手房过户后5-15个工作日可领取。",
        "category": "faq",
        "keywords": ["房产证", "办理", "时间"]
    },
    # ... 更多 FAQ
]
```

---

## 6. Feature Flag 配置

**文件**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # Phase 3: RAG Engine Feature Flags
    ENABLE_RAG_ENGINE: bool = True              # 启用 RAG 引擎
    ENABLE_RULE_ENGINE: bool = True             # 启用规则引擎
    RAG_TOP_K: int = 5                          # 检索 Top-K
    RAG_MIN_SCORE: float = 0.5                  # 最低相似度阈值
    ENABLE_HYBRID_SEARCH: bool = True           # 启用混合搜索
```

---

## 7. 验收清单 (Acceptance Checklist)

### Week 8 验收
- [ ] `PolicyKnowledge` 数据模型创建
- [ ] `FAQKnowledge` 数据模型创建
- [ ] 数据库迁移完成
- [ ] 知识录入脚本可运行

### Week 9 验收
- [ ] `KnowledgeRetriever` 实现
- [ ] Vector Search 功能正常
- [ ] Keyword Search 功能正常

### Week 10 验收
- [ ] `RuleEngine` 实现
- [ ] Hybrid Search (BM25) 实现
- [ ] `RAGEngine` 集成完成

### Week 11 验收
- [ ] 首批知识数据录入 (20政策+100FAQ+50产品)
- [ ] RAG vs Pure LLM A/B 测试
- [ ] 知识检索准确率 ≥ 70%

---

## 8. 风险与注意事项

| 风险 | 影响 | 缓解措施 |
| :--- | :--- | :--- |
| 知识库构建耗时 | 中 | 优先录入高频问题 |
| 向量检索性能 | 低 | 使用 pgvector HNSW 索引 |
| 规则冲突 | 中 | 设置优先级，高优先级覆盖 |
| 知识过期 | 中 | 添加失效日期字段 |

---

## 附录: AI Coding 快速参考

### 关键导入
```python
from app.models.knowledge import (
    PolicyKnowledge, FAQKnowledge, 
    KnowledgeChunk, RAGResponse, RuleResult
)
from app.services.rag_engine import RAGEngine
from app.services.knowledge_retriever import KnowledgeRetriever
from app.services.rule_engine import RuleEngine
from app.core.prompt_manager import prompt_manager  # 复用现有
```

### 文件组织
```
backend/app/
├── core/
│   └── prompt_manager.py          # 现有 Prompt 管理器 (复用)
├── models/
│   └── knowledge.py               # 知识库数据模型 (NEW)
├── services/
│   ├── rag_engine.py              # RAG 核心引擎 (NEW)
│   ├── knowledge_retriever.py     # 知识检索器 (NEW)
│   └── rule_engine.py             # 规则引擎 (NEW)
├── prompts/
│   ├── chat/                      # (现有)
│   ├── config/                    # (现有)
│   ├── extraction/                # (现有)
│   ├── insight/                   # (现有)
│   ├── rag/                       # (NEW) RAG 相关
│   │   ├── knowledge_query.yaml
│   │   └── no_knowledge_fallback.yaml
│   ├── rule/                      # (NEW) 规则引擎
│   │   └── policy_constraint.yaml
│   └── valuation/                 # (NEW) 房产估值
│       └── property_valuation.yaml
└── scripts/
    └── init_knowledge_base.py     # 知识初始化脚本 (NEW)
```


