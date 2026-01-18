# Portfolio Analyzer Usage Guide

## Quick Start

The refactored portfolio analyzer provides intelligent asset classification and realistic financial recommendations based on the Standard & Poor's Four Quadrant Model.

## Asset Metadata Format

To get the most accurate analysis, include metadata in your `UserAsset.extra_data` field:

### Investment Assets

```python
# Low-risk investment (goes to PRESERVATION quadrant)
UserAsset(
    asset_type=AssetType.INVESTMENT,
    name="国债基金",
    value=100000,
    extra_data={
        "risk_level": "low",  # "low", "medium", or "high"
        "subtype": "bond"     # "bond", "money_fund", "stock", etc.
    }
)

# High-risk investment (goes to GROWTH quadrant)
UserAsset(
    asset_type=AssetType.INVESTMENT,
    name="股票基金",
    value=200000,
    extra_data={
        "risk_level": "high",
        "subtype": "stock"
    }
)
```

### Liability Assets

```python
# Liability with explicit monthly payment
UserAsset(
    asset_type=AssetType.LIABILITY,
    name="房贷",
    value=2000000,
    extra_data={
        "monthly_payment": 10000  # Explicit monthly payment
    }
)

# Liability without metadata (will estimate 0.5% per month)
UserAsset(
    asset_type=AssetType.LIABILITY,
    name="车贷",
    value=300000
    # Will estimate ~1500/month (300000 * 0.005)
)
```

## Classification Rules

### Investment Classification

| Condition | Quadrant | Reasoning |
|-----------|----------|-----------|
| `risk_level == "low"` | PRESERVATION | Low-risk, stable returns |
| `subtype in ["bond", "money_fund", "债券", "货币基金"]` | PRESERVATION | Conservative instruments |
| All other investments | GROWTH | Higher risk, growth potential |
| No metadata | GROWTH | Conservative default (assume risk) |

### Spending Money Calculation

**Old Logic** (Fixed Ratio):
```
Ideal Spending = Net Worth × 10%
```

**New Logic** (Expense-Based):
```
Ideal Spending = (Monthly Expense + Monthly Debt Payment) × 6 months
```

**Example**:
- Net Worth: 10,000,000 (10M property)
- Monthly Expense: 30,000
- Monthly Debt: 8,000
- **Old**: 1,000,000 (10% of net worth) ❌ Too much!
- **New**: 228,000 ((30k + 8k) × 6) ✅ Realistic!

## API Usage

```python
from app.services.portfolio_analyzer import portfolio_analyzer
from app.models.user import UserAsset, UserProfile, AssetType, RiskLevel

# Create assets with proper metadata
assets = [
    UserAsset(
        user_id=1,
        asset_type=AssetType.CASH,
        name="活期存款",
        value=100000
    ),
    UserAsset(
        user_id=1,
        asset_type=AssetType.INVESTMENT,
        name="债券基金",
        value=500000,
        extra_data={"risk_level": "low", "subtype": "bond"}
    ),
    UserAsset(
        user_id=1,
        asset_type=AssetType.LIABILITY,
        name="房贷",
        value=1500000,
        extra_data={"monthly_payment": 8000}
    )
]

# Create user profile
profile = UserProfile(
    user_id=1,
    age_range="30-40",
    family_structure="married_with_kids",
    risk_preference=RiskLevel.MODERATE,
    monthly_expense=20000
)

# Analyze portfolio
analysis = portfolio_analyzer.analyze_portfolio(assets, profile)

# Access results
print(f"Net Worth: {analysis.net_worth:,.0f}")
print(f"Spending Money: {analysis.quadrant_allocations[SPQuadrant.SPENDING_MONEY]:,.0f}")
print(f"Growth Money: {analysis.quadrant_allocations[SPQuadrant.GROWTH_MONEY]:,.0f}")

# Check recommendations
for rec in analysis.recommendations:
    print(f"{rec['title']}: {rec['description']}")
```

## Understanding the Output

### Quadrant Analysis Structure

