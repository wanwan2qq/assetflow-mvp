# Phase 4: L3 Vector Memory Implementation Summary

## Overview
Phase 4 implements **L3 Vector Memory** - a long-term unstructured memory layer using pgvector for semantic search and RAG (Retrieval-Augmented Generation). This completes the 4-layer memory architecture:

- **L0 (History)**: Chat message history
- **L1 (Assets)**: Structured asset data (UserAsset, UserProfile)
- **L2 (Cognition)**: Psychological profile and advisor strategy (UserCognition)
- **L3 (Vector Memory)**: Unstructured long-term memories with semantic search

## Architecture

### Memory Hierarchy
```
┌─────────────────────────────────────────────────────────────┐
│ L3: Vector Memory (Long-term Semantic Memory)               │
│ - Unstructured memories (life events, constraints)          │
│ - Semantic search with pgvector                             │
│ - RAG for contextual recall                                 │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│ L2: Cognition (Psychological Profile)                       │
│ - Risk tolerance, decision style                            │
│ - Advisor strategy notes                                    │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│ L1: Assets (Structured Data)                                │
│ - UserAsset, UserProfile                                    │
│ - Collection status tracking                                │
└─────────────────────────────────────────────────────────────┘
                            ↑
┌─────────────────────────────────────────────────────────────┐
│ L0: History (Chat Messages)                                 │
│ - ChatMessage, ChatSession                                  │
│ - Conversation flow                                         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Details

### 1. Infrastructure Setup

#### Docker Compose
- **Updated**: `docker-compose.yml` to use `pgvector/pgvector:pg16` image
- Enables pgvector extension for vector similarity search

#### Dependencies
- **Added**: `langchain-postgres>=0.0.6` - PostgreSQL vector store integration
- **Added**: `pgvector>=0.2.4` - Python client for pgvector

### 2. Database Schema

#### Migration: Enable pgvector Extension
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Migration: Create vector_memory Table
```sql
CREATE TABLE vector_memory (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user(id),
    content TEXT NOT NULL,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB,
    created_at TIMESTAMP NOT NULL,
    
    INDEX ix_vector_memory_user_id (user_id),
    INDEX ix_vector_memory_user_created (user_id, created_at),
    INDEX ix_vector_memory_embedding_cosine USING hnsw (embedding vector_cosine_ops)
);
```

**Key Features:**
- `embedding`: 1536-dimensional vector for OpenAI embeddings
- `metadata`: JSON field for tags, categories, source tracking
- **HNSW Index**: Fast approximate nearest neighbor search using cosine similarity

### 3. Data Model

#### VectorMemory Model (`app/models/memory.py`)
```python
class VectorMemory(SQLModel, table=True):
    id: int | None
    user_id: int  # Foreign key to user
    content: str  # The actual memory text
    embedding: list[float] | None  # 1536-dim vector
    metadata_: dict[str, Any]  # Tags, category, source
    created_at: datetime
```

**Graceful Degradation:**
- Handles missing pgvector gracefully with try/except
- Falls back to text storage if pgvector not available

### 4. Memory Service (`app/services/memory_service.py`)

#### Core Methods

**add_memory(user_id, text, metadata)**
- Generates embedding using OpenAI `text-embedding-3-small`
- Stores memory with vector in database
- Returns created VectorMemory object

**retrieve_relevant(user_id, query_text, limit=3, similarity_threshold=0.7)**
- Generates query embedding
- Performs cosine similarity search: `1 - (embedding <=> query_embedding)`
- Returns top N memories above similarity threshold
- Falls back to keyword search if embeddings unavailable

**get_recent_memories(user_id, limit=10)**
- Returns recent memories in chronological order
- Useful for debugging and user memory management

**delete_memory(memory_id, user_id)**
- Deletes specific memory
- Validates user ownership

#### Fallback Strategy
- **Primary**: Semantic search with pgvector cosine similarity
- **Fallback**: Keyword-based search using PostgreSQL ILIKE
- Ensures functionality even without OpenAI API key

### 5. Integration Points

#### A. InsightService (Write Path)

**Method**: `_extract_and_store_key_memories(user_id, messages)`

Automatically extracts and stores key life events:

| Category | Keywords | Example Memory |
|----------|----------|----------------|
| Health Concern | 生病, 住院, 手术 | "用户提到家人健康问题，可能需要流动性资金" |
| Major Purchase | 买房, 购房, 换房 | "用户计划购买房产，需要大额资金准备" |
| Retirement Planning | 退休, 养老 | "用户关注退休规划，需要长期稳健投资策略" |
| Education Planning | 孩子, 教育, 学费 | "用户关注子女教育，需要预留教育资金" |
| Debt Constraint | 房贷, 负债, 还款 | "用户有房贷压力，需要保守的投资策略" |

**Trigger**: Called during `analyze_user_psychology()` after cognitive analysis

#### B. ChatAgent (Read Path)

**Method**: `_retrieve_relevant_memories(user_id, query_text)`

Retrieves relevant memories for RAG:
- Called in `_prepare_contextual_input()` before generating response
- Injects memories into system prompt context
- Format: `🧠 【RELEVANT MEMORIES】`

**Context Injection Example:**
```
🧠 【RELEVANT MEMORIES】
1. 用户提到母亲生病住院，需要准备医疗费用 (相关度: 0.89)
2. 用户有房贷压力，每月还款2万 (相关度: 0.82)
[重要提示: 这些是用户之前提到的关键信息，请在回复中考虑这些背景。]
```

### 6. RAG Workflow

```
User Message
     ↓
ChatAgent.process_message()
     ↓
_prepare_contextual_input()
     ↓
_retrieve_relevant_memories()  ← L3 Vector Memory (RAG)
     ↓
Generate query embedding
     ↓
