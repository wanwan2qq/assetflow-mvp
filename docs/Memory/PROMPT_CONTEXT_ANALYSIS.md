# ChatAI Prompt Context 分析报告

**分析日期**: 2026-01-15  
**分析对象**: AssetFlow ChatAgent 给 LLM 的 Prompt 内容

---

## 📋 核心发现

### 给 LLM 的 Prompt 包含以下信息（按顺序）：

1. **Fact Sheet（用户信息事实表）** - L1/L2 数据
2. **Relevant Memories（相关记忆）** - L4 向量记忆（RAG）
3. **Advisor Strategy Note（顾问策略笔记）** - L3 心理分析
4. **用户当前消息**
5. **对话阶段提示**
6. **已提取资产摘要**
7. **用户画像动态提示**

### L0 对话记录：

- **存储位置**: `context.conversation_history`（内存中）
- **使用范围**: 最近 **10 条消息**（5 轮对话）
- **用途**: 仅用于信息提取（extraction），**不直接传给 LLM**

---

## 🔍 详细分析

### 1. Prompt 构建流程

**代码位置**: `backend/app/services/chat_agent.py` - `_prepare_contextual_input()` 方法（第 1002-1070 行）

```python
async def _prepare_contextual_input(self, message: str, context: ChatContext, user_id: int) -> str:
    """Prepare input with conversation context and Fact Sheet for better AI responses"""
    contextual_parts = []
    
    # 1. Fact Sheet（最重要，防止 AI 幻觉）
    fact_sheet = await self._generate_fact_sheet(user_id)
    contextual_parts.append(fact_sheet)
    
    # 2. Relevant Memories（Phase 4: 向量记忆 RAG）
    relevant_memories = await self._retrieve_relevant_memories(user_id, message)
    if relevant_memories:
        memory_context = "\n\n🧠 【RELEVANT MEMORIES】\n"
        for i, memory in enumerate(relevant_memories, 1):
            memory_context += f"{i}. {memory['content']} (相关度: {memory['similarity']:.2f})\n"
        contextual_parts.append(memory_context)
    
    # 3. Advisor Strategy Note（Phase 3: 心理分析）
    advisor_note = await self._get_advisor_strategy_note(user_id)
    if advisor_note:
        contextual_parts.append(f"\n\n💡 【ADVISOR STRATEGY NOTE】\n{advisor_note}")
    
    # 4. 用户当前消息
    contextual_parts.append(f"\n【用户消息】\n{message}")
    
    # 5. 对话阶段提示
    if context.current_stage == "initial":
        contextual_parts.append("\n[系统提示: 用户刚开始对话，需要了解房产情况]")
    # ... 其他阶段
    
    # 6. 已提取资产摘要
    if context.extracted_assets:
        asset_summary = f"\n[已提取资产: {len(context.extracted_assets)}项]"
        contextual_parts.append(asset_summary)
    
    # 7. 用户画像动态提示
    if context.user_profile:
        # 风险偏好提示
        # 年龄段提示
        # 债务压力提示
        # ...
    
    return "".join(contextual_parts)
```

---

### 2. Fact Sheet 内容详解

**代码位置**: `backend/app/services/chat_agent.py` - `_generate_fact_sheet()` 方法（第 832-1001 行）

**数据来源**: 直接从数据库查询（L1/L2 层）

**包含内容**:

```
【当前系统已确信的用户信息 (Fact Sheet)】

【用户基本画像】
• 年龄段: 30-40岁
• 家庭结构: 已婚有子女
• 职业: 软件工程师
• 收入范围: 20-30万/年
• 月支出: 1.5万
• 风险偏好: 稳健型
• 财务目标: 退休规划, 子女教育

【资产清单】
1. [房产] 北京朝阳区公寓 | 估值: 500万 | 面积: 120平米 | 位置: 北京朝阳区 (用户已确认)
2. [现金] 50万 (用户已确认)
3. [投资] 股票基金 | 价值: 30万 (系统推测)
4. [负债] 房贷 | 金额: 200万 (用户已确认)

【缺失信息提示】
尚未了解: 保险保障

[重要提示] 请基于以上已确认的用户信息和资产数据回答问题，严禁编造或假设未提供的数据。
```

**数据库查询**:
- `UserProfile` 表（L1）: 年龄、家庭、职业、收入、月支出、风险偏好
- `UserAsset` 表（L1）: 所有资产（房产、现金、投资、保险、负债）
- `UserCognition` 表（L2）: 财务目标、收集状态

---

### 3. Relevant Memories（向量记忆）

**代码位置**: `backend/app/services/chat_agent.py` - `_retrieve_relevant_memories()` 方法（第 1072-1095 行）

**检索参数**:
```python
memories = await memory_service.retrieve_relevant(
    user_id=user_id,
    query_text=query_text,
    limit=3,  # 最多返回 3 条相关记忆
    similarity_threshold=0.7  # 相似度阈值 0.7（高相关性）
)
```

