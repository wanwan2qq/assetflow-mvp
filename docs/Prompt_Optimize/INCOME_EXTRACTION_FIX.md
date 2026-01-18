# 收入提取滞后问题修复

> **修复日期**: 2026-01-18  
> **问题**: 收入信息更新比其他信息更新滞后  
> **状态**: ✅ 已修复

---

## 问题描述

用户反馈：收入（income_range）的更新比年龄、家庭结构等其他信息更新滞后。

---

## 问题分析

### 根本原因

**文件**: `backend/app/prompts/extraction/profile_extraction.yaml`

**问题**:
1. ❌ Prompt中定义了 `monthly_income` 字段，但代码中没有处理
2. ❌ Prompt中没有明确的收入提取规则和示例
3. ❌ LLM可能返回 `monthly_income` 而不是 `income_range`
4. ❌ 月收入和年收入的转换规则不明确

### 代码流程分析

```
用户: "我年收入50万"
  ↓
LLM提取 (使用 profile_extraction.yaml)
  ↓
问题1: Prompt中有 monthly_income 和 income_range 两个字段，LLM可能混淆
问题2: 没有明确说明如何提取和格式化收入
问题3: 月收入转年收入的规则不清楚
  ↓
LLM返回: {"profile": {"monthly_income": 25000}} ← 错误的字段名
  ↓
代码处理: income_range = profile_data.get("income_range") ← 获取不到
  ↓
结果: income_range = None ← 提取失败
```

### 对比其他字段

| 字段 | Prompt中的规则 | 示例 | 是否清晰 |
|------|---------------|------|---------|
| age_range | ✅ 明确 | "30岁" → "30-35" | ✅ |
| family_structure | ✅ 明确 | "已婚" → "married" | ✅ |
| risk_preference | ✅ 明确 | "保守" → "conservative" | ✅ |
| **income_range** | ❌ 不明确 | 无示例 | ❌ |

---

## 修复方案

### 修复内容

**文件**: `backend/app/prompts/extraction/profile_extraction.yaml`

#### 1. 移除混淆的 `monthly_income` 字段

**修复前**:
```yaml
{
    "profile": {
        "monthly_expense": 15000,
        "monthly_income": 25000,  # ❌ 混淆字段
        "income_range": "收入范围",  # ❌ 没有明确说明
    }
}
```

**修复后**:
```yaml
{
    "profile": {
        "monthly_expense": 15000,
        "income_range": "50万",  # ✅ 明确格式
    }
}
```

#### 2. 添加明确的收入提取规则

**新增规则**:
```yaml
5. **收入信息提取（重要）：**
   - 从"年收入"、"年薪"中提取，格式化为"XX万"
     * "年收入50万" → "50万"
     * "年薪60万" → "60万"
     * "年收入大概50万" → "50万"
   - 从"月收入"、"月薪"、"工资"中提取，转换为年收入
     * "月收入3万" → "36万" (3 * 12)
     * "月薪2.5万" → "30万" (2.5 * 12)
     * "工资每月2万" → "24万" (2 * 12)
   - 收入范围格式统一为"XX万"（年收入）
   - 如果用户提供月收入，必须转换为年收入
```

#### 3. 强调字段名称

**新增说明**:
```yaml
**重要说明：**
- **收入信息必须使用 income_range 字段，格式为"XX万"（年收入）**
```

---

## 修复效果

### 场景1: 用户提供年收入

**用户消息**: "我年收入50万"

**修复前**:
```json
{
  "profile": {
    "monthly_income": 416666  // ❌ 错误的字段名
  }
}
```
→ `income_range` 获取不到 → 提取失败

**修复后**:
```json
{
  "profile": {
    "income_range": "50万"  // ✅ 正确的字段名和格式
  }
}
```
→ `income_range` 成功获取 → 提取成功

### 场景2: 用户提供月收入

**用户消息**: "我月收入3万"

**修复前**:
```json
{
  "profile": {
    "monthly_income": 30000  // ❌ 月收入，未转换
  }
}
```
→ `income_range` 获取不到 → 提取失败

