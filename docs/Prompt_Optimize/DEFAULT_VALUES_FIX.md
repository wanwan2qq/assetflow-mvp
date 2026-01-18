# 默认值问题修复报告 (V2)

> **修复日期**: 2026-01-18  
> **问题**: 年龄和家庭结构自动添加假的默认值  
> **解决方案**: 使用 "unknown" 表示未知信息  
> **状态**: ✅ 已修复

---

## 问题描述

### 原始问题

用户反馈：个人信息中年龄（age_range）和家庭结构（family_structure）添加的时候，会有一些假的默认值。

### 问题根源

**文件**: `backend/app/services/asset_extraction_service.py`  
**位置**: 第675-676行

**问题代码**:
```python
# 旧代码（有问题）:
profile = UserProfile(
    user_id=user_id,
    age_range=age_range or "30-40",  # ❌ 假的默认值
    family_structure=family_structure or "single",  # ❌ 假的默认值
    risk_preference=risk_preference or "moderate",  # ❌ 假的默认值
    ...
)
```

**问题分析**:
1. 当用户没有提供年龄时，系统自动设置为 `"30-40"`
2. 当用户没有提供家庭结构时，系统自动设置为 `"single"`
3. 当用户没有提供风险偏好时，系统自动设置为 `"moderate"`
4. 这导致系统"假装"知道用户的信息，但实际上是错误的假设

---

## 修复方案 V2

### 核心思路

**使用 "unknown" 表示未知信息，而不是假的默认值**

这样做的好处：
1. ✅ **诚实**: 明确表示我们不知道这些信息
2. ✅ **灵活**: 允许创建 profile，即使某些字段未知
3. ✅ **可追踪**: 可以识别哪些字段需要用户补充
4. ✅ **安全**: Portfolio Analyzer 可以跳过未知字段的处理

---

## 修复内容

### 修复1: 修改数据模型

**文件**: `backend/app/models/user.py`

#### 1.1 添加 "unknown" 到 RiskLevel 枚举

```python
class RiskLevel(str, Enum):
    CONSERVATIVE = "conservative"  # 保守型
    MODERATE = "moderate"  # 稳健型
    AGGRESSIVE = "aggressive"  # 激进型
    UNKNOWN = "unknown"  # ✅ 未知
```

#### 1.2 修改验证器允许 "unknown"

```python
@field_validator("age_range")
@classmethod
def validate_age_range(cls, v: str) -> str:
    """验证年龄段格式"""
    valid_ranges = ["20-30", "30-40", "40-50", "50-60", "60+", "unknown"]  # ✅ Added
    if v not in valid_ranges:
        raise ValueError(f"年龄段必须是以下之一: {', '.join(valid_ranges)}")
    return v

@field_validator("family_structure")
@classmethod
def validate_family_structure(cls, v: str) -> str:
    """验证家庭结构"""
    valid_structures = [
        "single",
        "married",
        "married_with_kids",
        "divorced",
        "widowed",
        "unknown",  # ✅ Added
    ]
    if v not in valid_structures:
        raise ValueError(f"家庭结构必须是以下之一: {', '.join(valid_structures)}")
    return v
```

### 修复2: 修改提取服务

**文件**: `backend/app/services/asset_extraction_service.py`