```python
analysis.quadrant_analysis = {
    "quadrants": {
        "spending": {
            "name": "要花的钱",
            "current_amount": 100000,
            "ideal_amount": 168000,  # (20k expense + 8k debt) × 6
            "current_ratio": 0.05,
            "ideal_ratio": 0.084,
            "gap": 68000,
            "status": "insufficient"
        },
        # ... other quadrants
    },
    "priorities": [
        {
            "quadrant": "spending",
            "name": "要花的钱",
            "gap": 68000,
            "priority": "high",
            "action": "increase"
        }
    ],
    "summary": {
        "total_allocated": 2000000,
        "allocation_efficiency": 1.0,
        "major_gaps": 1,
        "overall_balance": "needs_rebalancing"
    }
}
```

## Best Practices

### 1. Always Provide Monthly Expense
```python
# Good
profile = UserProfile(
    monthly_expense=20000,  # Explicit value
    # ...
)

# Fallback (will estimate based on net worth)
profile = UserProfile(
    monthly_expense=None,  # Will estimate
    # ...
)
```

### 2. Include Risk Metadata for Investments
```python
# Good - Clear classification
extra_data={
    "risk_level": "low",
    "subtype": "bond"
}

# Acceptable - Will default to growth
extra_data={}  # or None
```

### 3. Specify Debt Payments When Known
```python
# Best - Accurate calculation
extra_data={"monthly_payment": 10000}

# Acceptable - Will estimate at 0.5%
extra_data={}
```

## Migration Guide

If you have existing code using the old analyzer:

### No Changes Required ✅
The refactored analyzer is **backward compatible**. Existing code will work without modification.

### To Get Enhanced Features
Add metadata to your assets:

```python
# Before (still works)
asset = UserAsset(
    asset_type=AssetType.INVESTMENT,
    name="基金",
    value=100000
)

# After (better classification)
asset = UserAsset(
    asset_type=AssetType.INVESTMENT,
    name="债券基金",
    value=100000,
    extra_data={"risk_level": "low", "subtype": "bond"}
)
```

## Common Scenarios

### Scenario 1: High Net Worth, Low Expenses
```python
# 10M property, 30k monthly expense
# Old: Recommended 1M cash (10%)
# New: Recommended 180k cash (6 months)
# Benefit: 820k freed for investment
```

### Scenario 2: Mortgage Holder
```python
# 15k expense + 10k mortgage
# Old: 90k emergency fund (6 × 15k)
# New: 150k emergency fund (6 × 25k)
# Benefit: Realistic buffer for all obligations
```

### Scenario 3: Mixed Investment Portfolio
```python
# 100k bonds + 200k stocks
# Old: Both classified as growth (300k growth)
# New: 100k preservation + 200k growth
# Benefit: Accurate risk assessment
```

## Troubleshooting

### Issue: Spending money recommendation seems too high
**Check**: Do you have liabilities? The calculation includes debt servicing.
```python
# If you have 2M mortgage with 10k monthly payment
# Spending = (expense + 10k) × 6
```

### Issue: Investment classified incorrectly
**Check**: Is the metadata properly formatted?
```python
# Correct
extra_data={"risk_level": "low"}  # lowercase

# Incorrect
extra_data={"risk_level": "Low"}  # Will still work (case-insensitive)
extra_data={"Risk_Level": "low"}  # Won't work (wrong key)
```

### Issue: Debt payment estimation seems off
**Solution**: Provide explicit monthly payment in metadata
```python
extra_data={"monthly_payment": 8000}  # Explicit value
```

## Testing

Run the test suite to verify functionality:

```bash
cd backend
python -m pytest tests/test_portfolio_analyzer_refactor.py -v
```

All tests should pass:
- ✅ Investment classification by risk level
- ✅ Spending money includes debt servicing
- ✅ Debt payment estimation without metadata
- ✅ Spending money dynamic calculation
- ✅ Full portfolio analysis integration

## Support

For questions or issues, refer to:
- `PORTFOLIO_ANALYZER_REFACTOR_SUMMARY.md` - Detailed technical changes
- `backend/app/services/portfolio_analyzer.py` - Source code with inline comments
- `backend/tests/test_portfolio_analyzer_refactor.py` - Test examples