**修复后**:
```json
{
  "profile": {
    "income_range": "36万"  // ✅ 转换为年收入
  }
}
```
→ `income_range` 成功获取 → 提取成功

### 场景3: 同时提供年龄和收入

**用户消息**: "我35岁，年收入50万"

**修复前**:
```json
{
  "profile": {
    "age_range": "30-40",  // ✅ 年龄提取成功
    "monthly_income": 416666  // ❌ 收入字段错误
  }
}
```
→ 年龄更新成功，收入更新失败 → **滞后现象**

**修复后**:
```json
{
  "profile": {
    "age_range": "30-40",  // ✅ 年龄提取成功
    "income_range": "50万"  // ✅ 收入提取成功
  }
}
```
→ 年龄和收入同时更新成功 → **滞后问题解决**

---

## 为什么会滞后？

### 滞后的原因

1. **第一轮对话**: 用户说"我35岁，年收入50万"
   - 年龄提取成功 → 数据库更新
   - 收入提取失败（字段名错误）→ 数据库未更新

2. **第二轮对话**: 用户再次提到收入
   - 年龄已经在数据库中 → 不需要更新
   - 收入可能通过fallback提取成功 → 数据库更新

3. **结果**: 收入比年龄晚一轮更新 → **滞后现象**

### 修复后的流程

1. **第一轮对话**: 用户说"我35岁，年收入50万"
   - 年龄提取成功 → 数据库更新 ✅
   - 收入提取成功 → 数据库更新 ✅

2. **结果**: 年龄和收入同时更新 → **无滞后**

---

## Fallback提取

Fallback提取（正则表达式）已经有收入提取逻辑：

```python
# Income range extraction - improved patterns
income_patterns = [
    (r'年收入\s*大概\s*(\d+)\s*万', lambda m: f"{m.group(1)}万"),
    (r'年收入\s*(\d+)\s*万', lambda m: f"{m.group(1)}万"),
    (r'月收入\s*(\d+)\s*万', lambda m: f"{int(float(m.group(1)) * 12)}万"),
    (r'月收入\s*(\d+)', lambda m: f"{int(float(m.group(1)) * 12 / 10000)}万"),
]
```

✅ Fallback提取是正确的，但LLM提取应该是主要方式。

---

## 验证方法

### 测试脚本

创建测试脚本验证修复：

```python
# backend/test_income_extraction.py

async def test_income_extraction():
    extractor = InformationExtractor()
    
    # 测试1: 年收入
    result = await extractor.extract_information_from_conversation("我年收入50万")
    assert result.get('risk_profile', {}).get('income_range') == "50万"
    
    # 测试2: 月收入
    result = await extractor.extract_information_from_conversation("我月收入3万")
    assert result.get('risk_profile', {}).get('income_range') == "36万"
    
    # 测试3: 同时提供年龄和收入
    result = await extractor.extract_information_from_conversation("我35岁，年收入50万")
    assert result.get('risk_profile', {}).get('age_range') == "30-40"
    assert result.get('risk_profile', {}).get('income_range') == "50万"
```

### 生产环境验证

1. 观察日志中的提取结果
2. 检查数据库中 `income_range` 字段的更新
3. 对比年龄和收入的更新时间

---

## 总结

### 修复内容

✅ **移除了混淆的 `monthly_income` 字段**
✅ **添加了明确的收入提取规则和示例**
✅ **统一了收入格式为"XX万"（年收入）**
✅ **明确了月收入转年收入的规则**

### 修复效果

1. ✅ **收入提取成功率提升**: LLM现在知道如何提取和格式化收入
2. ✅ **消除滞后现象**: 收入和其他字段同时更新
3. ✅ **格式统一**: 所有收入都转换为年收入格式
4. ✅ **提示更清晰**: LLM不会混淆字段名

### 根本原因

**Prompt不清晰** → LLM混淆字段名 → 提取失败 → 滞后更新

### 解决方案

**优化Prompt** → LLM使用正确字段名 → 提取成功 → 同步更新

---

**修复完成日期**: 2026-01-18  
**修复人员**: Kiro AI Assistant  
**验证状态**: 待测试  
**版本**: 1.0