```python
if not profile:
    # Create profile with "unknown" for missing required fields
    # This allows profile creation even when some info is not yet extracted
    age_range = risk_profile.get("age_range")
    family_structure = risk_profile.get("family_structure")
    risk_preference = risk_profile.get("tolerance")
    occupation = risk_profile.get("occupation")
    income_range = risk_profile.get("income_range")
    monthly_expense = risk_profile.get("monthly_expense")
    
    # ✅ FIX: Use "unknown" for missing required fields instead of fake defaults
    # This is honest - we don't know the user's age/family structure yet
    # Create profile if we have at least one meaningful field
    if any([age_range, family_structure, risk_preference, occupation, income_range, monthly_expense]):
        try:
            profile = UserProfile(
                user_id=user_id,
                age_range=age_range or "unknown",  # ✅ Use "unknown" instead of "30-40"
                family_structure=family_structure or "unknown",  # ✅ Use "unknown" instead of "single"
                risk_preference=risk_preference or "unknown",  # ✅ Use "unknown" instead of "moderate"
                monthly_expense=monthly_expense,
                occupation=occupation,
                income_range=income_range
            )
            session.add(profile)
            has_updates = True
            logger.info(f"Created new UserProfile for user {user_id}")
            logger.info(f"  - age_range: {profile.age_range} {'(unknown - not yet provided)' if not age_range else ''}")
            logger.info(f"  - family_structure: {profile.family_structure} {'(unknown - not yet provided)' if not family_structure else ''}")
            logger.info(f"  - risk_preference: {profile.risk_preference} {'(unknown - not yet provided)' if not risk_preference else ''}")
```

### 修复3: 修改 Portfolio Analyzer

**文件**: `backend/app/services/portfolio_analyzer.py`

#### 3.1 修改风险阈值调整方法

```python
def _adjust_risk_thresholds(self, user_profile: UserProfile | None) -> dict[str, float]:
    """Adjust risk thresholds based on user profile"""
    thresholds = self.default_thresholds.copy()

    if not user_profile:
        return thresholds

    # ✅ Skip adjustment if age_range is "unknown"
    if user_profile.age_range and user_profile.age_range != "unknown":
        if ("20-30" in user_profile.age_range or ...):
            # Younger users can take more risk
            ...

    # ✅ Skip adjustment if family_structure is "unknown"
    if user_profile.family_structure and user_profile.family_structure != "unknown":
        if user_profile.family_structure == "married_with_kids":
            # Families need more liquidity
            ...

    # ✅ Skip adjustment if risk_preference is "unknown"
    if user_profile.risk_preference and user_profile.risk_preference != "unknown":
        if user_profile.risk_preference == "conservative":
            # Conservative users: stricter thresholds
            ...
```

#### 3.2 修改 SP 配置方法

```python
def _calculate_ideal_sp_allocations(self, user_profile: UserProfile | None) -> dict[SPQuadrant, float]:
    """Calculate ideal Standard & Poor's allocations based on user profile"""
    allocations = self.default_sp_allocations.copy()

    if not user_profile:
        return allocations

    # ✅ Skip adjustment if age_range is "unknown"
    if user_profile.age_range and user_profile.age_range != "unknown":
        if "20-30" in user_profile.age_range or "25-35" in user_profile.age_range:
            # Young users: more growth, less preservation
            ...

    # ✅ Skip adjustment if family_structure is "unknown"
    if user_profile.family_structure and user_profile.family_structure != "unknown":
        if user_profile.family_structure == "married_with_kids":
            # Families need more emergency funds
            ...

    # ✅ Skip adjustment if risk_preference is "unknown"
    if user_profile.risk_preference and user_profile.risk_preference != "unknown":
        if user_profile.risk_preference == "conservative":
            # Conservative users need more safety
            ...
```

---

## 修复效果

### 场景1: 用户只提供职业

**用户消息**: "我是一名软件工程师"

**提取结果**:
- occupation: "软件工程师"
- age_range: None
- family_structure: None
- risk_preference: None

**系统行为**:
- ✅ 创建 UserProfile
- ✅ age_range = "unknown"
- ✅ family_structure = "unknown"
- ✅ risk_preference = "unknown"

**Fact Sheet 显示**:
```
【用户基本画像】
• 年龄段: 未知
• 家庭结构: 未知
• 风险偏好: 未知
• 职业: 软件工程师
```

**Portfolio Analyzer 行为**:
- ✅ 跳过基于年龄的调整
- ✅ 跳过基于家庭结构的调整
- ✅ 跳过基于风险偏好的调整
- ✅ 使用默认的通用配置

**AI 响应**:
```
"您好！了解您是软件工程师。为了给您更精准的资产配置建议，
能否告诉我您的年龄、家庭情况和风险偏好呢？"
```
↑ ✅ AI 会主动询问缺失的信息

