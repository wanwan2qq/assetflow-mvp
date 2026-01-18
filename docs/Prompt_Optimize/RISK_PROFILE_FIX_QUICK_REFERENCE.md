# Risk Profile 更新修复 - 快速参考

## 问题

`UserCognition.risk_profile` 只更新了 `tolerance` 字段，其他心理画像字段（`decision_style`、`sentiment`、`liquidity_anxiety` 等）未更新。

## 根本原因

`chat_agent.py` 中的 `_update_cognition_state()` 方法存在冗余的 `risk_profile` 更新逻辑，只更新了 `tolerance` 字段，与 `InsightService` 的完整更新逻辑冲突。

## 解决方案

### 修改文件

**backend/app/services/chat_agent.py**

删除 `_update_cognition_state()` 方法中的 `risk_profile` 更新逻辑：

```python
# ❌ 删除以下代码
# Update risk profile if provided
if profile and hasattr(profile, 'risk_preference'):
    if not cognition.risk_profile:
        cognition.risk_profile = {}
    cognition.risk_profile['tolerance'] = profile.risk_preference
    cognition.updated_at = datetime.utcnow()
```

### 职责划分

- **chat_agent._update_cognition_state()**: 只负责更新 `collection_status`
- **insight_service._update_cognition_insights()**: 负责更新完整的 `risk_profile`

## 验证

运行测试脚本：

```bash
cd backend
python test_risk_profile_complete_update.py
```

### 预期结果

```
✅ Risk Profile Fields Found:
   - tolerance: conservative
   - decision_style: data_driven
   - sentiment: anxious
   - liquidity_anxiety: high
   - confidence_score: 0.7
   - loss_aversion: high
   - financial_literacy: intermediate
   - family_responsibility: high
   - planning_horizon: medium
   - last_analysis: 2026-01-18T10:30:00

✅ TEST PASSED: All expected fields are present!
```

## 日志监控

### 正确的日志模式

```
🔄 COGNITION_UPDATE: Updated collection_status for user 1
✅ INSIGHT_UPDATE: Updated complete risk_profile for user 1
✅ INSIGHT_UPDATE: Fields updated: ['tolerance', 'decision_style', 'sentiment', ...]
✅ INSIGHT_UPDATE: Values: tolerance=conservative, sentiment=anxious, liquidity_anxiety=high
```

### 错误的日志模式（修复前）

```
Updated cognition state for user 1  # ❌ 只更新了 tolerance
```

## 相关文档

- [完整分析文档](./RISK_PROFILE_UPDATE_ISSUE_ANALYSIS.md)
- [InsightService 文档](../Memory/PHASE3_QUICK_REFERENCE.md)
- [心理画像提示词](../../backend/app/prompts/insight/psychology_analysis.yaml)

## 影响范围

- ✅ 心理画像分析更完整
- ✅ 顾问策略调整更精准
- ✅ 用户体验个性化更好
- ✅ 避免数据冲突和不一致

## 优先级

🔴 **高优先级** - 影响核心功能（心理画像分析）
