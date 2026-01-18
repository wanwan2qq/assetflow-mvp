# YAML Prompt Refinement - Quick Reference

**Last Updated**: 2026-01-16  
**Status**: ✅ Complete

---

## 🎯 What Changed?

### 1. Agent System (`agent_system.yaml`)

**OLD** ❌:
```
"现金占比应该达到10%"
"保险占比太低了"
"标准普尔建议现金10%、保险20%..."
```

**NEW** ✅:
```
"您的现金储备可以覆盖X个月开销"
"根据您的家庭情况，建议保额达到X万"
"分析显示您的生钱的钱欠配了Y%"
```

**Key Principle**: Trust `[Portfolio Analysis]` data, not fixed percentages!

---

### 2. Information Extraction (`information_extraction.yaml`)

**Critical Mappings**:

| Asset Type | Subtype | Risk Level | Quadrant |
|------------|---------|------------|----------|
| 余额宝/货币基金 | `money_fund` | `low` | Preservation |
| 银行理财 | `bank_product` | `low` | Preservation |
| 股票基金 | `equity_fund` | `high` | Growth |
| 国债/债券 | `bond` | `low` | Preservation |

**Monthly Payment Extraction**:
```
"房贷月供5000" → metadata: { "monthly_payment": 5000 }
```

---

### 3. Memory Extraction (`memory_extraction.yaml`)

**New Field**: `timeline`

```json
{
  "content": "用户计划3年内购买学区房，预算500万",
  "category": "major_purchase",
  "tags": ["real_estate", "planning", "education"],
  "timeline": "3年内"  // NEW!
}
```

---

### 4. Psychology Analysis (`psychology_analysis.yaml`)

**New Field**: `liquidity_anxiety`

```json
{
  "psychological_traits": {
    "liquidity_anxiety": "high|medium|low"  // NEW!
  }
}
```

**Detection Keywords**:
- 手头紧
- 没钱花
- 转不开
- 现金流压力
- 资金周转困难

---

## 🧪 How to Validate

```bash
cd backend
python scripts/validate_prompt_refinement.py
```

Expected output:
```
✅ PASSED: Task 1 (agent_system.yaml)
✅ PASSED: Task 2 (information_extraction.yaml)
✅ PASSED: Task 3 (memory_extraction.yaml)
✅ PASSED: Task 4 (psychology_analysis.yaml)

🎉 All validation tests PASSED!
```

---

## 🔍 Key Concepts

### Dynamic Coverage Model

**Spending Money** = 3-6 months expense + total monthly debt payments

- ✅ Check `liquidity_months` field
- ✅ High net worth users may have 2-5% cash (normal!)
- ❌ Don't enforce 10% fixed percentage

### Asset Classification

**Preservation Money** (Low Risk):
- 货币基金 (money_fund)
- 银行理财 (bank_product)
- 债券 (bond)

**Growth Money** (High Risk):
- 股票 (stock)
- 股票基金 (equity_fund)
- 加密货币 (crypto)

### Liquidity Anxiety

**High Net Worth + Low Cash Flow** = Liquidity Anxiety

Example: User has 5M in real estate but only 50K cash and 10K/month mortgage payment.

---

## 📊 Before vs After

| Aspect | Before | After |
|--------|--------|-------|
| Cash Percentage | Fixed 10% | Dynamic (3-6 months) |
| Asset Subtypes | Generic "fund" | Specific "money_fund" vs "equity_fund" |
| Timeline Tracking | ❌ None | ✅ Extracted |
| Liquidity Anxiety | ❌ Not detected | ✅ Detected |

---

## 🚨 Common Pitfalls to Avoid

1. **Don't** say "现金占比太低" → Say "现金储备可以覆盖X个月"
2. **Don't** enforce fixed percentages → Trust `allocation_gaps` data
3. **Don't** classify 货币基金 as high risk → It's low risk (Preservation)
4. **Don't** ignore monthly payments → Critical for Spending Money calculation

---

## 📚 Related Files

- `backend/app/services/portfolio_analyzer.py` - Dynamic threshold logic
- `backend/app/services/chat_agent.py` - Uses agent_system.yaml
- `backend/app/services/information_extraction.py` - Uses information_extraction.yaml
- `backend/app/services/insight_service.py` - Uses psychology_analysis.yaml

---

**Quick Check**: If AI says "现金占比应该达到10%", the refinement failed. It should say "现金储备可以覆盖X个月开销".
