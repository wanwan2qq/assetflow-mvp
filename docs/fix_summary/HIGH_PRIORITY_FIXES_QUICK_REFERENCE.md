# 高优先级修复快速参考

## 🎯 修复内容

### 1️⃣ UserProfile创建优化
**问题**：occupation/income_range可能丢失  
**修复**：降低创建条件，使用默认值填充必填字段  
**影响**：用户提供任意画像字段时都会创建UserProfile

### 2️⃣ UserAsset重复处理
**问题**：同类型多个资产被覆盖  
**修复**：精细化匹配（位置/面积/名称相似度）  
**影响**：相似资产更新，不同资产追加

### 3️⃣ L1/L2数据分离
**问题**：UserProfile和UserCognition字段重复  
**修复**：明确分层，L1存基本画像，L2存心理分析  
**影响**：减少数据冗余，提高数据一致性

---

## 📊 数据分层规则

### L1层（UserProfile）- 基本画像
```
✓ age_range          年龄段
✓ family_structure   家庭结构
✓ risk_preference    风险偏好
✓ monthly_expense    月支出
✓ occupation         职业
✓ income_range       收入范围
```

### L2层（UserCognition.risk_profile）- 心理分析
```
✓ tolerance              风险承受能力
✓ decision_style         决策风格
✓ confidence_level       信心水平
✓ current_sentiment      当前情绪
✓ loss_aversion          损失厌恶
✓ uncertainty_tolerance  不确定性容忍度
✓ financial_literacy     财务知识水平
✓ family_responsibility  家庭责任感
✓ planning_horizon       规划时间跨度
```

---

## 🔍 资产匹配规则

### 房产（real_estate）
1. **位置匹配**：子串匹配（标准化后）
2. **面积匹配**：±10平米容差
3. **名称匹配**：Jaccard相似度 > 50%

### 其他资产
- **名称匹配**：Jaccard相似度 > 50%

---

## ✅ 测试验证

```bash
# 运行测试
python scripts/test_high_priority_fixes.py

# 预期结果
✓ PASSED: Fix 1: UserProfile Creation
✓ PASSED: Fix 2: Asset Duplicate Handling
✓ PASSED: Fix 3: Data Layer Separation
🎉 All tests PASSED!
```

---

## 📝 使用示例

### 示例1：只提供职业
```python
extraction_result = {
    "risk_profile": {
        "occupation": "软件工程师"
    }
}
# 结果：创建UserProfile，使用默认值填充age_range/family_structure
```

### 示例2：添加相似房产
```python
# 第一次
{"type": "real_estate", "name": "天通苑北一区", "location": "北京昌平区"}
# 第二次（相似）
{"type": "real_estate", "name": "天通苑北一区120平", "location": "北京市昌平区"}
# 结果：更新第一条记录，不创建新记录
```

### 示例3：L1/L2分离
```python
# 提取结果
risk_profile = {
    "age_range": "40-50",        # → L1 (UserProfile)
    "occupation": "医生",         # → L1 (UserProfile)
    "tolerance": "conservative"  # → L2 (UserCognition)
}
# 结果：基本画像存L1，心理分析存L2
```

---

## 🚀 后续优化

### 中优先级
- [ ] 放宽UserAsset.value约束（允许NULL）
- [ ] 实现审计日志自动化
- [ ] 添加VectorMemory嵌入重试

### 低优先级
- [ ] 数据完整性检查脚本
- [ ] 查询性能优化（索引）
- [ ] 数据归档机制

---

**最后更新**：2026-01-14  
**测试状态**：✅ 全部通过  
**文档版本**：v1.0