**输出格式**:
```
🧠 【RELEVANT MEMORIES】
1. 用户提到过担心房贷压力 (相关度: 0.85)
2. 用户对股市投资比较保守 (相关度: 0.78)
3. 用户计划5年后送孩子出国留学 (相关度: 0.72)
[重要提示: 这些是用户之前提到的关键信息，请在回复中考虑这些背景。]
```

**数据来源**: `VectorMemory` 表（L4 层）- 使用 BGE 嵌入模型进行语义搜索

---

### 4. Advisor Strategy Note（顾问策略笔记）

**代码位置**: `backend/app/services/chat_agent.py` - `_get_advisor_strategy_note()` 方法（第 813-828 行）

**数据来源**: `insight_service.get_advisor_strategy(user_id)` - L3 心理分析结果

**输出格式**:
```
💡 【ADVISOR STRATEGY NOTE】
用户当前情绪: 焦虑（关于房贷压力）
决策风格: 分析型，需要详细数据支持
建议策略: 
- 优先讨论降低债务压力的方案
- 提供具体数字和计算过程
- 避免过于激进的投资建议
[重要提示: 根据上述策略调整你的语气和建议方向。用户看不到这条笔记。]
```

**数据来源**: `UserCognition.risk_profile` 表（L3 层）- 心理分析结果

---

### 5. 对话历史记录（L0）

**代码位置**: `backend/app/services/chat_agent.py` - `_trigger_information_extraction()` 方法（第 720-765 行）

**关键代码**:
```python
# Prepare conversation history for LLM context
conversation_history = []
for msg in context.conversation_history[-10:]:  # Last 10 messages
    conversation_history.append({
        "role": msg.get("role", "user"),
        "content": msg.get("content", "")
    })
```

**重要发现**:

1. **存储位置**: `context.conversation_history`（内存中的列表）
2. **数量限制**: 最近 **10 条消息**（即 5 轮对话：5 个用户消息 + 5 个 AI 回复）
3. **使用场景**: 
   - ✅ 用于信息提取（`extract_information(user_message, conversation_history)`）
   - ❌ **不直接传给 LLM 生成回复**

**为什么不直接传给 LLM？**

因为系统采用了 **Fact Sheet + RAG** 架构：
- **Fact Sheet** 提供结构化的用户信息（更准确、更可靠）
- **Relevant Memories** 提供语义相关的历史信息（更智能、更相关）
- 直接传递对话历史会导致：
  - Token 消耗过大
  - 信息冗余
  - 难以控制上下文质量

---

### 6. 对话阶段提示

**代码位置**: `backend/app/services/chat_agent.py` - `_prepare_contextual_input()` 方法（第 1030-1043 行）

**阶段定义**:
```python
if context.current_stage == "initial":
    contextual_parts.append("\n[系统提示: 用户刚开始对话，需要了解房产情况]")
elif context.current_stage == "property_collection":
    contextual_parts.append("\n[系统提示: 已收集部分房产信息，继续完善或询问其他资产]")
elif context.current_stage == "asset_collection":
    contextual_parts.append("\n[系统提示: 房产信息较完整，需要收集其他资产和用户画像]")
elif context.current_stage == "analysis":
    contextual_parts.append("\n[系统提示: 信息收集完整，可以进行分析和建议]")
```

**阶段判断依据**: `UserCognition.collection_status`（L2 层）- 已收集的资产类型数量

---

### 7. 动态语气提示

**代码位置**: `backend/app/services/chat_agent.py` - `_prepare_contextual_input()` 方法（第 1051-1068 行）

**提示类型**:

1. **风险偏好提示**:
   ```python
   if risk_profile == "conservative":
       contextual_parts.append("\n[Tone Hint: Be extra cautious and focus on capital preservation]")
   elif risk_profile == "aggressive":
       contextual_parts.append("\n[Tone Hint: Focus on growth opportunities but remind about risks]")
   ```

2. **年龄段提示**:
   ```python
   if age and age > 50:
       contextual_parts.append("\n[Tone Hint: Focus on retirement planning and liquidity]")
   ```

3. **债务压力提示**:
   ```python
   if monthly_expenses and monthly_expenses > 20000:
       contextual_parts.append("\n[Tone Hint: Show empathy for financial pressure and focus on practical solutions]")
   ```

---

## 📊 数据层级总结

| 层级 | 数据类型 | 是否传给 LLM | 用途 | 数据来源 |
|------|----------|--------------|------|----------|
| **L0** | 对话历史 | ❌ 否 | 信息提取 | `context.conversation_history`（最近10条） |
| **L1** | 用户事实 | ✅ 是（Fact Sheet） | 防止幻觉 | `UserProfile`, `UserAsset` |
| **L2** | 收集状态 | ✅ 是（Fact Sheet） | 引导对话 | `UserCognition.collection_status` |
| **L3** | 心理分析 | ✅ 是（Advisor Note） | 调整策略 | `UserCognition.risk_profile` |
| **L4** | 向量记忆 | ✅ 是（RAG） | 语义检索 | `VectorMemory`（最多3条） |

---

## 🎯 关键设计决策

### 为什么对话历史不直接传给 LLM？

