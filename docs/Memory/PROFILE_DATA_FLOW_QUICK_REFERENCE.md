# User Profile Data Flow - Quick Reference

## Overview
Fixed the broken data flow for occupation and income_range fields from extraction to database storage.

## Key Changes

### 1. Database Schema
```sql
-- New columns in userprofile table
ALTER TABLE userprofile ADD COLUMN occupation VARCHAR(100);
ALTER TABLE userprofile ADD COLUMN income_range VARCHAR(50);
```

### 2. Data Storage Locations

| Field | UserCognition.risk_profile | UserProfile Table |
|-------|---------------------------|-------------------|
| occupation | ✅ Always | ✅ If complete profile |
| income_range | ✅ Always | ✅ If complete profile |
| monthly_expense | ✅ Always | ✅ If complete profile |
| age_range | ✅ Always | ✅ Required field |
| family_structure | ✅ Always | ✅ Required field |
| risk_preference | ✅ Always | ✅ Required field |

### 3. Storage Logic

**UserCognition (JSON):**
- Always stores all profile fields
- No schema constraints
- Used for AI context

**UserProfile (Table):**
- Only created when ALL required fields present:
  - age_range
  - family_structure
  - risk_preference
- Optional fields: occupation, income_range, monthly_expense

## Usage Examples

### Extract and Store Profile Data

```python
from app.services.information_extraction import extract_information
from app.services.asset_extraction_service import asset_extraction_service

# Extract from user message
extraction_result = await extract_information(
    "我是软件工程师，年收入30-50万",
    conversation_history
)

# Store to database
success = await asset_extraction_service.update_user_state(
    user_id=user_id,
    extraction_result=extraction_result
)
```

### Query Profile Data

```python
from app.models.user import UserProfile
from app.models.cognition import UserCognition

# From UserProfile (structured)
profile = await session.execute(
    select(UserProfile).where(UserProfile.user_id == user_id)
)
profile = profile.scalar_one_or_none()

if profile:
    occupation = profile.occupation
    income_range = profile.income_range

# From UserCognition (always available)
cognition = await session.execute(
    select(UserCognition).where(UserCognition.user_id == user_id)
)
cognition = cognition.scalar_one_or_none()

if cognition and cognition.risk_profile:
    occupation = cognition.risk_profile.get('occupation')
    income_range = cognition.risk_profile.get('income_range')
```

## Testing

```bash
# Test partial profile (occupation/income only)
python scripts/test_profile_data_flow.py

# Test complete profile (all fields)
python scripts/test_profile_complete_flow.py
```

## Migration

```bash
# Apply database migration
cd backend
alembic upgrade head
```

## Files Modified

- `backend/app/models/user.py` - Added fields to UserProfile
- `backend/app/services/asset_extraction_service.py` - Updated storage logic
- `backend/alembic/versions/add_occupation_income_to_user_profile.py` - Migration

## Common Issues

**Q: UserProfile not created?**  
A: UserProfile requires age_range, family_structure, and risk_preference. If these are missing, data is stored in UserCognition.risk_profile only.

**Q: Where should I query profile data from?**  
A: Use UserCognition.risk_profile for most cases (always available). Use UserProfile for structured queries when you need SQL filtering.

**Q: How to update occupation/income_range?**  
A: Call `asset_extraction_service.update_user_state()` with extraction_result containing the new values.

## Related Documents

- [Full Fix Summary](../fix_summary/profile_data_flow_fix_summary.md)
- [LLM Extraction Refactor](./LLM_EXTRACTION_REFACTOR_SUMMARY.md)
- [Phase 2 Implementation](./PHASE2_IMPLEMENTATION_SUMMARY.md)
