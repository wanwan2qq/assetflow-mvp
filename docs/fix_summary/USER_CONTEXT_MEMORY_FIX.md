# AI记忆问题修复：用户画像信息丢失

**问题报告时间**：2026-01-14  
**修复完成时间**：2026-01-14 23:50  
**严重程度**：🔴 高（影响用户体验）  
**测试状态**：✅ 已通过

---

## 🐛 问题描述

**用户反馈**：
> "已经提供了一些个人信息（如年龄和家庭情况）给AI，为什么它什么信息都不知道？"

**问题表现**：
- 用户提供了年龄、家庭结构、职业、收入等个人信息
- 数据已成功保存到数据库（UserProfile表）
- 但AI在后续对话中完全不记得这些信息
- AI表现得像第一次见到用户一样

---

## 🔍 根本原因分析

### 问题定位

通过代码审查发现，`chat_agent.py`中的`_generate_fact_sheet()`方法存在严重缺陷：

```python
# 问题代码（修复前）
async def _generate_fact_sheet(self, user_id: int) -> str:
    # ❌ 只读取了 UserAsset（资产）
    assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
    
    # ❌ 只读取了 UserCognition.risk_profile['tolerance']（风险偏好）
    if cognition and cognition.risk_profile:
        risk_info = cognition.risk_profile.get("tolerance", "未知")
        fact_lines.append(f"\n【用户画像】风险偏好: {risk_info}")
    
    # ❌ 完全没有读取 UserProfile 表！
    # 导致年龄、家庭、职业、收入等信息全部丢失
```

### 数据流分析

```
用户提供信息 → LLM提取 → 保存到UserProfile ✓
                                    ↓
                            AI生成回复时读取？ ✗
                                    ↓
                            Fact Sheet中缺失 ✗
                                    ↓
                            AI无法记住用户信息 ✗
```

### 影响范围

**丢失的信息**：
- ✗ 年龄段（age_range）
- ✗ 家庭结构（family_structure）
- ✗ 职业（occupation）
- ✗ 收入范围（income_range）
- ✗ 月支出（monthly_expense）
- ✗ 财务目标（financial_goals）

**保留的信息**：
- ✓ 资产信息（UserAsset）
- ✓ 风险偏好（仅tolerance字段）

---

## 🔧 修复方案

### 修复内容

在`_generate_fact_sheet()`方法中添加完整的UserProfile信息读取：

```python
# 修复后的代码
async def _generate_fact_sheet(self, user_id: int) -> str:
    """
    Generate detailed Fact Sheet of confirmed assets and user profile.
    FIXED: Now includes complete UserProfile information
    """
    
    # ✅ 添加 UserProfile 读取
    profile_statement = select(UserProfile).where(UserProfile.user_id == user_id)
    profile_result = await session.execute(profile_statement)
    profile = profile_result.scalar_one_or_none()
    
    # ✅ 在 Fact Sheet 顶部展示完整用户画像
    if profile:
        fact_lines.append("\n【用户基本画像】")
        
        if profile.age_range:
            fact_lines.append(f"• 年龄段: {profile.age_range}岁")
        
        if profile.family_structure:
            family_map = {
                "single": "单身",
                "married": "已婚",
                "married_with_kids": "已婚有子女",
                # ...
            }
            fact_lines.append(f"• 家庭结构: {family_map[profile.family_structure]}")
        
        if profile.occupation:
            fact_lines.append(f"• 职业: {profile.occupation}")
        
        if profile.income_range:
            fact_lines.append(f"• 收入范围: {profile.income_range}")
        
        if profile.monthly_expense:
            fact_lines.append(f"• 月支出: {profile.monthly_expense}")
        
        if profile.risk_preference:
            fact_lines.append(f"• 风险偏好: {profile.risk_preference}")
    
    # ✅ 添加财务目标
    if cognition and cognition.financial_goals:
        goals_str = ", ".join(cognition.financial_goals)
        fact_lines.append(f"• 财务目标: {goals_str}")
```

### Fact Sheet 对比

