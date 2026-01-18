# Risk Profile 数据流程图

## 问题场景：两条更新路径冲突

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户发送消息                                  │
│                    "我比较保守，不想冒太大风险"                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ chat_agent.process_  │
                  │    message()         │
                  └──────────┬───────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │   路径 A (同步)        │   │   路径 B (异步)         │
    │   _extract_and_store_ │   │   _background_         │
    │   information()       │   │   extraction_pipeline()│
    └───────────┬───────────┘   └────────────┬───────────┘
                │                            │
                ▼                            ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │ _update_cognition_    │   │ _trigger_insight_      │
    │    state()            │   │    analysis()          │
    └───────────┬───────────┘   └────────────┬───────────┘
                │                            │
                ▼                            ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │ ❌ 问题代码（已删除）  │   │ InsightService.        │
    │                       │   │ analyze_user_          │
    │ cognition.risk_       │   │    psychology()        │
    │   profile['tolerance']│   └────────────┬───────────┘
    │   = profile.risk_     │                │
    │     preference        │                ▼
    │                       │   ┌────────────────────────┐
    │ 只更新 tolerance      │   │ _update_cognition_     │
    └───────────────────────┘   │    insights()          │
                                └────────────┬───────────┘
                                             │
                                             ▼
                                ┌────────────────────────┐
                                │ ✅ 正确实现            │
                                │                        │
                                │ cognition.risk_profile │
                                │   .update({            │
                                │     "tolerance": ...,  │
                                │     "decision_style": │
                                │     "sentiment": ...,  │
                                │     "liquidity_anxiety"│
                                │     "confidence_score" │
                                │     "loss_aversion":   │
                                │     "financial_        │
                                │       literacy": ...,  │
                                │     "family_           │
                                │       responsibility"  │
                                │     "planning_horizon" │
                                │   })                   │
                                │                        │
                                │ 更新所有 10 个字段     │
                                └────────────────────────┘
```

## 修复前的数据冲突场景

### 场景 1：路径 A 先执行，路径 B 后执行

```
时间轴：
T0: 用户发送消息
T1: 路径 A 执行 → risk_profile = {"tolerance": "conservative"}
T2: 路径 B 执行 → risk_profile = {"tolerance": "conservative", "sentiment": "anxious", ...}

结果：✅ 最终数据正确（但有短暂的不一致期）
```

### 场景 2：路径 A 执行，路径 B 失败

```
时间轴：
T0: 用户发送消息
T1: 路径 A 执行 → risk_profile = {"tolerance": "conservative"}
T2: 路径 B 失败（LLM API 错误）→ 没有更新

结果：❌ 只有 tolerance，其他字段缺失
```

### 场景 3：路径 B 未触发（消息数 < 3）

```
时间轴：
T0: 用户发送第 1 条消息
T1: 路径 A 执行 → risk_profile = {"tolerance": "conservative"}
T2: 路径 B 跳过（消息数不足）→ 没有更新

结果：❌ 只有 tolerance，其他字段缺失
```

## 修复后的数据流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                         用户发送消息                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ chat_agent.process_  │
                  │    message()         │
                  └──────────┬───────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │   路径 A (同步)        │   │   路径 B (异步)         │
    │   只更新              │   │   完整更新              │
    │   collection_status   │   │   risk_profile         │
    └───────────┬───────────┘   └────────────┬───────────┘
                │                            │
                ▼                            ▼
    ┌───────────────────────┐   ┌────────────────────────┐
    │ ✅ 职责清晰            │   │ ✅ 职责清晰             │
    │                       │   │                        │
    │ 只更新资产收集状态：   │   │ 更新完整心理画像：      │
    │                       │   │                        │
    │ collection_status = { │   │ risk_profile = {       │
    │   "real_estate": true,│   │   "tolerance": ...,    │
    │   "cash": true,       │   │   "decision_style": ..│
    │   "investment": false │   │   "sentiment": ...,    │
    │ }                     │   │   "liquidity_anxiety": │
    │                       │   │   "confidence_score":  │
    │ ✅ 不再更新           │   │   "loss_aversion": ... │
    │    risk_profile       │   │   "financial_literacy" │
    └───────────────────────┘   │   "family_             │
                                │     responsibility":   │
                                │   "planning_horizon":  │
                                │ }                      │
                                │                        │
                                │ ✅ 唯一更新源          │
                                └────────────────────────┘
```

