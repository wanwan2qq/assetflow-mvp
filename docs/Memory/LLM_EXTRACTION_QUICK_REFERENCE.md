# LLM Extraction Quick Reference

## Usage

### Async (Recommended)
```python
from app.services.information_extraction import extract_information

result = await extract_information(
    user_message="我有一套北京的房子，120平米，价值500万",
    current_history=[
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "您好！"}
    ]
)

# Result format
{
    "assets": [
        {
            "type": "real_estate",
            "amount": 5000000,
            "currency": "CNY",
            "name": "房子",
            "location": "北京",
            "area": 120.0
        }
    ],
    "goals": [],
    "risk_profile": {},
    "completeness_update": {"real_estate": True},
    "intent": "new_info"  # or "correction"
}
```

### Sync (Backward Compatible)
```python
from app.services.information_extraction import extract_information_from_conversation

assets, profile, validation = extract_information_from_conversation(
    "我有50万现金"
)

# Returns tuple of (assets, profile, validation)
```

## Intent Detection

### New Information
```python
"我有一套房子" → intent: "new_info"
"现金存款50万" → intent: "new_info"
```

### Corrections
```python
"不是，是120平米" → intent: "correction"
"不对，应该是500万" → intent: "correction"
"其实是200平" → intent: "correction"
```

## Fuzzy Numbers

```python
"大概50万" → 500,000
"about 500k" → 500,000
"差不多300万" → 3,000,000
"大约100万左右" → 1,000,000
```

## Asset Types

```python
# Chinese → English mapping
"房产/房子/住房" → "real_estate"
"现金/存款/银行" → "cash"
"股票/基金/投资" → "investment"
"保险" → "insurance"
"贷款/房贷/债务" → "liability"
```

## Configuration

```bash
# .env
OPENAI_API_KEY=sk-your-deepseek-key
OPENAI_API_BASE=https://api.deepseek.com/v1
```

## Testing

```bash
# Run all tests
python scripts/test_llm_extraction.py
python scripts/test_extraction_integration.py
python scripts/verify_llm_extraction_refactor.py
```

## Troubleshooting

### No API Key
- System automatically falls back to keyword matching
- Set `OPENAI_API_KEY` in `.env` for full functionality

### Extraction Not Working
1. Check API key is valid
2. Verify `OPENAI_API_BASE` is set correctly
3. Check logs for LLM errors
4. Test with `scripts/test_llm_extraction.py`

### Database Issues
```bash
# Apply migration
cd backend
source .venv/bin/activate
python -m alembic upgrade head
```

## Performance

- **Extraction Time:** ~1-2 seconds (LLM API call)
- **Accuracy:** 85%+ confidence
- **Fallback:** <100ms (keyword matching)

## Model Field

```python
class UserAsset(SQLModel, table=True):
    is_confirmed: bool = Field(default=False)
    # Tracks if data came from explicit user input
```

## Future Enhancements

1. Use `is_confirmed` for correction logic
2. Add confidence thresholds
3. Implement multi-turn corrections
4. Add extraction analytics
