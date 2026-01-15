# Profile Extraction Fix - Quick Reference

## Problem
User profile fields (`occupation`, `income_range`, `monthly_expense`) were extracted by LLM but discarded before storage.

## Solution
✅ Fixed `extract_information()` to include all profile fields in result  
✅ Enhanced `update_user_state()` to store all fields in `UserCognition.risk_profile`  
✅ Added sync to `UserProfile` table for compatible fields

## Data Storage

### UserCognition.risk_profile (JSON)
Stores **ALL** profile data:
```json
{
  "tolerance": "moderate",
  "age_range": "30-40",
  "family_structure": "married_with_kids",
  "monthly_expense": 50000,
  "occupation": "软件工程师",
  "income_range": "50000"
}
```

### UserProfile table
Stores **schema-defined** fields only:
- `age_range`
- `family_structure`
- `risk_preference`
- `monthly_expense`

Note: `occupation` and `income_range` are NOT in UserProfile schema, only in UserCognition.

## Testing

```bash
cd backend
python ../scripts/test_profile_extraction_fix.py
```

Expected: ✅ SUCCESS: Both occupation and income_range are properly stored!

## Files Changed
- `backend/app/services/information_extraction.py` - Added field mappings
- `backend/app/services/asset_extraction_service.py` - Enhanced storage logic

## Verification
```python
# Check if data is stored
from app.models.cognition import UserCognition

cognition = session.query(UserCognition).filter_by(user_id=user_id).first()
print(cognition.risk_profile)
# Should show: {'occupation': '...', 'income_range': '...', ...}
```