**修复前**：
```
【当前系统已确信的资产清单 (Fact Sheet)】
(暂无已确认资产)

【缺失信息提示】
尚未了解: 房产, 现金储蓄, 投资产品, 保险保障

【用户画像】风险偏好: moderate

(请基于以上数据回答，严禁编造数据)
```

**修复后**：
```
【当前系统已确信的用户信息 (Fact Sheet)】

【用户基本画像】
• 年龄段: 30-40岁
• 家庭结构: 已婚有子女
• 职业: 软件工程师
• 收入范围: 30-50万
• 风险偏好: 稳健型

【资产清单】
(暂无已确认资产)

【缺失信息提示】
尚未了解: 房产, 现金储蓄, 投资产品, 保险保障

[重要提示] 请基于以上已确认的用户信息和资产数据回答问题，严禁编造或假设未提供的数据。
```

---

## ✅ 测试验证

### 测试脚本
`scripts/test_user_context_fix.py`

### 测试场景

**场景**：用户提供个人信息
```
用户说: "我今年35岁，已婚有一个孩子，是软件工程师，年收入大概30-50万"
```

**验证点**：
1. ✅ 数据是否保存到UserProfile
2. ✅ Fact Sheet是否包含年龄信息
3. ✅ Fact Sheet是否包含家庭结构
4. ✅ Fact Sheet是否包含职业信息
5. ✅ Fact Sheet是否包含收入信息
6. ✅ Fact Sheet是否包含风险偏好

### 测试结果

```
============================================================================
【测试结果】
============================================================================

🎉 测试通过！(5/5)

✓ AI现在可以正确读取和使用用户画像信息了！
✓ 用户提供的年龄、家庭、职业、收入等信息都会被AI记住
```

---

## 📊 修复效果

### 修复前
- ❌ AI无法记住用户年龄
- ❌ AI无法记住家庭结构
- ❌ AI无法记住职业信息
- ❌ AI无法记住收入范围
- ❌ AI每次都像第一次见面

### 修复后
- ✅ AI能记住用户年龄段
- ✅ AI能记住家庭结构
- ✅ AI能记住职业信息
- ✅ AI能记住收入范围
- ✅ AI能提供个性化建议

### 用户体验改善

**修复前的对话**：
```
用户: 我35岁，已婚有孩子，是软件工程师
AI: 好的，了解了

用户: 我该怎么投资？
AI: 请问您的年龄和家庭情况是？  ← 完全忘记了！
```

**修复后的对话**：
```
用户: 我35岁，已婚有孩子，是软件工程师
AI: 好的，了解了

用户: 我该怎么投资？
AI: 根据您35岁、已婚有子女的情况，作为软件工程师...  ← 记住了！
```

---

## 🔄 相关修复

本次修复与之前的高优先级修复协同工作：

1. **UserProfile创建优化**（已完成）
   - 确保用户信息能正确保存到数据库

2. **Fact Sheet读取优化**（本次修复）
   - 确保AI能正确读取用户信息

3. **数据层分离**（已完成）
   - L1（UserProfile）存基本画像
   - L2（UserCognition）存心理分析

---

## 📁 修改的文件

- `backend/app/services/chat_agent.py` - 修复`_generate_fact_sheet()`方法
- `scripts/test_user_context_fix.py` - 测试脚本（新增）
- `scripts/diagnose_user_context.py` - 诊断脚本（新增）

---

## 🎯 后续优化建议

### 已完成 ✅
1. 读取UserProfile完整信息
2. 在Fact Sheet中展示用户画像
3. 添加财务目标展示

### 待优化
1. 添加用户画像变更历史追踪
2. 优化Fact Sheet格式（更易读）
3. 添加用户信息完整度评分

---

## 📚 相关文档

- [SQL数据结构分析](../SQL_DATA_STRUCTURE_ANALYSIS.md)
- [高优先级修复总结](HIGH_PRIORITY_SQL_FIXES_SUMMARY.md)
- [Fact Sheet快速参考](../Memory/FACT_SHEET_QUICK_REFERENCE.md)

---

**修复完成**：2026-01-14 23:50  
**测试通过率**：100% (5/5)  
**用户体验改善**：显著提升  
**问题状态**：✅ 已解决