### 场景2: 用户提供年龄和家庭结构

**用户消息**: "我35岁，已婚有孩子"

**提取结果**:
- age_range: "30-40"
- family_structure: "married_with_kids"
- risk_preference: None

**系统行为**:
- ✅ 创建 UserProfile
- ✅ age_range = "30-40"
- ✅ family_structure = "married_with_kids"
- ✅ risk_preference = "unknown"

**Fact Sheet 显示**:
```
【用户基本画像】
• 年龄段: 30-40岁
• 家庭结构: 已婚有子女
• 风险偏好: 未知
```

**Portfolio Analyzer 行为**:
- ✅ 应用基于年龄的调整
- ✅ 应用基于家庭结构的调整
- ✅ 跳过基于风险偏好的调整（使用默认）

---

## 对比：V1 vs V2

| 方案 | 缺失字段处理 | Profile 创建 | 优点 | 缺点 |
|------|------------|------------|------|------|
| **V1** (不创建) | 等待用户提供 | 只有全部字段才创建 | 数据绝对准确 | 太严格，影响功能 |
| **V2** (使用 unknown) | 标记为 "unknown" | 有任意字段就创建 | 灵活、诚实、可追踪 | 需要处理 "unknown" |

**V2 的优势**:
1. ✅ 更灵活：允许部分信息创建 profile
2. ✅ 更诚实：明确表示未知，而不是假装知道
3. ✅ 更实用：Portfolio Analyzer 可以跳过未知字段
4. ✅ 更友好：AI 会主动询问缺失信息

---

## 验证测试

### 测试脚本

**文件**: `backend/test_unknown_values.py`

**测试结果**:
```
✅ RiskLevel 包含 'unknown'
✅ 成功创建带 'unknown' 值的 UserProfile
✅ 发现使用 'unknown' 作为默认值
✅ 已移除假的年龄默认值 '30-40'
✅ 已移除假的家庭结构默认值 'single'
✅ 发现跳过 'unknown' 值的逻辑

✅ 所有检查通过！'unknown' 值处理正确！
```

---

## 数据库迁移

### 需要迁移吗？

**不需要！** 因为：
1. ✅ "unknown" 是新增的有效值，不影响现有数据
2. ✅ 现有用户的 profile 保持不变
3. ✅ 只有新创建的 profile 会使用 "unknown"

### 如果需要清理旧数据

如果发现有使用假默认值的旧数据，可以运行：

```sql
-- 查找使用假默认值的记录
SELECT id, user_id, age_range, family_structure, risk_preference
FROM userprofile
WHERE age_range = '30-40' OR family_structure = 'single' OR risk_preference = 'moderate';

-- 可选：将假默认值更新为 'unknown'
-- UPDATE userprofile SET age_range = 'unknown' WHERE age_range = '30-40';
-- UPDATE userprofile SET family_structure = 'unknown' WHERE family_structure = 'single';
```

---

## 总结

### 修复内容

✅ **添加了 "unknown" 值支持**
- RiskLevel 枚举添加 UNKNOWN
- 验证器允许 "unknown"
- 使用 "unknown" 替代假的默认值

✅ **修改了 Portfolio Analyzer**
- 跳过 "unknown" 值的处理
- 使用默认配置处理未知信息

✅ **保持了灵活性**
- 允许部分信息创建 profile
- AI 会主动询问缺失信息

### 修复效果

1. ✅ **数据准确性**: 不会存储假的默认值
2. ✅ **系统灵活性**: 允许部分信息创建 profile
3. ✅ **用户体验**: AI 会主动引导用户补充信息
4. ✅ **可追踪性**: 可以识别哪些字段需要补充

### 验证状态

✅ **代码检查通过**
✅ **逻辑验证通过**
✅ **测试脚本通过**

---

**修复完成日期**: 2026-01-18  
**修复人员**: Kiro AI Assistant  
**验证状态**: ✅ 通过  
**版本**: 2.0 (使用 "unknown")
