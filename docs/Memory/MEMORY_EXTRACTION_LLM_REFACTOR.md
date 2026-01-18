# Memory Extraction LLM Refactor

## Overview
Refactored `_extract_and_store_key_memories` in `backend/app/services/insight_service.py` to use LLM-based semantic extraction instead of hardcoded keyword matching.

## Changes Made

### 1. Main Method Refactor
- **Location**: Line ~391
- **Changes**:
  - Removed hardcoded keyword checks and manual `key_events` construction
  - Added intelligent routing: LLM extraction when available, keyword fallback otherwise
  - Improved metadata tracking with `source` field indicating extraction method

### 2. New LLM Extraction Method
- **Method**: `_extract_memories_with_llm(conversation_text: str)`
- **Features**:
  - Comprehensive system prompt defining 8 memory categories
  - Structured JSON output format with content, category, and tags
  - Robust JSON parsing (handles markdown code blocks)
  - Validation of response structure and required fields
  - Detailed error handling and logging

### 3. Fallback Method
- **Method**: `_extract_memories_fallback(conversation_text: str)`
- **Purpose**: Maintains original keyword-based logic for development/testing
- **Use Case**: When no valid OpenAI API key is available

## Memory Categories Supported

1. **health_concern**: Health-related events
2. **major_purchase**: Major purchase plans
3. **retirement_planning**: Retirement planning
4. **education_planning**: Education planning
5. **debt_constraint**: Debt constraints
6. **career_change**: Career changes
7. **family_change**: Family changes
8. **investment_experience**: Investment experiences

## Benefits

1. **Semantic Understanding**: LLM can understand context and nuance beyond keywords
2. **Flexible Extraction**: Captures specific details (amounts, timelines, people)
3. **Reduced False Positives**: More accurate than keyword matching
4. **Graceful Degradation**: Falls back to keyword matching when LLM unavailable
5. **Better Metadata**: Richer categorization and tagging

## Technical Details

- **Async/Await**: Maintains asynchronous nature
- **Error Handling**: Comprehensive try-catch blocks with logging
- **JSON Parsing**: Handles markdown code blocks and malformed responses
- **Validation**: Ensures all memories have required fields before storage
- **Logging**: Detailed logging for debugging and monitoring

## Testing Recommendations

1. Test with real user conversations containing life events
2. Verify LLM extraction accuracy vs keyword fallback
3. Monitor extraction performance and token usage
4. Validate memory storage in vector database
5. Test edge cases (empty conversations, malformed LLM responses)
