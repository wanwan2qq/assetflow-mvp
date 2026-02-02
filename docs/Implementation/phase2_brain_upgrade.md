# Phase 2 技术方案：知识扩容与精准检索 (RAG 2.0)

## 1. 背景与目标 (Context & Goals)

当前 RAG 系统存在"检索粒度过粗"的问题。当用户询问"首付比例"时，系统可能会检索到多个城市的政策（因为语义相似），导致 AI 混淆或输出错误城市的政策。

**本阶段目标**：
1.  **精准检索 (Precision Retrieval)**：在检索阶段引入**元数据过滤 (Metadata Filtering)**，特别是基于**城市 (City)** 的过滤。
2.  **结构化知识 (Structured Knowledge)**：完善 `PolicyKnowledge` 的数据结构，确保地域性政策有明确的标签。
3.  **按需增强 (On-Demand Augmentation)**：优化 RAGEngine，确保仅在通过意图识别确认为 Policy/Advisory 且需要外部知识时才触发检索。

## 2. 核心架构变更 (Architecture Changes)

### 2.1 知识检索层 (KnowledgeRetriever)

支持基于元数据的硬过滤（Hard Filter）。

- **接口变更**:
  ```python
  async def search(
      self, 
      query: str, 
      filters: dict | None = None,  # New: {"city": "Beijing", "category": "policy"}
      top_k: int = 5
  )
  ```

- **过滤逻辑**:
  - `City Filter`:如果是地域性知识库（如 Policy），当传入 `city` 过滤条件时，SQL 查询应包含：
    `WHERE (city = :target_city OR city IS NULL)`
    *注：`city IS NULL` 代表全国通用政策，应当保留。*

### 2.2 RAG 引擎层 (RAGEngine)

负责连接 Context 与 Retriever。

- **逻辑流程**:
  1. 从 `ConversationOrchestrator` 传入的 `user_context` 中提取 `city`。
  2. 如果 `user_context` 中有 `city`，则在调用 `retriever.search()` 时构造 `filters={"city": city}`。
  3. 如果用户问题中显式包含了其他城市名（例如人在北京问"上海限购吗"），需要更高阶的实体提取来覆盖 Context（本阶段暂通过并在 Query 中保留城市词来依赖语义匹配，或者简单提取）。
  *策略：Phase 2 优先实现 Context 过滤。如果 Query 语义强匹配其他城市，向量搜索通常能因为 Embedding 距离近而召回（前提是不被 Hard Filter 过滤掉）。*
  
  *> 修正策略：为了支持"人在北京问上海"，Hard Filter 应该比较宽松，或者由 Intent Classifier 提取显式实体 `query_entities`。如果 `query_entities` 包含城市，则**优先**使用 query 中的城市作为 Filter，否则使用 Context 中的城市。*
  
  **本次实现范围**：优先支持 Context City Filtering。

### 2.3 数据层 (Data)

- **Policies.yaml**:
  规范化数据录入，必须包含 `city` 字段。
  ```yaml
  - title: "北京市居民家庭购房限购政策"
    category: "policy"
    city: "北京"  # Key Field
    content: |
      ...
  ```

## 3. 详细实施步骤 (Implementation Steps)

### Step 1: 改造 KnowledgeRetriever
- 修改 `vector_search` 和 `keyword_search`，接收 `filters` 参数。
- 在 `select` 语句中动态构建 `where` 子句。

### Step 2: 改造 RAGEngine
- 在 `query` 方法中，解析 `user_context`。
- 构建 `filters` 字典传给 Retriever。

### Step 3: 数据治理
- 检查并更新 `backend/data/knowledge/policies.yaml`。
- 运行 `init_knowledge_base.py` 刷新数据库（需处理 Upsert 或清库逻辑，当前脚本跳过已存在，可能需要手动清理数据或更新脚本以支持更新）。

### Step 4: 验证
- 编写测试脚本验证：设置 Context 为北京，搜索 "首付"，确认不返回上海的政策。

## 4. 预期效果
用户（画像：北京）问："首付多少？" -> 系统检索 `city='北京' OR city=NULL` -> 精准回答北京首付政策。
用户（画像：上海）问："首付多少？" -> 系统检索 `city='上海' OR city=NULL` -> 精准回答上海首付政策。