1. **Token 效率**: 10 条消息可能包含大量冗余信息
2. **信息质量**: Fact Sheet 提供结构化、可靠的数据
3. **语义相关性**: RAG 检索比时间顺序更智能
4. **成本控制**: 减少不必要的 Token 消耗

### 为什么是 10 条消息（5 轮对话）？

**代码位置**: `backend/app/services/chat_agent.py` 第 735 行

```python
for msg in context.conversation_history[-10:]:  # Last 10 messages
```

**设计考量**:
- **足够的上下文**: 5 轮对话足以捕捉用户的意图和信息
- **性能平衡**: 不会过度消耗 Token
- **信息提取**: 为 LLM 提取提供足够的历史背景

### 为什么 RAG 只检索 3 条记忆？

**代码位置**: `backend/app/services/chat_agent.py` 第 1086 行

```python
limit=3,  # 最多返回 3 条相关记忆
similarity_threshold=0.7  # 相似度阈值 0.7
```

**设计考量**:
- **高质量**: 只返回高度相关的记忆（相似度 > 0.7）
- **避免噪音**: 太多记忆会干扰 LLM 判断
- **Token 控制**: 3 条记忆通常不超过 200 tokens

---

## 📝 完整 Prompt 示例

```
【当前系统已确信的用户信息 (Fact Sheet)】

【用户基本画像】
• 年龄段: 30-40岁
• 家庭结构: 已婚有子女
• 职业: 软件工程师
• 收入范围: 20-30万/年
• 月支出: 1.5万
• 风险偏好: 稳健型
• 财务目标: 退休规划, 子女教育

【资产清单】
1. [房产] 北京朝阳区公寓 | 估值: 500万 | 面积: 120平米 | 位置: 北京朝阳区 (用户已确认)
2. [现金] 50万 (用户已确认)
3. [投资] 股票基金 | 价值: 30万 (系统推测)

【缺失信息提示】
尚未了解: 保险保障

[重要提示] 请基于以上已确认的用户信息和资产数据回答问题，严禁编造或假设未提供的数据。

🧠 【RELEVANT MEMORIES】
1. 用户提到过担心房贷压力 (相关度: 0.85)
2. 用户对股市投资比较保守 (相关度: 0.78)
[重要提示: 这些是用户之前提到的关键信息，请在回复中考虑这些背景。]

💡 【ADVISOR STRATEGY NOTE】
用户当前情绪: 焦虑（关于房贷压力）
决策风格: 分析型，需要详细数据支持
建议策略: 优先讨论降低债务压力的方案
[重要提示: 根据上述策略调整你的语气和建议方向。用户看不到这条笔记。]

【用户消息】
我现在有点担心房贷压力，应该怎么调整投资策略？

[系统提示: 房产信息较完整，需要收集其他资产和用户画像]
[已提取资产: 3项]
[用户画像: age_range, family_structure, occupation, income_range, monthly_expense, risk_preference]
[Tone Hint: Show empathy for financial pressure and focus on practical solutions]
```

---

## 🔧 代码位置速查

| 功能 | 方法名 | 文件 | 行号 |
|------|--------|------|------|
| Prompt 构建 | `_prepare_contextual_input()` | `chat_agent.py` | 1002-1070 |
| Fact Sheet 生成 | `_generate_fact_sheet()` | `chat_agent.py` | 832-1001 |
| 向量记忆检索 | `_retrieve_relevant_memories()` | `chat_agent.py` | 1072-1095 |
| 顾问策略获取 | `_get_advisor_strategy_note()` | `chat_agent.py` | 813-828 |
| 信息提取触发 | `_trigger_information_extraction()` | `chat_agent.py` | 720-765 |
| 对话历史定义 | `ChatContext` 类 | `chat_agent.py` | 35-47 |

---

## 💡 优化建议

### 当前架构的优势

✅ **Fact Sheet 架构**: 防止 AI 幻觉，提供可靠的用户信息  
✅ **RAG 检索**: 智能检索相关历史信息，比时间顺序更有效  
✅ **分层设计**: L0-L4 清晰分离，各司其职  
✅ **Token 效率**: 不直接传递对话历史，节省成本

### 潜在优化方向

1. **对话历史可视化**: 虽然不传给 LLM，但可以在 UI 中展示给用户
2. **动态调整记忆数量**: 根据查询复杂度动态调整 RAG 检索数量（3-5 条）
3. **对话历史压缩**: 如果需要更长的上下文，可以使用 LLM 压缩历史对话
4. **分阶段 Prompt**: 根据对话阶段动态调整 Prompt 结构

---

## 📚 相关文档

- [Dual-Process Architecture](./DUAL_PROCESS_ARCHITECTURE_REFACTOR.md)
- [Phase 4: Vector Memory](./PHASE4_VECTOR_MEMORY_SUMMARY.md)
- [Phase 3: Cognitive Insights](./PHASE3_COGNITIVE_INSIGHT_SUMMARY.md)
- [Fact Sheet Quick Reference](./FACT_SHEET_QUICK_REFERENCE.md)

---

**分析完成日期**: 2026-01-15  
**分析人员**: System Architect & Senior Backend Engineer
