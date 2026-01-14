# Phase 3: Quick Reference Guide

## 🎯 What is Phase 3?

Phase 3 adds **psychological profiling** and **adaptive behavior** to the AI advisor. The system analyzes conversation patterns to understand user psychology and adjusts its recommendations and tone accordingly.

## 🚀 Quick Start

### Run Tests
```bash
cd backend
python test_phase3_insight_worker.py
```

### Check Database
```sql
-- View psychological profile
SELECT 
    user_id,
    risk_profile->>'tolerance' as risk_tolerance,
    risk_profile->>'current_sentiment' as sentiment,
    advisor_note
FROM user_cognition
WHERE user_id = 3;
```

## 📊 How It Works

```
User Message → Chat Agent → AI Response
                    ↓
            (Background Task)
                    ↓
         Insight Service Analyzes
                    ↓
    Updates UserCognition (risk_profile, advisor_note)
                    ↓
         Next Turn: AI Reads Note
                    ↓
         Adapts Behavior & Tone
```

## 🔑 Key Components

### 1. Insight Service
**File**: `app/services/insight_service.py`

**Main Method**:
```python
await insight_service.analyze_user_psychology(user_id)
```

**Output**:
- Risk tolerance: conservative/moderate/aggressive
- Sentiment: anxious/confident/confused/optimistic/stressed
- Advisor note: Internal strategy guidance

### 2. Chat Agent Integration
**File**: `app/services/chat_agent.py`

**Key Methods**:
- `_get_advisor_strategy_note()`: Retrieves strategy from DB
- `_trigger_insight_analysis()`: Starts background analysis
- `_prepare_contextual_input()`: Injects note into context

### 3. Database
**Table**: `user_cognition`

**Key Fields**:
- `risk_profile` (JSON): Psychological profile
- `advisor_note` (String): Strategy guidance
- `updated_at` (DateTime): Last analysis time

## 💡 Example Scenarios

### Scenario 1: Anxious User
```
User: "我很害怕股市崩盘，2015年亏了50万"

Analysis:
- Risk Tolerance: conservative
- Sentiment: anxious
- Note: "避免提及股市，强调保本和安全"

Next Response:
- Suggests: Bonds, bank wealth management
- Avoids: Stocks, high-risk investments
- Tone: Empathetic and reassuring
```

### Scenario 2: Confident User
```
User: "我想追求高收益，能承受波动"

Analysis:
- Risk Tolerance: aggressive
- Sentiment: confident
- Note: "可以介绍成长型投资，但要提示风险"

Next Response:
- Suggests: Growth stocks, equity funds
- Includes: Risk warnings
- Tone: Professional and balanced
```

## 🎛️ Configuration

### Trigger Frequency
```python
# In chat_agent.py, _trigger_insight_analysis()

# Option 1: Every turn (after 5 messages) - Current
if message_count < 5:
    return

# Option 2: Every 5 turns - Cost-optimized
if message_count % 5 != 0:
    return
```

### Mock vs Real Analysis
```bash
# In .env file

# Real LLM analysis
OPENAI_API_KEY=sk-your-real-key

# Mock analysis (development)
OPENAI_API_KEY=sk-mock-key
```

## 📈 Monitoring

### Check Analysis Status
```python
from app.services.insight_service import get_insight_service

insight_service = get_insight_service()
advisor_note = await insight_service.get_advisor_strategy(user_id)
print(advisor_note)
```

### View Logs
```bash
# Filter insight service logs
tail -f logs/app.log | grep "insight_service"
```

## 🧪 Testing Checklist

- [ ] Unit tests pass: `python test_phase3_insight_worker.py`
- [ ] Integration tests pass: `python test_phase3_e2e_integration.py`
- [ ] Database updates correctly
- [ ] Advisor note is injected into context
- [ ] AI response adapts to user psychology
- [ ] Conservative users get conservative advice
- [ ] Empathetic tone for anxious users

## 🐛 Troubleshooting

### Issue: No insight analysis triggered
**Solution**: Check message count (needs 5+ messages)
```python
# In chat_agent.py
logger.info(f"Message count: {len(context.conversation_history)}")
```

### Issue: Advisor note not found
**Solution**: Check database
```sql
SELECT * FROM user_cognition WHERE user_id = ?;
```

### Issue: AI not adapting behavior
**Solution**: Verify context injection
```python
# In chat_agent.py, _prepare_contextual_input()
logger.info(f"Contextual input: {contextual_input}")
```

## 📚 Related Files

### Core Implementation
- `app/services/insight_service.py` - Insight analysis
- `app/services/chat_agent.py` - Chat integration
- `app/models/cognition.py` - Database model

### Tests
- `test_phase3_insight_worker.py` - Unit tests
- `test_phase3_e2e_integration.py` - Integration tests
- `PHASE3_VERIFICATION.py` - Demonstration

### Documentation
- `PHASE3_COGNITIVE_INSIGHT_SUMMARY.md` - Detailed docs
- `PHASE3_IMPLEMENTATION_COMPLETE.md` - Implementation summary
- `PHASE3_QUICK_REFERENCE.md` - This file

## 🎓 Key Concepts

### System 1 vs System 2
- **System 1** (Fast): Immediate chat responses
- **System 2** (Slow): Deep psychological analysis

### Adaptive Behavior
- **Input**: User conversation history
- **Process**: LLM psychological profiling
- **Output**: Personalized advisor strategy
- **Effect**: AI adapts tone and recommendations

### Context Injection
```
[Hidden from user]
💡 ADVISOR STRATEGY NOTE:
用户表现出保守倾向。建议避免激进投资，多强调稳健保本方案。

[User sees]
User: "我该怎么投资？"
AI: "考虑到您的情况，我建议采用稳健的配置策略..."
```

## ✅ Success Criteria

Phase 3 is working correctly if:
1. ✅ Insight analysis runs after 5+ messages
2. ✅ UserCognition table is updated
3. ✅ Advisor note is injected into context
4. ✅ AI response reflects psychological insights
5. ✅ Conservative users get conservative advice
6. ✅ Empathetic tone for anxious users

## 🚦 Status

**Implementation**: ✅ Complete  
**Testing**: ✅ Passed  
**Documentation**: ✅ Complete  
**Production Ready**: ✅ Yes

---

For detailed information, see `PHASE3_COGNITIVE_INSIGHT_SUMMARY.md`