## 职责划分矩阵

| 数据字段 | 路径 A (chat_agent) | 路径 B (insight_service) |
|---------|---------------------|--------------------------|
| `collection_status` | ✅ 负责更新 | ❌ 不涉及 |
| `risk_profile.tolerance` | ❌ 不再更新 | ✅ 负责更新 |
| `risk_profile.decision_style` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.sentiment` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.liquidity_anxiety` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.confidence_score` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.loss_aversion` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.financial_literacy` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.family_responsibility` | ❌ 不涉及 | ✅ 负责更新 |
| `risk_profile.planning_horizon` | ❌ 不涉及 | ✅ 负责更新 |
| `advisor_note` | ❌ 不涉及 | ✅ 负责更新 |

## 数据完整性保证

### 修复前（❌ 不可靠）

```python
# 可能的数据状态
risk_profile = {
    "tolerance": "conservative"  # 只有这一个字段
}

# 或者（如果路径 B 成功执行）
risk_profile = {
    "tolerance": "conservative",
    "decision_style": "data_driven",
    "sentiment": "anxious",
    # ... 其他字段
}
```

**问题**：数据完整性不确定，取决于执行顺序和成功状态

### 修复后（✅ 可靠）

```python
# 初始状态（路径 B 未执行）
risk_profile = {}  # 空字典

# 路径 B 执行后（要么全部更新，要么不更新）
risk_profile = {
    "tolerance": "conservative",
    "decision_style": "data_driven",
    "sentiment": "anxious",
    "liquidity_anxiety": "high",
    "confidence_score": 0.7,
    "loss_aversion": "high",
    "financial_literacy": "intermediate",
    "family_responsibility": "high",
    "planning_horizon": "medium",
    "last_analysis": "2026-01-18T10:30:00"
}
```

**优势**：数据完整性有保证，要么全有，要么全无

## 触发时机

### InsightService 触发条件

```python
# 条件 1：新消息数量 >= 3
if len(recent_messages) < 3:
    return {"skipped": True, "reason": "insufficient_new_messages"}

# 条件 2：每 3 轮对话触发一次
if message_count % 3 != 0:
    return {"skipped": True, "reason": "not_at_trigger_interval"}
```

### 触发时间线示例

```
消息 1: "我今年35岁" → 跳过（消息数 < 3）
消息 2: "我有一套房产" → 跳过（消息数 < 3）
消息 3: "我比较保守" → ✅ 触发分析（消息数 = 3）
消息 4: "我担心房贷" → 跳过（不在触发间隔）
消息 5: "手头有点紧" → 跳过（不在触发间隔）
消息 6: "怎么投资" → ✅ 触发分析（消息数 = 6，3 的倍数）
```

## 日志监控模式

### 正确的日志序列

```
[T0] User message received
[T1] 🔄 COGNITION_UPDATE: Updated collection_status for user 1
[T2] ✅ Started background extraction pipeline for user 1
[T3] 🔍 Triggering incremental insight analysis for user 1 at turn 3
[T4] ✅ INSIGHT_UPDATE: Updated complete risk_profile for user 1
[T5] ✅ INSIGHT_UPDATE: Fields updated: ['tolerance', 'decision_style', ...]
[T6] ✅ INSIGHT_UPDATE: Values: tolerance=conservative, sentiment=anxious, ...
```

### 错误的日志序列（修复前）

```
[T0] User message received
[T1] Updated cognition state for user 1  # ❌ 只更新了 tolerance
[T2] ✅ Started background extraction pipeline for user 1
[T3] Skipping insight analysis - insufficient messages  # ❌ 路径 B 未执行
```

## 总结

通过删除路径 A 中的冗余更新逻辑，确保了：

1. **单一职责**：只有 InsightService 负责 `risk_profile`
2. **数据完整性**：要么全部更新，要么不更新
3. **避免冲突**：不会出现部分字段更新的情况
4. **易于维护**：职责清晰，代码简洁
