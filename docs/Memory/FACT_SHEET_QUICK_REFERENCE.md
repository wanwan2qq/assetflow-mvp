# Fact Sheet Quick Reference

## What is the Fact Sheet?

The Fact Sheet is a structured summary of confirmed user assets that gets injected into the AI's context on every turn. It prevents the AI from hallucinating or confusing asset details.

## Key Components

### 1. Asset Details
```
1. [房产] 北京海淀区永靓家园 | 估值: 428万 | 面积: 100平米 | 位置: 北京海淀区 (用户已确认)
2. [现金] 10万 (用户已确认)
3. [投资] 股票基金 | 价值: 50万 (系统推测)
```

### 2. Missing Information
```
【缺失信息提示】
尚未了解: 保险保障
```

### 3. Anti-Hallucination Warning
```
(请基于以上数据回答，严禁编造数据)
```

## How It Works

### Data Flow
```
UserAsset (DB) → _generate_fact_sheet() → _prepare_contextual_input() → AI Context
```

### Confirmation Status
- `is_confirmed=True` → "(用户已确认)"
- `is_confirmed=False` → "(系统推测)"

### Asset Type Formatting

| Asset Type | Format |
|------------|--------|
| Real Estate | `[房产] {name} \| 估值: {value} \| 面积: {area}平米 \| 位置: {location} {status}` |
| Cash | `[现金] {value} {status}` |
| Investment | `[投资] {name} \| 价值: {value} {status}` |
| Insurance | `[保险] {name} \| 保额: {value} {status}` |
| Liability | `[负债] {name} \| 金额: {value} {status}` |

## Code Location

### Main Implementation
- **File:** `backend/app/services/chat_agent.py`
- **Method:** `_generate_fact_sheet(user_id: int) -> str`
- **Line:** ~700-800

### Integration Point
- **Method:** `_prepare_contextual_input(message, context, user_id)`
- **Line:** ~850

### Test Suite
- **File:** `scripts/test_fact_sheet.py`
- **Run:** `cd backend && python ../scripts/test_fact_sheet.py`

## Usage Example

```python
# In ChatAgent
async def _prepare_contextual_input(self, message: str, context: ChatContext, user_id: int) -> str:
    contextual_parts = []
    
    # Generate Fact Sheet
    fact_sheet = await self._generate_fact_sheet(user_id)
    contextual_parts.append(fact_sheet)
    
    # Add other context...
    contextual_parts.append(f"\n【用户消息】\n{message}")
    
    return "".join(contextual_parts)
```

## Testing

### Run Tests
```bash
cd backend
python ../scripts/test_fact_sheet.py
```

### Expected Output
```
✅ Fact Sheet Generation: PASSED
✅ Contextual Input: PASSED
🎉 All tests passed!
```

## Debugging

### Check Fact Sheet Content
```python
from app.services.chat_agent import get_chat_agent

agent = get_chat_agent()
fact_sheet = await agent._generate_fact_sheet(user_id=1)
print(fact_sheet)
```

### Verify Asset Data
```python
from app.models.user import UserAsset
from sqlmodel import select

async for session in get_db_session():
    statement = select(UserAsset).where(UserAsset.user_id == user_id)
    result = await session.execute(statement)
    assets = result.scalars().all()
    
    for asset in assets:
        print(f"{asset.asset_type}: {asset.name} = {asset.value} (confirmed={asset.is_confirmed})")
```

## Common Issues

### Issue 1: Fact Sheet is Empty
**Cause:** No assets in database for user
**Solution:** Check if assets were properly extracted and stored

### Issue 2: Missing Asset Details
**Cause:** `extra_data` field is empty
**Solution:** Ensure extraction service populates `extra_data` with location, area, etc.

### Issue 3: Wrong Confirmation Status
**Cause:** `is_confirmed` field not set correctly
**Solution:** Update extraction logic to set `is_confirmed=True` for explicit user input

## Best Practices

### 1. Always Use Fact Sheet
- Include Fact Sheet at the beginning of contextual input
- It's the most important context for preventing hallucination

### 2. Keep It Concise
- Only include essential information
- Use abbreviations where appropriate
- Token efficiency is important

### 3. Update Regularly
- Fact Sheet reads from DB on every turn
- Ensure DB is updated when new information is extracted

### 4. Test After Changes
- Run test suite after modifying Fact Sheet logic
- Verify output format is correct

## Related Documentation

- [Context Amnesia Fix Summary](./CONTEXT_AMNESIA_FIX_SUMMARY.md)
- [LLM Extraction Quick Reference](./LLM_EXTRACTION_QUICK_REFERENCE.md)
- [Phase 2 Implementation Summary](./PHASE2_IMPLEMENTATION_SUMMARY.md)

## Maintenance

### When to Update Fact Sheet

1. **New Asset Type Added**
   - Add formatting logic in `_generate_fact_sheet()`
   - Update test cases

2. **New Field Added to UserAsset**
   - Update formatting to include new field
   - Consider if it should be in Fact Sheet

3. **Confirmation Logic Changed**
   - Update status display logic
   - Ensure consistency with extraction service

### Performance Considerations

- Fact Sheet generation is fast (single DB query)
- Caching not needed (data changes frequently)
- Keep format concise to save tokens

## Quick Commands

```bash
# Run tests
cd backend && python ../scripts/test_fact_sheet.py

# Check diagnostics
# (Use IDE or linter)

# View Fact Sheet in logs
# Look for "Generated Fact Sheet:" in test output

# Clean up test data
# Test script automatically cleans up
```

## Support

For questions or issues:
1. Check this quick reference
2. Review [Context Amnesia Fix Summary](./CONTEXT_AMNESIA_FIX_SUMMARY.md)
3. Run test suite to verify behavior
4. Check logs for Fact Sheet content