Cosine similarity search in pgvector
     ↓
Top 3 relevant memories (similarity > 0.7)
     ↓
Inject into system prompt
     ↓
LLM generates response with memory context
     ↓
Response to user
```

## Usage Examples

### Example 1: Storing a Memory
```python
from app.services.memory_service import get_memory_service

memory_service = get_memory_service()

memory = await memory_service.add_memory(
    user_id=1,
    text="用户提到母亲生病住院，需要准备20万医疗费用",
    metadata={
        "category": "health_concern",
        "tags": ["family", "health", "liquidity"],
        "source": "insight_analysis"
    }
)
```

### Example 2: Retrieving Relevant Memories
```python
memories = await memory_service.retrieve_relevant(
    user_id=1,
    query_text="用户家人健康情况如何？",
    limit=3,
    similarity_threshold=0.7
)

for mem in memories:
    print(f"[{mem['similarity']:.2f}] {mem['content']}")
```

### Example 3: Automatic Extraction (InsightService)
```python
# Automatically triggered during psychological analysis
analysis = await insight_service.analyze_user_psychology(user_id=1)
# Memories are extracted and stored automatically
```

### Example 4: RAG in ChatAgent
```python
# Automatically triggered during chat
async for chunk in chat_agent.process_message(
    message="我想了解一下我的整体财务状况",
    user_id=1
):
    print(chunk, end="")
# Relevant memories are automatically retrieved and injected
```

## Testing

### Test Suite: `test_phase4_vector_memory.py`

**Test 1: Memory Service**
- Add memories with embeddings
- Semantic search retrieval
- Recent memories query

**Test 2: InsightService Integration**
- Automatic memory extraction from conversation
- Key life event detection
- Memory storage validation

**Test 3: ChatAgent RAG**
- Memory retrieval during chat
- Context injection
- Response quality with memory context

**Test 4: Memory Lifecycle**
- Create, retrieve, delete operations
- Verification of CRUD operations

### Running Tests
```bash
cd backend
python test_phase4_vector_memory.py
```

## Configuration

### Environment Variables
```bash
# Required for embeddings
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.deepseek.com  # Optional

# Database (pgvector-enabled)
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
```

### Similarity Threshold Tuning
```python
# In memory_service.py
similarity_threshold=0.7  # Default: 0.7 (70% similarity)

# Adjust based on use case:
# - 0.8-0.9: Very strict, only highly relevant
# - 0.7-0.8: Balanced (recommended)
# - 0.5-0.7: More permissive, broader context
```

## Performance Considerations

### Embedding Generation
- **Model**: `text-embedding-3-small` (1536 dimensions)
- **Cost**: ~$0.00002 per 1K tokens
- **Latency**: ~100-200ms per embedding

### Vector Search
- **Index**: HNSW (Hierarchical Navigable Small World)
- **Search Time**: O(log N) approximate
- **Accuracy**: >95% recall with proper tuning

### Optimization Strategies
1. **Batch Embedding**: Generate embeddings in batches for bulk imports
2. **Caching**: Cache frequently accessed memories in Redis
3. **Lazy Loading**: Only generate embeddings when needed
4. **Threshold Tuning**: Adjust similarity threshold based on use case

## Error Handling

### Graceful Degradation
1. **No OpenAI Key**: Falls back to keyword search
2. **No pgvector**: Stores text without embeddings
3. **Embedding Failure**: Stores memory without vector, logs warning
4. **Search Failure**: Returns empty list, logs error

### Logging
```python
logger.info("Added memory for user {user_id}")
logger.warning("Failed to generate embedding")
logger.error("Error retrieving memories: {error}")
```

## Future Enhancements

### Phase 4.1: Advanced Features
- [ ] Memory summarization (compress old memories)
- [ ] Memory importance scoring (decay over time)
- [ ] Cross-user memory patterns (anonymized)
- [ ] Memory conflict detection

### Phase 4.2: Performance
- [ ] Redis caching for hot memories
- [ ] Batch embedding generation
- [ ] Async background memory extraction
- [ ] Memory pruning strategies

### Phase 4.3: Analytics
- [ ] Memory usage dashboard
- [ ] Embedding quality metrics
- [ ] Search relevance tracking
- [ ] Memory lifecycle analytics

## Migration Guide

### Running Migrations
```bash
cd backend

# Enable pgvector extension
alembic upgrade phase4_pgvector

# Create vector_memory table
alembic upgrade phase4_vector_memory

# Verify
alembic current
```

### Rollback
```bash
# Rollback vector_memory table
alembic downgrade phase4_pgvector

# Rollback pgvector extension
alembic downgrade cc1330024231
```

## Troubleshooting

### Issue: pgvector extension not found
**Solution**: Ensure using `pgvector/pgvector:pg16` Docker image

### Issue: Embedding dimension mismatch
**Solution**: Verify using `text-embedding-3-small` (1536 dims)

### Issue: Slow vector search
**Solution**: Ensure HNSW index is created on embedding column

### Issue: No memories retrieved
**Solution**: 
1. Check similarity threshold (try lowering to 0.5)
2. Verify embeddings are generated
3. Check fallback keyword search

## Summary

Phase 4 successfully implements L3 Vector Memory with:

✅ **Infrastructure**: pgvector-enabled PostgreSQL
✅ **Data Model**: VectorMemory with 1536-dim embeddings
✅ **Service Layer**: MemoryService with semantic search
✅ **Write Integration**: InsightService automatic extraction
✅ **Read Integration**: ChatAgent RAG retrieval
✅ **Testing**: Comprehensive test suite
✅ **Documentation**: Complete implementation guide

**Result**: AssetFlow now has a complete 4-layer memory architecture (L0-L3) enabling long-term contextual understanding and personalized financial advice.
