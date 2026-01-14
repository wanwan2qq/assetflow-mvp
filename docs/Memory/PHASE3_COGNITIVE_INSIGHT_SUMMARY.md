# Phase 3: Cognitive Insight Worker (System 2) - Implementation Summary

## Overview

Phase 3 implements a "Slow Thinking" layer that analyzes conversation history to generate deep psychological insights and adaptive advisor strategies. This enables the AI to adjust its tone, recommendations, and communication style based on the user's emotional state and risk profile.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Chat Flow (Real-time)                     │
│  User Message → Chat Agent → LLM Response → User            │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    (Background Trigger)
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              Insight Service (System 2 - Slow)               │
│  1. Fetch recent 20-50 messages                             │
│  2. LLM psychological analysis                               │
│  3. Update UserCognition (risk_profile, advisor_note)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Next Turn Context Injection                │
│  Chat Agent reads advisor_note from UserCognition           │
│  Injects as hidden context: [💡 ADVISOR STRATEGY NOTE]      │
│  LLM adjusts behavior based on psychological profile         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Insight Service (`app/services/insight_service.py`)

**Core Method: `analyze_user_psychology(user_id, recent_messages)`**

- **Input**: User ID and recent 20-50 chat messages
- **Process**: 
  - Formats conversation history for LLM analysis
  - Uses specialized psychological profiling prompt
  - Analyzes tone, word choice, emotional reactions
- **Output**: JSON with psychological profile
  ```json
  {
    "risk_profile": {
      "tolerance": "conservative|moderate|aggressive",
      "decision_style": "analytical|intuitive|cautious|impulsive",
      "confidence_level": "low|medium|high"
    },
    "current_sentiment": "anxious|confident|confused|optimistic|stressed",
    "psychological_traits": {
      "loss_aversion": "high|medium|low",
      "uncertainty_tolerance": "high|medium|low",
      "financial_literacy": "beginner|intermediate|advanced",
      "family_responsibility": "high|medium|low",
      "planning_horizon": "short|medium|long"
    },
    "advisor_note_internal": "Strategy guidance for AI advisor",
    "key_concerns": ["concern1", "concern2", ...],
    "recommended_approach": "Communication strategy"
  }
  ```

**Database Update:**
- Updates `UserCognition.risk_profile` with psychological traits
- Updates `UserCognition.advisor_note` with strategy guidance
- Sets `updated_at` timestamp

**Mock Mode:**
- Provides keyword-based analysis for development without API costs
- Detects stress, conservative, and aggressive keywords
- Generates appropriate advisor notes

### 2. Chat Agent Integration (`app/services/chat_agent.py`)

**Changes Made:**

1. **Context Injection** (`_prepare_contextual_input`):
   ```python
   # Phase 3: Add advisor strategy note
   advisor_note = await self._get_advisor_strategy_note(user_id)
   if advisor_note:
       contextual_parts.append(
           f"\n\n💡 【ADVISOR STRATEGY NOTE】\n{advisor_note}\n"
           "[重要提示: 根据上述策略调整你的语气和建议方向。用户看不到这条笔记。]"
       )
   ```

2. **Background Trigger** (`_trigger_insight_analysis`):
   - Triggered after each AI response (fire-and-forget)
   - Optimization: Only runs after 5+ messages
   - Optional: Can be configured to run every N turns to save API costs
   - Non-blocking: Doesn't delay user response

3. **Helper Methods**:
   - `_get_advisor_strategy_note(user_id)`: Retrieves current strategy from DB
   - `_trigger_insight_analysis(user_id, context)`: Initiates background analysis

### 3. Database Schema (Already Exists)

**UserCognition Model** (`app/models/cognition.py`):
- `risk_profile` (JSON): Stores psychological profile
- `advisor_note` (String): Internal strategy guidance for AI
- `updated_at` (DateTime): Last analysis timestamp

## Acceptance Criteria Test

### Scenario:
1. **User says**: "I'm really scared of the stock market crashing again."
2. **Background Task**: `InsightService` analyzes conversation
3. **Result**: Updates `risk_profile` → "conservative" and `advisor_note` → "Focus on capital preservation"
4. **Next Turn**: When user asks "What should I buy?", AI reads the note and suggests "Bonds/Gold" instead of "Crypto/Stocks", using a reassuring tone

### Test Script:
```bash
cd backend
python test_phase3_insight_worker.py
```

## Key Features

### 1. Psychological Profiling
- **Risk Tolerance**: Conservative, Moderate, Aggressive
- **Decision Style**: Analytical, Intuitive, Cautious, Impulsive
- **Emotional State**: Anxious, Confident, Confused, Optimistic, Stressed
- **Behavioral Traits**: Loss aversion, uncertainty tolerance, financial literacy

