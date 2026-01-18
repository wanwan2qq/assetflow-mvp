# SP Quadrant Integration - Quick Reference

## 🎯 What Was Done

Updated 3 services to support Standard & Poor's 4-Quadrant Model with metadata extraction:

1. **Extraction** - Extract `subtype`, `risk_level`, `monthly_payment`
2. **Recommendation** - Map SP risk types to product categories
3. **Chat Context** - Display metadata in fact sheet

## 📋 Quick Test

```bash
cd backend

# Run validation script
python scripts/validate_sp_quadrant_integration.py

# Or test with demo
python scripts/demo_portfolio_analyzer_refactor.py
```

## 🔍 Key Changes

### 1. Extraction Prompt (`information_extraction.yaml`)

**New Metadata Fields:**
```yaml
metadata:
  subtype: "stock|bond|fund|crypto|property_fund|fixed_deposit|money_market"
  risk_level: "low|medium|high"
  monthly_payment: 5000  # For liabilities
```

**Example Extraction:**
```
Input: "我有 50 万国债"
Output: {
  "type": "investment",
  "name": "国债",
  "value": 500000,
  "metadata": {
    "subtype": "bond",
    "risk_level": "low"
  }
}
```

### 2. Recommendation Mapping (`recommendation_service.py`)

**New SP Risk Types:**
```python
"sp_spending_insufficient" → "investment"      # 要花的钱
"sp_life_insufficient" → "insurance"           # 保命的钱
"sp_growth_insufficient" → "broker"            # 生钱的钱
"sp_preservation_insufficient" → "investment"  # 保本升值的钱
```

### 3. Fact Sheet Display (`chat_agent.py`)

**Before:**
```
1. [投资] 国债 | 价值: 50万 (用户已确认)
```

**After:**
```
1. [投资] 国债 | 类型: 债券 | 风险: 低风险 | 价值: 50万 (用户已确认)
```

## 🧪 Test Cases

### Investment with Subtype
```python
Input: "我有 50 万国债"
Expected:
  - type: "investment"
  - subtype: "bond"
  - risk_level: "low"
  - value: 500000
```

### Liability with Monthly Payment
```python
Input: "房贷 200 万，月供 8000"
Expected:
  - type: "liability"
  - value: 2000000
  - monthly_payment: 8000
```

### Fact Sheet Display
```python
Expected Output:
  "1. [投资] 国债 | 类型: 债券 | 风险: 低风险 | 价值: 50万 (用户已确认)"
  "2. [负债] 房贷 | 金额: 200万 | 月供: 8000元 (用户已确认)"
```

## 📊 Data Flow

```
User: "我有 50 万国债"
    ↓
[Extraction] → Extract: subtype="bond", risk_level="low"
    ↓
[Storage] → Store in asset.metadata
    ↓
[Portfolio Analyzer] → Classify as "Preservation Money"
    ↓
[Fact Sheet] → Display: "类型: 债券 | 风险: 低风险"
    ↓
[Recommendation] → Map SP risks to products
```

## 🔧 Files Modified

1. `backend/app/prompts/extraction/information_extraction.yaml`
2. `backend/app/services/recommendation_service.py`
3. `backend/app/services/chat_agent.py`

## ✅ Validation Checklist

- [ ] Extraction extracts subtype for investments
- [ ] Extraction extracts risk_level for investments
- [ ] Extraction extracts monthly_payment for liabilities
- [ ] Fact sheet displays subtype in Chinese
- [ ] Fact sheet displays risk_level in Chinese
- [ ] Fact sheet displays monthly_payment for liabilities
- [ ] Portfolio analyzer uses metadata for classification
- [ ] Recommendation service maps SP risk types correctly

## 🚀 Next Steps

1. Run validation script to verify integration
2. Test with real user conversations
3. Monitor extraction accuracy in logs
4. Adjust extraction prompt if needed

## 📚 Related Documentation

- `backend/SP_QUADRANT_INTEGRATION_COMPLETE.md` - Full documentation
- `backend/PORTFOLIO_ANALYZER_QUICK_REFERENCE.md` - Analyzer reference
- `backend/PORTFOLIO_ANALYZER_USAGE_GUIDE.md` - Usage guide
