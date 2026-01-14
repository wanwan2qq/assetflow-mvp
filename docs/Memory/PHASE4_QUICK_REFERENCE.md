# Phase 4: L3 Vector Memory - Quick Reference

## 🎯 What is L3 Vector Memory?

Long-term unstructured memory storage with semantic search capabilities. Stores life events, constraints, and context that don't fit into L1 (Assets) or L2 (Cognition).

## 🏗️ Architecture

```
L3 (Vector Memory) ← Unstructured long-term memories
L2 (Cognition)     ← Psychological profile
L1 (Assets)        ← Structured asset data
L0 (History)       ← Chat messages
```

## 📦 Key Components

### 1. VectorMemory Model
```python
from app.models.memory import VectorMemory

# Fields:
# - id: int
# - user_id: int
# - content: str (memory text)
# - embedding: list[float] (1536-dim vector)
# - metadata_: dict (tags, category, source)
# - created_at: datetime
```

### 2. MemoryService
```python
from app.services.memory_service import get_memory_service

memory_service = get_memory_service()

# Add memory
await memory_service.add_memory(
    user_id=1,
    text="用户提到母亲生病住院",
    metadata={"category": "health_concern"}
)

# Retrieve relevant
memories = await memory_service.retrieve_relevant(
    user_id=1,
    query_text="用户家人健康情况？",
    limit=3,
    similarity_threshold=0.7
)

# Get recent
recent = await memory_service.get_recent_memories(user_id=1, limit=10)

# Delete
await memory_service.delete_memory(memory_id=123, user_id=1)
```

### 3. Integration Points

#### Write Path (InsightService)
```python
# Automatic extraction during psychological analysis
await insight_service.analyze_user_psychology(user_id=1)
# → Extracts key life events
# → Stores in vector memory
```

#### Read Path (ChatAgent)
```python
# Automatic retrieval during chat
async for chunk in chat_agent.process_message(message, user_id):
    print(chunk)
# → Retrieves relevant memories
# → Injects into context
# → LLM generates response
```

## 🔧 Setup

### 1. Docker
```yaml
# docker-compose.yml
postgres:
  image: pgvector/pgvector:pg16
```

### 2. Dependencies
```bash
pip install langchain-postgres pgvector
```

### 3. Migrations
```bash
alembic upgrade phase4_pgvector      # Enable extension
alembic upgrade phase4_vector_memory # Create table
```

### 4. Environment
```bash
OPENAI_API_KEY=sk-...  # For embeddings
```

## 📊 Memory Categories

| Category | Keywords | Use Case |
|----------|----------|----------|
| health_concern | 生病, 住院, 手术 | Medical expenses, liquidity needs |
| major_purchase | 买房, 购房, 换房 | Large capital requirements |
| retirement_planning | 退休, 养老 | Long-term conservative strategy |
| education_planning | 孩子, 教育, 学费 | Education fund allocation |
| debt_constraint | 房贷, 负债, 还款 | Conservative risk profile |

## 🧪 Testing

```bash
cd backend
python test_phase4_vector_memory.py
```

**Tests:**
1. Memory Service (add, retrieve, search)
2. InsightService Integration (auto-extraction)
3. ChatAgent RAG (context injection)
4. Memory Lifecycle (CRUD)

## 🎨 RAG Context Format

```
🧠 【RELEVANT MEMORIES】
1. 用户提到母亲生病住院，需要准备医疗费用 (相关度: 0.89)
2. 用户有房贷压力，每月还款2万 (相关度: 0.82)
3. 用户计划2年后购买学区房 (相关度: 0.76)
[重要提示: 这些是用户之前提到的关键信息，请在回复中考虑这些背景。]
```

## ⚙️ Configuration

### Similarity Threshold
```python
# Default: 0.7 (70% similarity)
similarity_threshold=0.7

# Tuning:
# 0.8-0.9: Very strict
# 0.7-0.8: Balanced (recommended)
# 0.5-0.7: More permissive
```

### Embedding Model
```python
# OpenAI text-embedding-3-small
# - Dimensions: 1536
# - Cost: ~$0.00002 per 1K tokens
# - Latency: ~100-200ms
```