### 2. Adaptive Behavior
- **Tone Adjustment**: Empathetic for anxious users, encouraging for confident users
- **Product Recommendations**: Conservative products for risk-averse users
- **Communication Style**: Detailed for analytical users, simple for intuitive users

### 3. Performance Optimization
- **Trigger Threshold**: Only analyzes after 5+ messages
- **Optional Interval**: Can be configured to run every N turns
- **Non-blocking**: Runs as background task, doesn't delay responses
- **Mock Mode**: Keyword-based analysis for development

## Example Flow

### Turn 1-4: Initial Conversation
```
User: "你好，我想咨询资产配置"
AI: "您好！请问您目前有房产吗？"
User: "有的，但房贷压力很大，每月还2万多"
AI: "我理解高房贷确实会带来压力..."
```

### Turn 5: Insight Analysis Triggered
```
[Background] Analyzing conversation...
[Background] Detected: High stress, conservative tendency
[Background] Updated risk_profile: "conservative"
[Background] Updated advisor_note: "用户表现出财务压力。建议避免激进投资，多强调稳健保本方案，语气要温和安抚。"
```

### Turn 6: Adaptive Response
```
User: "我有50万，该怎么投资？"

[Hidden Context Injected]
💡 【ADVISOR STRATEGY NOTE】
用户表现出财务压力。建议避免激进投资，多强调稳健保本方案，语气要温和安抚。

AI: "考虑到您的房贷压力，我建议采用稳健的配置策略 🤝
     
     🔹 应急资金（20%）：10万 - 银行活期/货币基金
     🔹 保险保障（20%）：10万 - 重疾险、意外险
     🔹 稳健理财（40%）：20万 - 债券基金、银行理财
     🔹 适度增长（20%）：10万 - 混合型基金
     
     这样的配置既能保证资金安全，又能获得稳定收益，不会给您增加心理压力。"
```

## Configuration

### Trigger Frequency (Optional Optimization)
```python
# In chat_agent.py, _trigger_insight_analysis method

# Current: Analyze every turn (after 5+ messages)
if message_count < 5:
    return

# Optional: Analyze every 5 turns to save API costs
# if message_count % 5 != 0:
#     return
```

### Mock vs Real Analysis
```python
# Controlled by OPENAI_API_KEY in .env
# If key is "sk-mock" or "mock-key", uses keyword-based mock analysis
# Otherwise, uses LLM-based deep analysis
```

## Testing

### Unit Test
```bash
cd backend
python test_phase3_insight_worker.py
```

### Integration Test
1. Start backend server
2. Login as test user
3. Send messages with emotional content:
   - "我很担心股市崩盘"
   - "房贷压力很大"
   - "不想冒险"
4. After 5+ messages, check database:
   ```sql
   SELECT risk_profile, advisor_note FROM user_cognition WHERE user_id = ?;
   ```
5. Send investment question
6. Verify AI response reflects conservative strategy

## Files Modified/Created

### Created:
- `backend/app/services/insight_service.py` - Core insight analysis service
- `backend/test_phase3_insight_worker.py` - Test script
- `backend/PHASE3_COGNITIVE_INSIGHT_SUMMARY.md` - This document

### Modified:
- `backend/app/services/chat_agent.py`:
  - Added `_get_advisor_strategy_note()` method
  - Added `_trigger_insight_analysis()` method
  - Updated `_prepare_contextual_input()` to inject advisor note
  - Added insight trigger in `process_message()` and `_process_message_mock()`

## Benefits

1. **Personalized Experience**: AI adapts to each user's psychological profile
2. **Emotional Intelligence**: Detects and responds to user stress, anxiety, fear
3. **Better Outcomes**: Recommendations align with user's actual risk tolerance
4. **Trust Building**: Empathetic responses increase user confidence
5. **Scalable**: Background processing doesn't impact response time

## Future Enhancements

1. **Sentiment Tracking**: Track sentiment changes over time
2. **Trigger Events**: Analyze after significant market events
3. **Multi-dimensional Analysis**: Add more psychological dimensions
4. **A/B Testing**: Compare outcomes with/without adaptive behavior
5. **User Feedback Loop**: Learn from user reactions to recommendations

## Conclusion

Phase 3 successfully implements a cognitive insight layer that enables the AI advisor to understand user psychology and adapt its behavior accordingly. This creates a more empathetic, personalized, and effective advisory experience.

The system is production-ready with:
- ✅ LLM-based psychological analysis
- ✅ Database persistence of insights
- ✅ Context injection for adaptive behavior
- ✅ Background processing for performance
- ✅ Mock mode for development
- ✅ Comprehensive testing
