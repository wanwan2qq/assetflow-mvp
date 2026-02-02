# Phase 1 技术实现方案：大脑升级 (Intent + Memory)

## 1. 目标
通过引入意图识别和长短期记忆联动，让 AI 能够准确理解用户意图，不再"答非所问"或"健忘"，解决 Stale Context 问题，提升对话的连贯性和个性化。

## 2. 核心组件设计

### 2.1 意图分类服务 (IntentClassifier)

不再让主对话 LLM 猜测意图，而是前置一个轻量级分类步骤。

- **位置**: `app/services/intent_classifier.py`
- **输入**: 用户最新消息 + 最近 2 轮对话历史
- **输出**: `IntentResult` (intent_type, confidence, metadata)
- **分类体系**:
  ```python
  class IntentType(str, Enum):
      INFO_COLLECTION = "info_collection"   # 资产/画像录入 (我月入3万)
      POLICY_QUERY = "policy_query"         # 政策/产品咨询 (北京买房资格)
      ADVISORY = "advisory"                 # 寻求建议 (我该怎么配置)
      CHIT_CHAT = "chit_chat"               # 闲聊/确认 (好的/谢谢)
      ACTION_REQUEST = "action_request"     # 指令 (生成报告/修改估值)
  ```
- **实现策略**:
  - **Level 1 (Fast)**: 正则/关键词匹配 (e.g. "政策", "买房" -> POLICY_QUERY)
  - **Level 2 (Smart)**: 轻量级 LLM 调用 (GPT-3.5-turbo / DeepSeek-V3-Mini) for nuanced classification.
  - **Prompt**: 专门的 Few-shot prompt，仅输出 JSON。

### 2.2 记忆服务集成 (Memory Integration)

启用 `MemoryService`，使其真正介入对话流程。

- **召唤点 (Recall)**: 在构建 System Prompt 之前。
- **流程**:
  1. **Query 生成**: 提取用户消息中的关键实体 (e.g. "我想投资")。
  2. **向量检索**: `MemoryService.retrieve_relevant(user_id, query_text)`
  3. **记忆过滤**: 过滤掉相关度低 (< 0.75) 的记忆。
  4. **上下文注入**: 将记忆注入到 Prompt 的 `<RelevantMemories>` 区块。

### 2.3 动态 System Prompt (Dynamic Context)

重构 `agent_system.yaml`，不再使用单一的静态 Prompt，而是根据意图动态组装。

- **Base Prompt**: 核心人设 (Assets Expert)。
- **Modules**:
  - `[MEMORY_BLOCK]`: 召回的长期记忆。
  - `[RAG_BLOCK]`: 检索的知识 (仅 Policy/Advisory 意图)。
  - `[TASK_INSTRUCTION]`: 基于意图的具体指令。
    - *Info*: "确认收到，简要分析，询问下一步"
    - *Policy*: "基于知识库回答，不要编造"
    - *Advisory*: "结合用户资产给建议"

---

## 3. 详细实施步骤 (Step-by-Step Implementation)

### Step 1: 基础设施准备
1. 创建 `app/services/intent_classifier.py`。
2. 定义 `IntentResult` Pydantic 模型。
3. 实现基于 LLM 的分类逻辑 (使用 `generate(json_mode=True)`).

### Step 2: 编排层重构 (ConversationOrchestrator)
修改 `process_message` 流程：

```python
async def process_message(self, user_id, message):
    # 1. 意图识别 (并行)
    context_task = self.context_manager.get_context(user_id)
    intent_task = self.intent_classifier.classify(message, recent_history)
    context, intent = await asyncio.gather(context_task, intent_task)
    
    # 2. 记忆与知识召回 (根据意图)
    memory_task = blank_task()
    rag_task = blank_task()
    
    if intent.type in [ADVISORY, CHIT_CHAT]:
        memory_task = self.memory_service.retrieve_relevant(user_id, message)
        
    if intent.type in [POLICY_QUERY, ADVISORY]:
        rag_task = self.rag_engine.retrieve(message)
        
    memories, knowledge = await asyncio.gather(memory_task, rag_task)
    
    # 3. 构建 Prompt
    system_prompt = self.prompt_builder.build(
        intent=intent,
        memories=memories,
        knowledge=knowledge,
        context=context
    )
    
    # 4. 生成回复 & 5. 后台提取 (保持不变)
    ...
```

### Step 3: Prompt 模板拆分
1. 创建 `app/prompts/chat/intent_instructions.yaml`。
2. 定义不同意图的专用指令。

### Step 4: 记忆写入优化
在 `_background_extraction_pipeline` 中，除了提取结构化资产，增加 "摘要记忆提取"：
- **Prompt**: "Summarize key user preferences, life events, or constraints from this conversation."
- **Action**: Call `MemoryService.add_memory()`.

---

## 4. 验收标准 Verification

1. **意图测试**:
   - 输入 "我年薪50万" -> 识别为 `INFO_COLLECTION`，且不触发 RAG。
   - 输入 "北京二套房首付" -> 识别为 `POLICY_QUERY`，触发 RAG。
   
2. **记忆测试**:
   - T1: 用户说 "我讨厌风险" (Memory Saved)
   - T2 (New Session): 用户说 "推荐个理财" -> AI 回复 "考虑到您之前提到偏好低风险..."

3. **性能测试**:
   - 意图分类耗时 < 500ms (使用 Cache/Fast Model)。
   - 整体回复首字延迟 (TTFT) < 2s。
