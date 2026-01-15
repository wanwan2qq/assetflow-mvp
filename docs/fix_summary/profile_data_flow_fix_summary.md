# User Profile Data Flow Fix Summary

**Date:** January 14, 2026  
**Issue:** Profile fields (occupation, income_range) were being extracted but not stored in the database

## Problem Analysis

The user profile data flow had two critical issues:

1. **Extraction Issue:** `information_extraction.py` was extracting occupation and income_range from user messages, but these fields were already being included in the `risk_profile` dict (no issue found here after review)

2. **Storage Issue:** `asset_extraction_service.py` was missing logic to store occupation and income_range fields in the database:
   - The `_update_user_profile_from_extraction` method didn't handle these fields
   - The `UserProfile` model didn't have columns for occupation and income_range

## Solution Implemented

### 1. Database Schema Update

Added two new columns to the `UserProfile` table:

```python
# backend/app/models/user.py
class UserProfile(SQLModel, table=True):
    # ... existing fields ...
    occupation: str | None = Field(default=None, max_length=100)
    income_range: str | None = Field(default=None, max_length=50)
```

**Migration:** `backend/alembic/versions/add_occupation_income_to_user_profile.py`

### 2. Service Layer Update

Updated `asset_extraction_service.py` to store occupation and income_range:

```python
async def _update_user_profile_from_extraction(self, user_id: int, risk_profile: dict, session: Session):
    """Update UserProfile with occupation and income_range"""
    
    # When creating new profile
    if not profile:
        if age_range and family_structure and risk_preference:
            profile = UserProfile(
                user_id=user_id,
                age_range=age_range,
                family_structure=family_structure,
                risk_preference=risk_preference,
                monthly_expense=risk_profile.get("monthly_expense"),
                occupation=risk_profile.get("occupation"),  # NEW
                income_range=risk_profile.get("income_range")  # NEW
            )
    
    # When updating existing profile
    else:
        if risk_profile.get("occupation"):
            profile.occupation = risk_profile["occupation"]
        
        if risk_profile.get("income_range"):
            profile.income_range = risk_profile["income_range"]
```

### 3. Data Storage Strategy

The fix implements a dual-storage strategy:

**UserCognition.risk_profile (JSON):**
- Always stores occupation and income_range
- Used for flexible data storage and AI context
- No schema constraints

**UserProfile (Structured Table):**
- Stores occupation and income_range when ALL required fields are present
- Required fields: age_range, family_structure, risk_preference
- Used for structured queries and data integrity

## Testing

Created comprehensive test scripts:

### Test 1: Partial Profile
**Script:** `scripts/test_profile_data_flow.py`

```python
# Test message with only occupation and income
test_message = "我是一名软件工程师，年收入大概在30-50万之间，每月支出约1万元"

# Result:
# ✅ Extraction: occupation='软件工程师', income_range='30-50万'
# ✅ Storage: Stored in UserCognition.risk_profile
# ⚠️  UserProfile not created (missing required fields)
```

### Test 2: Complete Profile
**Script:** `scripts/test_profile_complete_flow.py`

```python
# Test message with complete profile
test_message = "我今年35岁，已婚有孩子，是一名软件工程师，年收入30-50万，每月支出1万元，投资偏好稳健"

# Result:
# ✅ Extraction: All fields extracted
# ✅ Storage: Stored in both UserCognition.risk_profile AND UserProfile table
```

## Verification

Run the tests to verify the fix:

```bash
# Test partial profile (occupation/income only)
python scripts/test_profile_data_flow.py

# Test complete profile (all fields)
python scripts/test_profile_complete_flow.py
```

Both tests should pass with output:
```
✅ ALL TESTS PASSED!
🎉 User Profile data flow is working correctly!
```

## Data Flow Diagram

```
User Message
    ↓
[LLM Extraction] (information_extraction.py)
    ↓
extraction_result = {
    "risk_profile": {
        "occupation": "软件工程师",
        "income_range": "30-50万",
        "monthly_expense": 10000.0,
        ...
    }
}
    ↓
[Service Layer] (asset_extraction_service.py)
    ↓
    ├─→ UserCognition.risk_profile (JSON) ✅ Always stored
    │   └─ Flexible storage for AI context
    │
    └─→ UserProfile (Table) ✅ Stored if required fields present
        └─ Structured storage for queries
```

## Files Modified

1. **backend/app/models/user.py**
   - Added `occupation` and `income_range` fields to `UserProfile` model

2. **backend/app/services/asset_extraction_service.py**
   - Updated `_update_user_profile_from_extraction` to handle new fields
   - Added logging for occupation and income_range updates

3. **backend/alembic/versions/add_occupation_income_to_user_profile.py**
   - New migration to add columns to database

## Impact

- ✅ Occupation and income_range are now properly stored
- ✅ Data persists across sessions
- ✅ Available for AI context and user profile queries
- ✅ Backward compatible (existing profiles not affected)
- ✅ Graceful handling of partial vs complete profiles

## Next Steps

1. Update API endpoints to return occupation and income_range
2. Update frontend to display these fields
3. Add validation for income_range format
4. Consider adding more profile fields (education, industry, etc.)

## Related Documents

- [Profile Extraction Fix](./profile_extraction_data_loss_fix.md)
- [LLM Extraction Refactor](../Memory/LLM_EXTRACTION_REFACTOR_SUMMARY.md)
- [Phase 2 Implementation](../Memory/PHASE2_IMPLEMENTATION_SUMMARY.md)
