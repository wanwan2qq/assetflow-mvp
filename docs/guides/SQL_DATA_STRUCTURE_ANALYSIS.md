# AssetFlow SQL数据结构详细分析

## 📊 数据库架构概览

AssetFlow采用**三层记忆架构**（L1-L2-L3）来管理用户数据：

- **L1层（结构化资产数据）**：User, UserProfile, UserAsset - 存储确定的、结构化的资产信息
- **L2层（认知状态管理）**：UserCognition - 存储AI对用户的理解和信息收集状态
- **L3层（向量记忆）**：VectorMemory - 存储长期的、非结构化的语义记忆

---

## 🗂️ 核心数据表结构

### 1. User（用户表）- L1层

**用途**：存储用户基本信息

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    phone VARCHAR(15) UNIQUE NOT NULL,  -- 手机号（唯一标识）
    device_id VARCHAR(255),              -- 设备ID
    created_at DATETIME NOT NULL
);
```

**关联关系**：
- 一对一：UserProfile（用户画像）
- 一对多：UserAsset（用户资产）
- 一对一：UserCognition（认知状态）
- 一对多：ChatMessage（聊天消息）
- 一对多：VectorMemory（向量记忆）

**更新时机**：
- ✅ 用户注册/登录时创建
- ❌ 几乎不更新（只在用户更换设备时更新device_id）

---


### 2. UserProfile（用户画像表）- L1层

**用途**：存储用户的基本画像信息（年龄、家庭、风险偏好等）

```sql
CREATE TABLE userprofile (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,     -- 外键：user.id（一对一）
    age_range VARCHAR(20) NOT NULL,      -- 年龄段："30-40", "40-50"等
    family_structure VARCHAR(50) NOT NULL, -- 家庭结构："single", "married", "married_with_kids"
    risk_preference ENUM NOT NULL,       -- 风险偏好：conservative/moderate/aggressive
    monthly_expense FLOAT,               -- 月支出
    occupation VARCHAR(100),             -- 职业（新增字段）
    income_range VARCHAR(50),            -- 收入范围（新增字段）
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**字段验证规则**：
- `age_range`: 必须是 ["20-30", "30-40", "40-50", "50-60", "60+"] 之一
- `family_structure`: 必须是 ["single", "married", "married_with_kids", "divorced", "widowed"] 之一
- `risk_preference`: 必须是 ["conservative", "moderate", "aggressive"] 之一

**更新时机**：
- ✅ LLM提取到用户画像信息时（通过`information_extraction.py`）
- ✅ 用户明确提供年龄、家庭、职业、收入等信息时
- ✅ 通过`asset_extraction_service._update_user_profile_from_extraction()`更新

**当前业务逻辑问题**：
- ⚠️ **创建条件过严**：只有当`age_range`、`family_structure`、`risk_preference`三个字段**同时存在**时才会创建记录
- ⚠️ **occupation和income_range可能丢失**：如果用户先提供职业/收入，但没有提供年龄/家庭结构，这些信息会被存储到`UserCognition.risk_profile`中，但不会创建`UserProfile`记录

---


### 3. UserAsset（用户资产表）- L1层

**用途**：存储用户的具体资产信息

```sql
CREATE TABLE userasset (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,            -- 外键：user.id
    asset_type ENUM NOT NULL,            -- 资产类型：real_estate/cash/investment/insurance/liability
    name VARCHAR(200) NOT NULL,          -- 资产名称（如"天通苑北一区"）
    value FLOAT NOT NULL,                -- 资产价值（必须>0）
    is_confirmed BOOLEAN DEFAULT FALSE,  -- 是否经用户确认
    extra_data JSON,                     -- 额外信息（如面积、位置等）
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**资产类型枚举**：
- `REAL_ESTATE`: 房产
- `CASH`: 现金
- `INVESTMENT`: 投资
- `INSURANCE`: 保险
- `LIABILITY`: 负债

**更新时机**：
- ✅ LLM从对话中提取到资产信息时
- ✅ 通过`asset_extraction_service._update_assets_from_extraction()`创建或更新
- ✅ 更新策略：如果同类型资产已存在，则更新；否则创建新记录

**extra_data字段存储内容**：
```json
{
    "location": "北京市朝阳区",
    "area": 120.5,
    "confidence": 0.85,
    "extracted_from": "用户消息内容",
    "extraction_timestamp": "2026-01-14T10:00:00",
    "last_updated": "2026-01-14T10:00:00"
}
```

**当前业务逻辑问题**：
- ⚠️ **重复资产问题**：目前按`asset_type`查找已存在资产，可能导致同类型多个资产被覆盖
- ⚠️ **value字段约束**：必须>0，但LLM提取时可能无法获取具体金额，当前使用1作为占位符

---


### 4. UserCognition（用户认知表）- L2层

**用途**：存储AI对用户的理解和信息收集状态（防止重复询问）

```sql
CREATE TABLE usercognition (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL,     -- 外键：user.id（一对一）
    financial_goals JSON,                -- 财务目标列表：["retirement", "buy_house", "education"]
    risk_profile JSON,                   -- 风险画像：{"tolerance": "low", "anxiety": "high", ...}
    collection_status JSON,              -- 资产收集状态：{"real_estate": true, "cash": false, ...}
    advisor_note TEXT,                   -- AI顾问的内部策略笔记（最多2000字符）
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**JSON字段详细结构**：

#### financial_goals（财务目标）
```json
["retirement", "buy_house", "education", "wealth_growth"]
```

#### risk_profile（风险画像）
```json
{
    "tolerance": "conservative",          // 风险承受能力
    "decision_style": "analytical",       // 决策风格
    "confidence_level": "medium",         // 信心水平
    "current_sentiment": "anxious",       // 当前情绪
    "loss_aversion": "high",              // 损失厌恶程度
    "uncertainty_tolerance": "low",       // 不确定性容忍度
    "financial_literacy": "intermediate", // 财务知识水平
    "family_responsibility": "high",      // 家庭责任感
    "planning_horizon": "long",           // 规划时间跨度
    "age_range": "30-40",                 // 年龄段（也存在UserProfile）
    "family_structure": "married_with_kids", // 家庭结构（也存在UserProfile）
    "monthly_expense": 15000,             // 月支出（也存在UserProfile）
    "occupation": "软件工程师",            // 职业（也存在UserProfile）
    "income_range": "20-50万",            // 收入范围（也存在UserProfile）
    "last_analysis": "2026-01-14T10:00:00"
}
```

#### collection_status（收集状态）
```json
{
    "real_estate": true,   // 已收集房产信息
    "cash": false,         // 未收集现金信息
    "investment": true,    // 已收集投资信息
    "insurance": false,    // 未收集保险信息
    "liability": false     // 未收集负债信息
}
```

**更新时机**：
- ✅ Phase 2信息提取后（`asset_extraction_service._update_cognition_from_extraction()`）
- ✅ Phase 3心理分析后（`insight_service._update_cognition_insights()`）
- ✅ 每次对话后更新`collection_status`标记已收集的资产类型

**当前业务逻辑问题**：
- ⚠️ **collection_status更新问题**：需要使用`flag_modified()`告知SQLAlchemy JSON字段已修改
- ⚠️ **数据冗余**：`risk_profile`中的部分字段与`UserProfile`重复（age_range, family_structure, monthly_expense, occupation, income_range）

---


### 5. VectorMemory（向量记忆表）- L3层

**用途**：存储长期的、非结构化的语义记忆（使用pgvector进行语义搜索）

```sql
CREATE TABLE vector_memory (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,            -- 外键：user.id
    content TEXT NOT NULL,               -- 记忆内容
    embedding VECTOR(1024),              -- 向量嵌入（BGE-Large-zh-v1.5，1024维）
    metadata JSONB,                      -- 元数据
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- 索引
CREATE INDEX ix_vector_memory_user_id ON vector_memory(user_id);
CREATE INDEX ix_vector_memory_user_created ON vector_memory(user_id, created_at);
CREATE INDEX ix_vector_memory_embedding_cosine ON vector_memory USING hnsw (embedding vector_cosine_ops);
```

**metadata字段结构**：
```json
{
    "category": "health_concern",        // 记忆类别
    "tags": ["family", "health", "liquidity"],
    "source": "insight_analysis",        // 来源
    "timestamp": "2026-01-14T10:00:00"
}
```

**记忆类别**：
- `health_concern`: 健康问题
- `major_purchase`: 重大购买计划
- `retirement_planning`: 退休规划
- `education_planning`: 教育规划
- `debt_constraint`: 债务约束

**更新时机**：
- ✅ Phase 3心理分析时提取关键生活事件（`insight_service._extract_and_store_key_memories()`）
- ✅ 检测到用户提及重要信息时（如家人生病、购房计划、退休规划等）

**语义搜索**：
- 使用本地BGE模型生成1024维向量
- 使用pgvector的余弦相似度搜索
- 支持相似度阈值过滤（默认0.7）

---


### 6. ChatMessage（聊天消息表）

**用途**：存储完整的对话历史

```sql
CREATE TABLE chatmessage (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,            -- 外键：user.id
    role ENUM NOT NULL,                  -- 角色：user/ai
    content TEXT NOT NULL,               -- 消息内容（包含widget标签）
    meta_data JSON,                      -- Widget数据和其他元数据
    timestamp DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**更新时机**：
- ✅ 用户发送消息时立即保存
- ✅ AI生成回复完成后保存
- ❌ 不更新，只追加

---

### 7. ChatSession（会话表）

**用途**：存储对话上下文（已废弃，被ChatMessage替代）

```sql
CREATE TABLE chatsession (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_data JSON NOT NULL,          -- 对话上下文
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**状态**：⚠️ 已废弃，当前使用ChatMessage存储对话历史

---

### 8. CommercialProduct（商业产品表）

**用途**：存储推荐的商业产品（保险、理财等）

```sql
CREATE TABLE commercialproduct (
    id INTEGER PRIMARY KEY,
    category VARCHAR(50) NOT NULL,       -- 类别：insurance/broker/investment/loan/consulting
    name VARCHAR(200) NOT NULL,
    description VARCHAR(1000) NOT NULL,
    provider VARCHAR(200) NOT NULL,
    contact_info JSON NOT NULL,          -- 联系方式：{"phone": "xxx", "name": "xxx"}
    priority INTEGER DEFAULT 0,          -- 推荐优先级（0-100）
    target_tags JSON DEFAULT [],         -- 目标用户标签
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

**更新时机**：
- ✅ 管理员手动添加/更新产品
- ❌ 不由用户对话触发更新

---


### 9. UserInteraction（用户交互表）

**用途**：跟踪用户与商业产品的交互行为

```sql
CREATE TABLE userinteraction (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    interaction_type ENUM NOT NULL,      -- 交互类型：view/click/contact/dismiss/share
    interaction_metadata JSON DEFAULT {},
    session_id VARCHAR,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (product_id) REFERENCES commercialproduct(id)
);
```

**更新时机**：
- ✅ 用户查看/点击/联系商业产品时
- ❌ 不更新，只追加

---

### 10. AuditLog（审计日志表）

**用途**：跟踪所有数据变更（用于审计和回溯）

```sql
CREATE TABLE auditlog (
    id INTEGER PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,    -- 被修改的表名
    record_id INTEGER NOT NULL,          -- 被修改的记录ID
    action ENUM NOT NULL,                -- 操作类型：CREATE/UPDATE/DELETE
    user_id INTEGER,
    user_type VARCHAR(50) DEFAULT 'user',
    timestamp DATETIME NOT NULL,
    old_values JSON,                     -- 修改前的值
    new_values JSON,                     -- 修改后的值
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    session_id VARCHAR(100),
    extra_metadata JSON
);
```

**更新时机**：
- ✅ 任何数据表发生CREATE/UPDATE/DELETE操作时
- ❌ 当前未实现自动审计（需要在ORM层添加钩子）

---

### 11. UserAssetHistory（资产历史表）

**用途**：记录资产变更历史（时间序列）

```sql
CREATE TABLE userassethistory (
    id INTEGER PRIMARY KEY,
    asset_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    asset_type VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    value FLOAT NOT NULL,
    is_confirmed BOOLEAN NOT NULL,
    extra_data JSON,
    change_reason VARCHAR(500),
    changed_by INTEGER,
    changed_at DATETIME NOT NULL,
    is_valid_from DATETIME NOT NULL,
    is_valid_to DATETIME,                -- NULL表示当前版本
    FOREIGN KEY (asset_id) REFERENCES userasset(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

**更新时机**：
- ✅ UserAsset发生变更时创建历史记录
- ❌ 当前未实现自动历史记录（需要在ORM层添加钩子）

---


## 🔄 数据更新流程分析

### Phase 1: 用户发送消息

```
用户消息 → ChatAgent.process_message()
    ↓
1. 保存用户消息到 ChatMessage 表
2. 生成AI回复（流式输出）
3. 保存AI回复到 ChatMessage 表
```

---

### Phase 2: 信息提取与状态同步（LLM-based）

```
用户消息 → information_extraction.extract_information()
    ↓
LLM分析消息内容，提取结构化信息
    ↓
返回 extraction_result = {
    "assets": [...],              // 提取的资产信息
    "goals": [...],               // 财务目标
    "risk_profile": {...},        // 风险画像
    "completeness_update": {...}, // 收集状态更新
    "intent": "new_info|correction" // 意图识别
}
    ↓
asset_extraction_service.update_user_state()
    ↓
┌─────────────────────────────────────────┐
│ L1层更新：_update_assets_from_extraction │
│ - 创建或更新 UserAsset 记录              │
│ - 按 asset_type 查找已存在资产           │
│ - 更新 value, name, extra_data          │
└─────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ L2层更新：_update_cognition_from_extraction │
│ 1. 更新 UserCognition.financial_goals    │
│ 2. 更新 UserCognition.risk_profile       │
│ 3. 更新 UserCognition.collection_status  │
│    ⚠️ 需要 flag_modified() 标记JSON修改   │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ L1层更新：_update_user_profile_from_extraction │
│ - 更新 UserProfile 基本字段               │
│ - age_range, family_structure            │
│ - risk_preference, monthly_expense       │
│ - occupation, income_range               │
│ ⚠️ 只有三个必填字段都存在时才创建记录      │
└──────────────────────────────────────────┘
```

**关键代码位置**：
- `backend/app/services/information_extraction.py::extract_information()`
- `backend/app/services/asset_extraction_service.py::update_user_state()`

---


### Phase 3: 心理分析与策略生成（System 2）

```
每5条消息触发一次（可配置）
    ↓
insight_service.analyze_user_psychology()
    ↓
1. 获取最近50条 ChatMessage
2. LLM分析用户心理画像
    ↓
返回 analysis = {
    "risk_profile": {...},           // 风险画像
    "current_sentiment": "anxious",  // 当前情绪
    "psychological_traits": {...},   // 心理特征
    "advisor_note_internal": "...",  // AI策略笔记
    "key_concerns": [...],           // 关键关注点
    "recommended_approach": "..."    // 推荐沟通策略
}
    ↓
┌─────────────────────────────────────────┐
│ L2层更新：_update_cognition_insights     │
│ - 更新 UserCognition.risk_profile       │
│ - 更新 UserCognition.advisor_note       │
│ - 添加心理特征和情绪分析结果             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ L3层更新：_extract_and_store_key_memories │
│ - 检测关键生活事件（健康、购房、退休等）  │
│ - 生成向量嵌入（BGE-Large-zh-v1.5）      │
│ - 存储到 VectorMemory 表                │
└─────────────────────────────────────────┘
```

**关键代码位置**：
- `backend/app/services/insight_service.py::analyze_user_psychology()`
- `backend/app/services/memory_service.py::add_memory()`

---

### Phase 4: 向量记忆检索（RAG）

```
AI生成回复前
    ↓
memory_service.retrieve_relevant(query_text)
    ↓
1. 生成查询向量（BGE embeddings）
2. 使用pgvector进行余弦相似度搜索
3. 返回相似度>0.7的记忆
    ↓
将相关记忆注入到AI的上下文中
    ↓
AI生成更个性化的回复
```

**关键代码位置**：
- `backend/app/services/memory_service.py::retrieve_relevant()`

---


## ⚠️ 当前业务逻辑问题分析

### 问题1：UserProfile创建条件过严

**问题描述**：
```python
# asset_extraction_service.py::_update_user_profile_from_extraction()
if not profile:
    age_range = risk_profile.get("age_range")
    family_structure = risk_profile.get("family_structure")
    risk_preference = risk_profile.get("tolerance")
    
    # ⚠️ 只有三个字段都存在时才创建
    if age_range and family_structure and risk_preference:
        profile = UserProfile(...)
    else:
        # occupation和income_range会丢失！
        logger.info("Skipping UserProfile creation - missing required fields")
```

**影响**：
- 用户先提供职业/收入，但未提供年龄/家庭结构时，`UserProfile`不会被创建
- `occupation`和`income_range`只存储在`UserCognition.risk_profile`中
- 导致数据分散，查询不便

**建议修复**：
1. 降低创建条件：只要有任意一个字段就创建记录
2. 使用默认值填充必填字段（如age_range="unknown", family_structure="unknown"）
3. 或者修改表结构，将必填字段改为可选

---

### 问题2：UserAsset重复资产处理不当

**问题描述**：
```python
# asset_extraction_service.py::_update_assets_from_extraction()
existing_statement = select(UserAsset).where(
    UserAsset.user_id == user_id,
    UserAsset.asset_type == asset_type  # ⚠️ 只按类型查找
)
```

**影响**：
- 用户有多套房产时，只会保留最后一套
- 同类型资产会被覆盖，而不是追加

**建议修复**：
1. 添加更精细的匹配逻辑（如按name或location匹配）
2. 或者改为追加模式，不覆盖已存在资产
3. 添加资产唯一标识符（如asset_key）

---

### 问题3：UserCognition.collection_status更新问题

**问题描述**：
```python
# asset_extraction_service.py::_update_cognition_from_extraction()
cognition.collection_status[asset_type] = True

# ⚠️ SQLAlchemy不知道JSON字段被修改了
# 需要显式标记
from sqlalchemy.orm.attributes import flag_modified
flag_modified(cognition, 'collection_status')
```

**影响**：
- `collection_status`更新可能不会持久化到数据库
- 导致AI重复询问已收集的资产类型

**当前状态**：✅ 已修复（代码中已添加`flag_modified()`）

---


### 问题4：数据冗余（UserProfile vs UserCognition.risk_profile）

**问题描述**：
以下字段同时存在于两个表中：
- `age_range`: UserProfile.age_range + UserCognition.risk_profile["age_range"]
- `family_structure`: UserProfile.family_structure + UserCognition.risk_profile["family_structure"]
- `monthly_expense`: UserProfile.monthly_expense + UserCognition.risk_profile["monthly_expense"]
- `occupation`: UserProfile.occupation + UserCognition.risk_profile["occupation"]
- `income_range`: UserProfile.income_range + UserCognition.risk_profile["income_range"]

**影响**：
- 数据不一致风险：两处数据可能不同步
- 查询困惑：不清楚应该从哪个表读取
- 存储浪费

**建议修复方案**：

**方案A：单一数据源（推荐）**
- UserProfile只存储基本画像（age_range, family_structure, risk_preference, monthly_expense, occupation, income_range）
- UserCognition.risk_profile只存储心理分析结果（tolerance, decision_style, confidence_level, sentiment等）
- 修改代码，从UserCognition.risk_profile中移除重复字段

**方案B：保持冗余，但明确主从关系**
- UserProfile为主数据源（用于查询和展示）
- UserCognition.risk_profile为辅助数据源（用于AI内部决策）
- 确保更新时同步两处数据

---

### 问题5：UserAsset.value字段约束过严

**问题描述**：
```python
# user.py::UserAsset
value: float = Field(gt=0)  # ⚠️ 必须大于0

# asset_extraction_service.py
amount = asset_data.get("amount", 1)  # 默认为1
if amount is None or amount <= 0:
    amount = 1  # 使用1作为占位符
```

**影响**：
- LLM提取时可能无法获取具体金额（如"我有一套房"）
- 使用1作为占位符不够语义化
- 无法区分"真实价值为1"和"未知价值"

**建议修复**：
1. 允许value为NULL或0，表示未知价值
2. 添加`value_estimated`字段，标记是否为估算值
3. 或者使用负数表示未知（如-1）

---


### 问题6：缺少审计和历史记录自动化

**问题描述**：
- `AuditLog`和`UserAssetHistory`表已定义，但未实现自动记录
- 数据变更无法追溯
- 无法回滚到历史版本

**建议修复**：
1. 在SQLAlchemy ORM层添加事件监听器（`@event.listens_for`）
2. 自动记录所有CREATE/UPDATE/DELETE操作
3. 实现数据版本控制

---

### 问题7：VectorMemory嵌入生成失败时的处理

**问题描述**：
```python
# memory_service.py::add_memory()
embedding = await self._generate_embedding(text)

if embedding is None:
    logger.warning("Failed to generate embedding")
    # ⚠️ 仍然存储，但embedding为NULL
```

**影响**：
- 无法进行语义搜索
- 只能使用关键词搜索（fallback）
- 降低记忆检索质量

**建议修复**：
1. 添加重试机制（如3次重试）
2. 如果仍然失败，考虑不存储该记忆
3. 或者添加`needs_embedding`标志，后台异步生成

---

## 📊 数据表关联关系图

```
User (用户)
  ├─ 1:1 → UserProfile (用户画像)
  ├─ 1:1 → UserCognition (认知状态)
  ├─ 1:N → UserAsset (用户资产)
  ├─ 1:N → ChatMessage (聊天消息)
  ├─ 1:N → VectorMemory (向量记忆)
  └─ 1:N → UserInteraction (用户交互)

UserAsset (用户资产)
  └─ 1:N → UserAssetHistory (资产历史)

CommercialProduct (商业产品)
  └─ 1:N → UserInteraction (用户交互)

所有表
  └─ 1:N → AuditLog (审计日志)
```

---


## 🎯 优化建议总结

### 高优先级（建议立即修复）

#### 1. 修复UserProfile创建逻辑
**问题**：occupation和income_range可能丢失
**修复方案**：
```python
# 方案A：降低创建条件
if not profile:
    if any([risk_profile.get("age_range"), 
            risk_profile.get("family_structure"),
            risk_profile.get("occupation"),
            risk_profile.get("income_range")]):
        profile = UserProfile(
            user_id=user_id,
            age_range=risk_profile.get("age_range") or "unknown",
            family_structure=risk_profile.get("family_structure") or "unknown",
            risk_preference=risk_profile.get("tolerance") or "moderate",
            monthly_expense=risk_profile.get("monthly_expense"),
            occupation=risk_profile.get("occupation"),
            income_range=risk_profile.get("income_range")
        )
```

#### 2. 改进UserAsset重复资产处理
**问题**：同类型多个资产会被覆盖
**修复方案**：
```python
# 添加更精细的匹配逻辑
def _find_similar_asset(user_id, asset_type, name, location=None):
    # 先按类型查找
    existing_assets = query(UserAsset).filter(
        UserAsset.user_id == user_id,
        UserAsset.asset_type == asset_type
    ).all()
    
    # 再按名称或位置匹配
    for asset in existing_assets:
        if name and name in asset.name:
            return asset
        if location and asset.extra_data.get("location") == location:
            return asset
    
    return None  # 未找到，创建新资产
```

#### 3. 解决数据冗余问题
**问题**：UserProfile和UserCognition.risk_profile字段重复
**修复方案**：
```python
# 明确数据分层
# L1层（UserProfile）：基本画像，用于查询和展示
# L2层（UserCognition.risk_profile）：心理分析，用于AI决策

# 修改_update_cognition_from_extraction()
# 只存储心理分析相关字段到risk_profile
cognition.risk_profile.update({
    "tolerance": risk_profile_data.get("tolerance"),
    "decision_style": risk_profile_data.get("decision_style"),
    "confidence_level": risk_profile_data.get("confidence_level"),
    "current_sentiment": analysis.get("current_sentiment"),
    # 移除：age_range, family_structure, monthly_expense, occupation, income_range
})
```

---

### 中优先级（建议近期优化）

#### 4. 放宽UserAsset.value约束
**修复方案**：
```python
# 修改模型定义
class UserAsset(SQLModel, table=True):
    value: float | None = Field(default=None, ge=0)  # 允许NULL，表示未知
    value_estimated: bool = Field(default=False)     # 是否为估算值
```

#### 5. 实现审计日志自动化
**修复方案**：
```python
from sqlalchemy import event

@event.listens_for(UserAsset, 'after_update')
def receive_after_update(mapper, connection, target):
    # 自动记录到AuditLog
    audit_log = AuditLog(
        table_name='userasset',
        record_id=target.id,
        action='UPDATE',
        user_id=target.user_id,
        old_values={...},
        new_values={...}
    )
    connection.execute(audit_log.insert())
```

#### 6. 添加VectorMemory嵌入重试机制
**修复方案**：
```python
async def _generate_embedding_with_retry(self, text: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.warning(f"Embedding generation failed (attempt {attempt+1}): {e}")
            if attempt == max_retries - 1:
                return None
            await asyncio.sleep(1)  # 等待1秒后重试
```

---

### 低优先级（可选优化）

#### 7. 添加数据完整性检查
- 定期检查UserProfile和UserCognition.risk_profile的一致性
- 检测并修复孤立记录（如没有User的UserAsset）

#### 8. 优化查询性能
- 为常用查询添加复合索引
- 考虑使用Redis缓存热点数据（如UserProfile）

#### 9. 实现数据归档
- 将超过1年的ChatMessage归档到历史表
- 定期清理无用的VectorMemory

---


## 📝 数据更新时机完整清单

### User表
- ✅ **创建**：用户注册/登录时（`POST /auth/login`）
- ⚠️ **更新**：几乎不更新（只在更换设备时更新device_id）
- ❌ **删除**：不支持（需要实现GDPR合规）

### UserProfile表
- ✅ **创建**：LLM提取到完整画像信息时（age_range + family_structure + risk_preference）
- ✅ **更新**：
  - Phase 2信息提取后（`asset_extraction_service._update_user_profile_from_extraction()`）
  - 用户明确修改个人信息时
- ❌ **删除**：不支持

### UserAsset表
- ✅ **创建**：
  - Phase 2信息提取后（`asset_extraction_service._update_assets_from_extraction()`）
  - 用户手动添加资产时
- ✅ **更新**：
  - LLM提取到新的资产价值时
  - 用户修正资产信息时
  - 房产估值更新时
- ⚠️ **删除**：当前不支持（建议添加软删除标志）

### UserCognition表
- ✅ **创建**：首次对话时自动创建
- ✅ **更新**：
  - Phase 2信息提取后（`asset_extraction_service._update_cognition_from_extraction()`）
    - 更新financial_goals
    - 更新risk_profile
    - 更新collection_status
  - Phase 3心理分析后（`insight_service._update_cognition_insights()`）
    - 更新risk_profile（心理特征）
    - 更新advisor_note
- ❌ **删除**：不支持

### VectorMemory表
- ✅ **创建**：
  - Phase 3心理分析时提取关键记忆（`insight_service._extract_and_store_key_memories()`）
  - 检测到重要生活事件时
- ❌ **更新**：不支持（只追加）
- ✅ **删除**：支持手动删除（`memory_service.delete_memory()`）

### ChatMessage表
- ✅ **创建**：
  - 用户发送消息时（`chat_history_service.save_user_message()`）
  - AI生成回复后（`chat_history_service.save_ai_message()`）
- ❌ **更新**：不支持（只追加）
- ❌ **删除**：不支持（建议实现归档机制）

### CommercialProduct表
- ✅ **创建**：管理员手动添加
- ✅ **更新**：管理员手动更新
- ✅ **删除**：软删除（设置is_active=False）

### UserInteraction表
- ✅ **创建**：用户与商业产品交互时
- ❌ **更新**：不支持（只追加）
- ❌ **删除**：不支持

### AuditLog表
- ⚠️ **创建**：应该在所有数据变更时自动创建（当前未实现）
- ❌ **更新**：不支持（只追加）
- ❌ **删除**：不支持（建议实现归档机制）

### UserAssetHistory表
- ⚠️ **创建**：应该在UserAsset变更时自动创建（当前未实现）
- ❌ **更新**：不支持（只追加）
- ❌ **删除**：不支持

---

## 🔍 数据一致性检查建议

### 检查项1：UserProfile与UserCognition.risk_profile一致性
```sql
-- 查找不一致的记录
SELECT 
    u.id,
    up.age_range AS profile_age,
    uc.risk_profile->>'age_range' AS cognition_age,
    up.occupation AS profile_occupation,
    uc.risk_profile->>'occupation' AS cognition_occupation
FROM user u
LEFT JOIN userprofile up ON u.id = up.user_id
LEFT JOIN usercognition uc ON u.id = uc.user_id
WHERE 
    (up.age_range IS NOT NULL AND uc.risk_profile->>'age_range' IS NOT NULL 
     AND up.age_range != uc.risk_profile->>'age_range')
    OR
    (up.occupation IS NOT NULL AND uc.risk_profile->>'occupation' IS NOT NULL 
     AND up.occupation != uc.risk_profile->>'occupation');
```

### 检查项2：孤立的UserAsset记录
```sql
-- 查找没有对应User的资产
SELECT ua.* 
FROM userasset ua
LEFT JOIN user u ON ua.user_id = u.id
WHERE u.id IS NULL;
```

### 检查项3：collection_status与实际资产不一致
```sql
-- 查找标记为已收集但实际没有资产的情况
SELECT 
    u.id,
    uc.collection_status,
    COUNT(ua.id) AS actual_asset_count
FROM user u
JOIN usercognition uc ON u.id = uc.user_id
LEFT JOIN userasset ua ON u.id = ua.user_id
GROUP BY u.id, uc.collection_status
HAVING 
    (uc.collection_status->>'real_estate' = 'true' 
     AND SUM(CASE WHEN ua.asset_type = 'REAL_ESTATE' THEN 1 ELSE 0 END) = 0);
```

---

## 📚 相关文档

- [Phase 2实现总结](Memory/PHASE2_IMPLEMENTATION_SUMMARY.md)
- [Phase 3认知洞察总结](Memory/PHASE3_COGNITIVE_INSIGHT_SUMMARY.md)
- [Phase 4向量记忆总结](Memory/PHASE4_VECTOR_MEMORY_SUMMARY.md)
- [Profile数据流修复](fix_summary/profile_data_flow_fix_summary.md)

---

**文档生成时间**：2026-01-14
**分析范围**：AssetFlow Backend所有数据模型和服务层代码
**分析深度**：表结构、关联关系、更新逻辑、业务问题、优化建议
