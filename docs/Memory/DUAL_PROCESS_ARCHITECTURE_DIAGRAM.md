# Dual-Process Cognitive Architecture - Visual Diagram

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER SENDS MESSAGE                              │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CHAT AGENT: process_message()                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. Build Initial Context                                              │
│     ├─ Load conversation history                                       │
│     ├─ Load user profile (from memory)                                 │
│     └─ Load extracted assets (from memory)                             │
│                                                                         │
│  2. Generate AI Response (Streaming)                                   │
│     ├─ Prepare contextual input with Fact Sheet                        │
│     ├─ Call LLM with context                                           │
│     └─ Stream response chunks to user                                  │
│                                                                         │
│  3. Save AI Response to Database                                       │
│     └─ chat_history_service.save_ai_message()                          │
│                                                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM 1: IMMEDIATE CONSISTENCY                      │
│                         (Blocking - Must Complete)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  4. Extract Information                                                │
│     └─ _trigger_information_extraction()                               │
│        ├─ Call LLM to extract structured data                          │
│        ├─ Parse assets, profile, goals                                 │
│        └─ Return extraction_result                                     │
│                                                                         │
│  5. Write to Database (L1/L2)                                          │
│     └─ asset_extraction_service.update_user_state()                    │
│        ├─ L1: Upsert UserAsset (cash, real_estate, etc.)              │
│        ├─ L1: Upsert UserProfile (age, family, occupation, income)    │
│        └─ L2: Update UserCognition (collection_status, goals)         │
│                                                                         │
│  6. ✨ CONTEXT REFRESH ✨ (NEW!)                                       │
│     └─ _refresh_context_from_db()                                      │
│        ├─ Reload UserProfile from DB                                   │
│        │  └─ context.user_profile = fresh_profile                      │
│        ├─ Reload UserAssets from DB                                    │
│        │  └─ context.extracted_assets = fresh_assets                   │
│        └─ Reload UserCognition from DB                                 │
│           └─ context.current_stage = calculate_stage()                 │
│                                                                         │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SYSTEM 2: NON-BLOCKING LATENCY                       │
│                      (Async - Fire and Forget)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  7. Trigger Insight Analysis (Background)                              │
│     └─ _trigger_insight_analysis()                                     │
│        ├─ insight_service.analyze_user_psychology()                    │
│        │  ├─ L3: Analyze conversation for psychological traits         │
│        │  ├─ L3: Generate advisor strategy notes                       │
│        │  └─ L3: Update UserCognition.risk_profile                     │
│        └─ memory_service.store_conversation_memory()                   │
│           ├─ L4: Generate embeddings for conversation                  │
│           ├─ L4: Store in VectorMemory table                           │
│           └─ L4: Enable semantic search for future queries             │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                        READY FOR NEXT MESSAGE
                    (Context is fresh and up-to-date!)
```

---

## Data Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYERS                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  L1: FACTS (Immediate Consistency)                                     │
│  ├─ UserProfile                                                        │
│  │  ├─ age_range: "30-40"                                              │
│  │  ├─ family_structure: "married_with_kids"                           │
│  │  ├─ occupation: "Software Engineer"                                 │
│  │  ├─ income_range: "200k-300k"                                       │
│  │  ├─ monthly_expense: 15000                                          │
│  │  └─ risk_preference: "moderate"                                     │
│  │                                                                      │
│  └─ UserAsset                                                          │
│     ├─ [Real Estate] Beijing Apartment | 5M | 120㎡                    │
│     ├─ [Cash] Savings | 500k                                           │
│     ├─ [Investment] Stock Portfolio | 300k                             │
│     └─ [Liability] Mortgage | -2M                                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  L2: STATUS (Immediate Consistency)                                    │
│  └─ UserCognition                                                      │
│     ├─ collection_status:                                              │
│     │  ├─ real_estate: ✅ True                                         │
│     │  ├─ cash: ✅ True                                                │
│     │  ├─ investment: ✅ True                                          │
│     │  ├─ insurance: ❌ False                                          │
│     │  └─ liability: ✅ True                                           │
│     │                                                                   │
│     └─ financial_goals:                                                │
│        ├─ "retirement"                                                 │
│        ├─ "education"                                                  │
│        └─ "wealth_growth"                                              │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  L3: INSIGHTS (Eventual Consistency - System 2)                        │
│  └─ UserCognition.risk_profile                                         │
│     ├─ tolerance: "moderate"                                           │
│     ├─ decision_style: "analytical"                                    │
│     ├─ confidence_level: "high"                                        │
│     ├─ current_sentiment: "optimistic"                                 │
│     ├─ loss_aversion: "medium"                                         │
│     ├─ uncertainty_tolerance: "high"                                   │
│     ├─ financial_literacy: "advanced"                                  │
│     ├─ family_responsibility: "high"                                   │
│     └─ planning_horizon: "long_term"                                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  L4: MEMORY (Eventual Consistency - System 2)                          │
│  └─ VectorMemory                                                       │
│     ├─ Conversation embeddings (768-dim vectors)                       │
│     ├─ Semantic search capability                                      │
│     └─ Relevant memory retrieval for context                           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Before vs After Comparison

### BEFORE: Stale Context Bug

```
Turn 1:
  User: "I am 35 years old"
  ├─ AI generates response
  ├─ Extraction writes to DB: UserProfile.age_range = "30-40"
  └─ ❌ Context NOT refreshed
      └─ context.user_profile = {} (empty!)

