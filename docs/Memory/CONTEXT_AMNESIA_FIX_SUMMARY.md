# Context Amnesia Fix - Fact Sheet Implementation

## Problem Statement
The AI was experiencing "Context Amnesia" - hallucinating asset details (e.g., confusing 100sqm with 90sqm) because it relied on loose conversation history without structured, confirmed data.

## Solution Overview
Implemented a structured "Fact Sheet" that injects confirmed asset data into the system prompt context, preventing the AI from fabricating or confusing information.

## Changes Made

### 1. Modified `backend/app/services/chat_agent.py`

#### A. Replaced `_generate_state_checklist` with `_generate_fact_sheet`

**Old Approach:**
- Simple checklist showing ✅/❌ for asset types
- Limited detail: only showed if asset type exists
- Example: `[✅] 房产 (Real Estate): 已知 (北京海淀区永靓家园, 428万)`

**New Approach:**
- Detailed fact sheet with complete asset information
- Shows all critical fields: location, area, value, confirmation status
- Highlights missing fields to prompt AI to ask about them
- Example:
```
【当前系统已确信的资产清单 (Fact Sheet)】
1. [房产] 北京海淀区永靓家园 | 估值: 428万 | 面积: 100平米 | 位置: 北京海淀区 (用户已确认)
2. [现金] 10万 (用户已确认)
3. [投资] 股票基金 | 价值: 50万 (系统推测)

【缺失信息提示】
尚未了解: 保险保障

(请基于以上数据回答，严禁编造数据)
```

#### B. Updated `_prepare_contextual_input`

Changed from:
```python
state_checklist = await self._generate_state_checklist(user_id)
contextual_parts.append(state_checklist)
```

To:
```python
fact_sheet = await self._generate_fact_sheet(user_id)
contextual_parts.append(fact_sheet)
```

### 2. Key Features of the Fact Sheet

#### Asset-Specific Formatting
- **Real Estate**: Shows location, value, area, and confirmation status
- **Cash**: Shows value and confirmation status
- **Investment**: Shows name, value, and confirmation status
- **Insurance**: Shows name, coverage amount, and confirmation status
- **Liability**: Shows name, amount, and confirmation status

#### Confirmation Status Tracking
- `(用户已确认)` - User explicitly confirmed this data
- `(系统推测)` - System inferred from conversation (needs confirmation)

#### Missing Information Hints
- Lists asset types not yet collected
- Prompts AI to ask about missing categories
- Example: "尚未了解: 保险保障"

#### Anti-Hallucination Warning
- Explicit instruction: "(请基于以上数据回答，严禁编造数据)"
- Prevents AI from fabricating information

### 3. Asset Merging Logic (Already Implemented)

The existing `asset_extraction_service.py` already handles intelligent merging:

```python
# Check for existing asset of same type
existing_statement = select(UserAsset).where(
    UserAsset.user_id == user_id,
    UserAsset.asset_type == asset_type
)
existing_result = await session.execute(existing_statement)
existing_asset = existing_result.scalar_one_or_none()

if existing_asset:
    # Update existing asset instead of creating duplicate
    existing_asset.value = amount
    existing_asset.name = name
    # Update metadata...
```

This ensures:
- No duplicate assets of the same type
- Updates existing records when new information is extracted
- Preserves metadata (location, area, etc.)

## Testing

Created comprehensive test suite: `scripts/test_fact_sheet.py`

### Test Results
```
✅ Fact Sheet Generation: PASSED
  ✅ Has header
  ✅ Shows real estate
  ✅ Shows value
  ✅ Shows area
  ✅ Shows confirmation
  ✅ Shows cash
  ✅ Shows investment
  ✅ Shows unconfirmed
  ✅ Has missing info
  ✅ Has warning

✅ Contextual Input: PASSED
  ✅ Has Fact Sheet
  ✅ Has user message
  ✅ Has asset details
  ✅ Has stage hint
```

## Benefits

### 1. Prevents Hallucination
- AI sees exact data from database
- Clear distinction between confirmed and inferred data
- Explicit warning against fabrication

### 2. Improves Accuracy
- Detailed asset information (location, area, value)
- Confirmation status helps AI understand data reliability
- Missing field hints guide conversation flow

### 3. Better User Experience
- AI doesn't confuse similar assets
- Consistent information across conversation
- Natural follow-up questions for missing data

### 4. Token Efficiency
- Concise format saves tokens
- Only shows relevant information
- Structured format is easy for AI to parse

## Example Conversation Flow

**User:** "我的房子现在值多少钱？"

**AI receives:**
```
【当前系统已确信的资产清单 (Fact Sheet)】
1. [房产] 北京海淀区永靓家园 | 估值: 428万 | 面积: 100平米 | 位置: 北京海淀区 (用户已确认)

【用户消息】
我的房子现在值多少钱？
```

**AI responds:** "根据最新的市场数据，您在北京海淀区永靓家园的房产估值约为428万元。这是一套100平米的房产..."

**Result:** AI uses exact data from Fact Sheet, no hallucination!

## Integration with Existing Systems

### L1 (UserAsset)
- Fact Sheet reads directly from UserAsset table
- Uses `is_confirmed` field to show confirmation status
- Reads `extra_data` for location, area, etc.

### L2 (UserCognition)
- Shows risk profile from cognition data
- Can be extended to show financial goals

### L3 (Vector Memory)
- Fact Sheet complements vector memory
- Provides structured data while vector memory provides context

### L4 (Insight Service)
- Fact Sheet provides factual data
- Insight service provides psychological profiling
- Together they give AI complete context

## Future Enhancements

1. **Dynamic Field Highlighting**
   - Highlight recently updated fields
   - Show data freshness (e.g., "更新于2天前")

2. **Confidence Scoring**
   - Show confidence levels for inferred data
   - Example: "估值: 428万 (置信度: 85%)"

3. **Change Tracking**
   - Show when values changed
   - Example: "估值: 428万 (↑ 从420万)"

4. **Multi-Asset Support**
   - Handle multiple assets of same type
   - Example: "房产1: ..., 房产2: ..."

5. **Validation Prompts**
   - Suggest validation for old data
   - Example: "房产估值已3个月未更新，建议重新评估"

## Conclusion

The Fact Sheet implementation successfully addresses the "Context Amnesia" problem by providing the AI with structured, confirmed asset data. This prevents hallucination, improves accuracy, and creates a better user experience.

**Status:** ✅ Implemented and Tested
**Impact:** High - Directly addresses core AI reliability issue
**Complexity:** Low - Simple, maintainable solution
