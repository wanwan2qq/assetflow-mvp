# Dual-Process Architecture - Quick Reference

**Last Updated**: 2026-01-15  
**Status**: ✅ PRODUCTION READY

---

## 🎯 What Problem Does This Solve?

**Before**: User says "I am 35 years old" → AI responds → Next turn: AI asks "How old are you?" again  
**After**: User says "I am 35 years old" → AI responds → Next turn: AI says "Based on your age (35)..."

**Root Cause**: Missing context refresh after data extraction  
**Solution**: Implement System 1 (immediate consistency) + System 2 (async processing)

---

## 🏗️ Architecture at a Glance

```
User Message
    ↓
Generate AI Response (streaming)
    ↓
Save to DB
    ↓
┌─────────────────────────────────────┐
│ SYSTEM 1 (Blocking - Must Complete)│
├─────────────────────────────────────┤
│ 1. Extract Information (LLM)       │
│ 2. Write to DB (L1/L2)             │
│ 3. ✨ REFRESH CONTEXT ✨           │
│    - Reload UserProfile            │
│    - Reload UserAssets             │
│    - Reload UserCognition          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ SYSTEM 2 (Async - Fire & Forget)  │
├─────────────────────────────────────┤
│ 1. Psychological Analysis (L3)     │
│ 2. Vector Memory Storage (L4)     │
│ 3. Advisor Strategy Notes (L3)    │
└─────────────────────────────────────┘
```

---

## 📁 Key Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/app/services/chat_agent.py` | Added `_refresh_context_from_db()` | System 1: Context refresh |
| `backend/app/services/chat_agent.py` | Updated `process_message()` | Call context refresh after extraction |
| `backend/app/services/chat_agent.py` | Updated `_process_message_mock()` | Call context refresh in mock mode |
| `backend/app/services/asset_extraction_service.py` | Fixed L1/L2 separation | Proper data layer management |

---

## 🔧 Key Implementation

### Context Refresh (System 1)

```python
async def _refresh_context_from_db(self, user_id: int, context: ChatContext):
    """Force reload user state from DB after extraction"""
    
    # Reload UserProfile (L1: age, family, occupation, income)
    profile = await get_user_profile(user_id)
    context.user_profile = profile.to_dict()
    
    # Reload UserAssets (L1: all assets)
    assets = await get_user_assets(user_id)
    context.extracted_assets = [asset.to_dict() for asset in assets]
    
    # Reload UserCognition (L2: collection status, goals)
    cognition = await get_user_cognition(user_id)
    context.current_stage = calculate_stage(cognition.collection_status)
```

### Integration Point

```python
async def process_message(self, message, user_id):
    # ... generate AI response ...
    
    # Extract and store information
    await self._trigger_information_extraction(message, user_id, context)
    
    # ✨ NEW: Refresh context from DB ✨
    await self._refresh_context_from_db(user_id, context)
    
    # Trigger async System 2 processing
    await self._trigger_insight_analysis(user_id, context)
```

---

## 🧪 Testing

### Run Tests

```bash
cd backend
python ../scripts/test_dual_process_architecture.py
```

### Quick Manual Test

```python
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload

# Terminal 2: Test with curl
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "I am 35 years old"}'

# Next message should acknowledge age
curl -X POST http://localhost:8000/api/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"message": "What should I invest in?"}'
```

---

## 📊 Data Layers

| Layer | Type | Storage | Timing | Examples |
|-------|------|---------|--------|----------|
| **L1** | Facts | `UserProfile`, `UserAsset` | Immediate | Age, income, assets |
| **L2** | Status | `UserCognition.collection_status` | Immediate | Cash collected: ✅ |
| **L3** | Insights | `UserCognition.risk_profile` | Async | Psychological profile |
| **L4** | Memory | `VectorMemory` | Async | Semantic search |

---

## 🐛 Debugging

### Check Context Refresh Logs

```bash
# Look for these log messages
grep "CONTEXT_REFRESH" backend/logs/app.log

# Expected output:
🔄 CONTEXT_REFRESH: Starting context refresh for user 123
🔄 CONTEXT_REFRESH: Updated user_profile in context: {'age_range': '30-40'}
🔄 CONTEXT_REFRESH: Updated 3 assets in context
🔄 CONTEXT_REFRESH: ✅ Context refresh complete for user 123
```

### Verify DB State

```sql
-- Check UserProfile
SELECT * FROM user_profile WHERE user_id = 123;

-- Check UserAssets
SELECT * FROM user_asset WHERE user_id = 123;

-- Check UserCognition
SELECT collection_status FROM user_cognition WHERE user_id = 123;
```

---

## ⚡ Performance

- **Context Refresh Overhead**: ~50-100ms (3 DB queries)
- **Response Time Impact**: Negligible (happens after streaming)
- **System 2 Latency**: 2-5 seconds (doesn't block response)

---

## 🚨 Common Issues

### Issue 1: AI Still Asks Repetitive Questions

**Cause**: Context refresh not being called  
**Fix**: Check logs for `CONTEXT_REFRESH` messages  
**Verify**: Ensure `_refresh_context_from_db` is called after extraction

### Issue 2: Slow Response Times

**Cause**: System 2 blocking System 1  
**Fix**: Verify `_trigger_insight_analysis` is fire-and-forget  
**Verify**: Check response time < 5 seconds

### Issue 3: Data Not Persisting

**Cause**: Extraction failing silently  
**Fix**: Check logs for extraction errors  
**Verify**: Query DB directly to confirm data is written

---

## 📚 Related Docs

- [Full Architecture Doc](./DUAL_PROCESS_ARCHITECTURE_REFACTOR.md)
- [Phase 2: Collection Status](./PHASE2_COLLECTION_STATUS_FIX_SUMMARY.md)
- [Phase 3: Cognitive Insights](./PHASE3_COGNITIVE_INSIGHT_SUMMARY.md)
- [Phase 4: Vector Memory](./PHASE4_VECTOR_MEMORY_SUMMARY.md)

---

## ✅ Checklist for New Developers

- [ ] Read full architecture doc
- [ ] Run test suite and verify all pass
- [ ] Understand System 1 vs System 2 separation
- [ ] Know where context refresh happens
- [ ] Understand L1/L2/L3/L4 data layers
- [ ] Can debug using logs and DB queries

---

**Questions?** Check the full documentation or ask the team!