Turn 2:
  User: "What should I invest in?"
  ├─ AI reads context.user_profile = {} (empty!)
  └─ AI: "To give better advice, how old are you?" ❌
```

### AFTER: Context Refresh Working

```
Turn 1:
  User: "I am 35 years old"
  ├─ AI generates response
  ├─ Extraction writes to DB: UserProfile.age_range = "30-40"
  └─ ✅ Context refreshed!
      └─ context.user_profile = {"age_range": "30-40", ...}

Turn 2:
  User: "What should I invest in?"
  ├─ AI reads context.user_profile = {"age_range": "30-40"}
  └─ AI: "Based on your age (35), I recommend..." ✅
```

---

## Timing Diagram

```
Time →

User Message Arrives
│
├─ [0ms] Start processing
│
├─ [100ms] Load initial context from memory
│
├─ [2000ms] Generate AI response (streaming)
│   └─ User sees response chunks in real-time
│
├─ [2100ms] Save AI response to DB
│
├─ [2200ms] SYSTEM 1 START (Blocking)
│   ├─ Extract information (LLM call)
│   ├─ Write to DB (L1/L2)
│   └─ ✨ Refresh context ✨ (+50ms overhead)
│
├─ [2800ms] SYSTEM 1 COMPLETE
│
├─ [2800ms] SYSTEM 2 START (Fire-and-forget)
│   ├─ Psychological analysis (background)
│   └─ Vector memory storage (background)
│
└─ [2800ms] Ready for next message!
    └─ Context is fresh and up-to-date

    [5000ms] SYSTEM 2 COMPLETE (doesn't block next message)
```

---

## Key Insight: Why Context Refresh is Critical

### The Problem

```python
# BEFORE: Data written to DB but not visible to AI

# Turn 1
extraction_result = {"age_range": "30-40"}
await db.write(extraction_result)  # ✅ DB updated
# context.user_profile = {}  # ❌ Still empty!

# Turn 2
ai_input = prepare_input(context)  # Uses empty context
# AI doesn't know user's age!
```

### The Solution

```python
# AFTER: Data written to DB AND refreshed in context

# Turn 1
extraction_result = {"age_range": "30-40"}
await db.write(extraction_result)  # ✅ DB updated
await refresh_context_from_db(context)  # ✅ Context updated!
# context.user_profile = {"age_range": "30-40"}  # ✅ Fresh!

# Turn 2
ai_input = prepare_input(context)  # Uses fresh context
# AI knows user's age!
```

---

## Performance Characteristics

| Operation | Latency | Blocking? | Impact |
|-----------|---------|-----------|--------|
| Load initial context | ~10ms | Yes | Negligible |
| Generate AI response | ~2s | Yes (streaming) | User sees chunks |
| Save to DB | ~50ms | Yes | Negligible |
| Extract information | ~500ms | Yes | Necessary |
| Write to DB (L1/L2) | ~100ms | Yes | Necessary |
| **Context refresh** | **~50ms** | **Yes** | **Minimal** |
| Psychological analysis | ~2s | No (async) | No impact |
| Vector memory storage | ~1s | No (async) | No impact |

**Total overhead from context refresh**: ~50ms per turn (negligible)

---

## Success Metrics

### Before Refactor
- ❌ AI asks repetitive questions
- ❌ User frustration: "I just told you my age!"
- ❌ Poor conversation flow
- ❌ Data in DB but not used

### After Refactor
- ✅ AI remembers what user said
- ✅ Natural conversation flow
- ✅ User satisfaction improved
- ✅ Data in DB and immediately available

---

## Conclusion

The Dual-Process Cognitive Architecture successfully separates:

1. **System 1 (Fast Thinking)**: Immediate facts and status that must be available NOW
2. **System 2 (Slow Thinking)**: Deep insights and analysis that can happen later

The critical missing piece was **context refresh** - ensuring that data written to the database is immediately reflected in the in-memory context used by the AI.

**Result**: A natural, intelligent conversation experience where the AI truly "remembers" what the user tells it.
