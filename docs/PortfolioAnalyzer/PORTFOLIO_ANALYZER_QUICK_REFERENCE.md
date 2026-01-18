# Portfolio Analyzer Refactor - Quick Reference

## 🎯 What Changed?

### 1. Investment Classification (Risk-Based) ✅
**Before**: All investments → Growth Money (high risk)
**After**: Checks `extra_data` for risk level

```python
# Low-risk → PRESERVATION
extra_data={"risk_level": "low"}
extra_data={"subtype": "bond"}
extra_data={"subtype": "money_fund"}

# High-risk → GROWTH
extra_data={"risk_level": "high"}
extra_data={"subtype": "stock"}
# or no metadata (default)
```

### 2. Spending Money Calculation (Expense-Based) ✅
**Before**: Fixed 10% of net worth
**After**: Dynamic based on actual needs

```python
# Old Formula
ideal_spending = net_worth × 0.10

# New Formula
ideal_spending = (monthly_expense + monthly_debt) × 6
```

**Example Impact**:
- 10M net worth, 30k expense
- Old: 1M cash (inefficient)
- New: 180k cash (realistic)
- **Saves**: 820k for investment!

### 3. Debt Servicing (Included) ✅
**Before**: Ignored debt payments
**After**: Includes mortgage/loan payments

```python
# Liability with explicit payment
extra_data={"monthly_payment": 10000}

# Without metadata (estimates 0.5%)
# 2M mortgage → ~10k/month estimated
```

## 📊 Quick Examples

### Example 1: Bond Fund
```python
UserAsset(
    asset_type=AssetType.INVESTMENT,
    name="国债基金",
    value=100000,
    extra_data={"risk_level": "low", "subtype": "bond"}
)
# Result: Goes to PRESERVATION (not GROWTH) ✅
```

### Example 2: High Net Worth
```python
# Assets: 10M property + 500k cash
# Monthly expense: 30k
# Old recommendation: 1M cash (10%)
# New recommendation: 180k cash (6 months)
# Benefit: 820k freed for investment ✅
```

### Example 3: Mortgage Holder
```python
# Monthly expense: 15k
# Monthly mortgage: 10k
# Old emergency fund: 90k (6 × 15k)
# New emergency fund: 150k (6 × 25k)
# Benefit: Covers all obligations ✅
```

## 🔧 How to Use

### Basic Usage (No Changes Required)
```python
from app.services.portfolio_analyzer import portfolio_analyzer

analysis = portfolio_analyzer.analyze_portfolio(assets, profile)
# Works exactly as before ✅
```

### Enhanced Usage (Add Metadata)
```python
# For investments
asset = UserAsset(
    asset_type=AssetType.INVESTMENT,
    name="债券基金",
    value=100000,
    extra_data={
        "risk_level": "low",  # "low", "medium", "high"
        "subtype": "bond"     # "bond", "stock", "money_fund"
    }
)

# For liabilities
liability = UserAsset(
    asset_type=AssetType.LIABILITY,
    name="房贷",
    value=2000000,
    extra_data={
        "monthly_payment": 10000  # Explicit payment
    }
)
```

## ✅ Testing

### Run Tests
```bash
cd backend
python -m pytest tests/test_portfolio_analyzer_refactor.py -v
```

### Run Demo
```bash
cd backend
python scripts/demo_portfolio_analyzer_refactor.py
```

## 📈 Impact Summary

| Improvement | Before | After | Benefit |
|-------------|--------|-------|---------|
| **Investment Classification** | All → Growth | Risk-based | Accurate risk assessment |
| **Spending Calculation** | 10% of net worth | 6 months expenses | Efficient allocation |
| **Debt Consideration** | Ignored | Included | Realistic liquidity |

## 🚀 Key Benefits

1. **More Accurate**: Risk-based classification reflects reality
2. **More Efficient**: Spending based on needs, not arbitrary %
3. **More Realistic**: Includes debt obligations in planning
4. **Backward Compatible**: Existing code works without changes
5. **Well Tested**: 9/9 tests pass (4 existing + 5 new)

## 📚 Documentation

- **Summary**: `PORTFOLIO_ANALYZER_REFACTOR_SUMMARY.md`
- **Usage Guide**: `PORTFOLIO_ANALYZER_USAGE_GUIDE.md`
- **Tests**: `tests/test_portfolio_analyzer_refactor.py`
- **Demo**: `scripts/demo_portfolio_analyzer_refactor.py`
- **Source**: `app/services/portfolio_analyzer.py`

## 🎯 Quick Decision Tree

### Should I add metadata?

```
Do you have investment assets?
├─ Yes → Add risk_level and subtype
│         for accurate classification
└─ No → No action needed

Do you have liabilities?
├─ Yes → Add monthly_payment if known
│         for accurate liquidity planning
└─ No → No action needed

Do you know monthly expenses?
├─ Yes → Set in UserProfile.monthly_expense
│         for accurate spending calculation
└─ No → Will estimate based on net worth
```

## 💡 Pro Tips

1. **Always provide monthly_expense** in UserProfile for best results
2. **Add risk_level** to investments for accurate classification
3. **Include monthly_payment** for liabilities when known
4. **Use Chinese or English** field names (both supported)
5. **Test with demo script** to see improvements in action

## 🔍 Troubleshooting

**Q: My bond fund is classified as growth money**
A: Add `extra_data={"risk_level": "low"}` or `{"subtype": "bond"}`

**Q: Spending recommendation seems too high**
A: Check if you have liabilities - debt payments are included

**Q: Debt payment estimation seems off**
A: Provide explicit `monthly_payment` in liability metadata

**Q: Will this break my existing code?**
A: No! It's backward compatible. All existing tests pass.

---

**Last Updated**: January 2026
**Version**: 2.0 (Refactored)
**Status**: ✅ Production Ready