## 🚨 Error Handling

### Graceful Degradation
- **No OpenAI Key** → Keyword search fallback
- **No pgvector** → Text storage only
- **Embedding Failure** → Store without vector
- **Search Failure** → Return empty list

## 📈 Performance

### Vector Search
- **Index**: HNSW (fast approximate search)
- **Complexity**: O(log N)
- **Accuracy**: >95% recall

### Optimization
1. Batch embeddings for bulk imports
2. Cache hot memories in Redis
3. Adjust similarity threshold
4. Prune old low-importance memories

## 🔍 Debugging

### Check Memories
```python
# Get recent memories
memories = await memory_service.get_recent_memories(user_id=1, limit=10)
for mem in memories:
    print(f"{mem.id}: {mem.content[:50]}...")
```

### Test Semantic Search
```python
# Test query
memories = await memory_service.retrieve_relevant(
    user_id=1,
    query_text="测试查询",
    limit=5,
    similarity_threshold=0.5  # Lower threshold for testing
)
print(f"Found {len(memories)} memories")
```

### Check Embeddings
```python
# Verify embedding generation
embedding = await memory_service._generate_embedding("测试文本")
print(f"Embedding dimensions: {len(embedding) if embedding else 'None'}")
```

## 📚 API Reference

### MemoryService Methods

```python
# Add memory
add_memory(user_id: int, text: str, metadata: dict | None) -> VectorMemory | None

# Retrieve relevant (semantic search)
retrieve_relevant(
    user_id: int, 
    query_text: str, 
    limit: int = 3,
    similarity_threshold: float = 0.7
) -> list[dict]

# Get recent (chronological)
get_recent_memories(user_id: int, limit: int = 10) -> list[VectorMemory]

# Delete memory
delete_memory(memory_id: int, user_id: int) -> bool
```

### InsightService Integration

```python
# Automatic memory extraction
_extract_and_store_key_memories(
    user_id: int, 
    messages: list[ChatMessage]
) -> None
```

### ChatAgent Integration

```python
# Automatic memory retrieval
_retrieve_relevant_memories(
    user_id: int, 
    query_text: str
) -> list[dict]
```

## 🎯 Use Cases

### 1. Long-term Context Recall
**Scenario**: User mentioned family health issue 3 months ago
**Solution**: Vector memory retrieves this context when discussing liquidity needs

### 2. Constraint Awareness
**Scenario**: User has high debt burden
**Solution**: Memory informs conservative investment recommendations

### 3. Goal Tracking
**Scenario**: User planning major purchase in 2 years
**Solution**: Memory guides asset allocation timeline

### 4. Personalized Advice
**Scenario**: User's risk tolerance changed after market volatility
**Solution**: Memory tracks sentiment evolution over time

## 🔗 Related Documentation

- [PHASE4_VECTOR_MEMORY_SUMMARY.md](./PHASE4_VECTOR_MEMORY_SUMMARY.md) - Complete implementation guide
- [PHASE3_QUICK_REFERENCE.md](./PHASE3_QUICK_REFERENCE.md) - L2 Cognition layer
- [PHASE2_IMPLEMENTATION_SUMMARY.md](./PHASE2_IMPLEMENTATION_SUMMARY.md) - L1 Asset extraction

## 💡 Tips

1. **Start with default threshold (0.7)** - Adjust based on retrieval quality
2. **Use metadata tags** - Helps with filtering and analytics
3. **Monitor embedding costs** - Batch operations when possible
4. **Test fallback search** - Ensure functionality without OpenAI key
5. **Prune old memories** - Implement lifecycle management for production

## ✅ Checklist

- [ ] Docker using pgvector image
- [ ] Dependencies installed (langchain-postgres, pgvector)
- [ ] Migrations run (phase4_pgvector, phase4_vector_memory)
- [ ] OPENAI_API_KEY configured
- [ ] Tests passing (test_phase4_vector_memory.py)
- [ ] Memory extraction working (InsightService)
- [ ] RAG retrieval working (ChatAgent)

---

**Phase 4 Status**: ✅ Complete

**Next Steps**: Test in production, monitor performance, tune similarity threshold
