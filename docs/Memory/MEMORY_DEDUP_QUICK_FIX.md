# 长期记忆去重 - 快速修复指南

## 🎯 问题概述

**现象**: 用户多次提到相同信息时，系统会创建多条相似的长期记忆记录

**影响**: 数据冗余30-50%，检索效率下降20-30%

**优先级**: P2 - 建议下个迭代修复

---

## ⚡ 快速修复方案（推荐）

### 修改1: 添加去重方法到 `memory_service.py`

**文件**: `backend/app/services/memory_service.py`

在 `MemoryService` 类中添加以下方法：

```python
async def add_memory_with_time_window(
    self, 
    user_id: int, 
    text: str,
    metadata: dict[str, Any] | None = None,
    time_window_hours: int = 24
) -> VectorMemory | None:
    """
    Add memory with time-window deduplication
    Prevents duplicate memories of same category within 24 hours
    """
    try:
        category = metadata.get("category") if metadata else None
        
        if category:
            # Check for recent memory of same category
            recent_memory = await self._get_recent_memory_by_category(
                user_id=user_id,
                category=category,
                time_window_hours=time_window_hours
            )
            
            if recent_memory:
                logger.info(
                    f"Skipping duplicate memory: category={category}, "
                    f"within {time_window_hours}h window"
                )
                return recent_memory
        
        # No duplicate found, create new memory
        return await self.add_memory(user_id, text, metadata)
        
    except Exception as e:
        logger.error(f"Error in add_memory_with_time_window: {e}")
        return await self.add_memory(user_id, text, metadata)

async def _get_recent_memory_by_category(
    self,
    user_id: int,
    category: str,
    time_window_hours: int
) -> VectorMemory | None:
    """Get most recent memory of specific category within time window"""
    try:
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        async for session in get_db_session():
            statement = (
                select(VectorMemory)
                .where(VectorMemory.user_id == user_id)
                .where(VectorMemory.created_at >= cutoff_time)
                .where(VectorMemory.metadata_["category"].astext == category)
                .order_by(VectorMemory.created_at.desc())
                .limit(1)
            )
            
            result = await session.execute(statement)
            return result.scalar_one_or_none()
            
    except Exception as e:
        logger.error(f"Error getting recent memory by category: {e}")
        return None
```

### 修改2: 更新调用点 `insight_service.py`

**文件**: `backend/app/services/insight_service.py`

找到 `_extract_and_store_key_memories` 方法（约第391行），修改存储逻辑：

```python
async def _extract_and_store_key_memories(self, user_id: int, messages: list[ChatMessage]) -> None:
    """
    Phase 4: Extract key life events using LLM Semantic Analysis
    Store them in L3 Vector Memory for long-term recall
    """
    try:
        from app.services.memory_service import get_memory_service
        
        memory_service = get_memory_service()
        
        # ... 现有的提取逻辑保持不变 ...
        
        # ✅ 修改: 使用带去重的存储方法
        for mem in memories:
            await memory_service.add_memory_with_time_window(  # 改用去重方法
                user_id=user_id,
                text=mem["content"],
                metadata={
                    "category": mem.get("category", "general"),
                    "tags": mem.get("tags", []),
                    "source": "llm_insight_extraction",
                    "timestamp": datetime.utcnow().isoformat()
                },
                time_window_hours=24  # 24小时内同类别不重复
            )
        
        if memories:
            logger.info(f"Extracted and stored {len(memories)} memories for user {user_id} (with dedup)")
        
    except Exception as e:
        logger.error(f"Error extracting and storing key memories: {e}")
```

---

## 🧪 测试验证

### 测试脚本

创建 `scripts/test_memory_dedup.py`:

```python
"""
Test memory deduplication functionality
"""

import asyncio
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.services.memory_service import get_memory_service
from app.models.memory import VectorMemory
from sqlmodel import select


async def test_memory_dedup():
    """Test that duplicate memories are prevented"""
    
    print("\n" + "="*80)
    print("TEST: Memory Deduplication")
    print("="*80)
    
    memory_service = get_memory_service()
    test_user_id = 999  # Test user
    
    try:
        # Clean up test data
        async for session in get_db_session():
            statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
            result = await session.execute(statement)
            test_memories = result.scalars().all()
            
            for mem in test_memories:
                await session.delete(mem)
            await session.commit()
            print(f"✓ Cleaned up {len(test_memories)} test memories")
            break
        
        # Test 1: Create first memory
        print("\n--- Test 1: Create first memory ---")
        memory1 = await memory_service.add_memory_with_time_window(
            user_id=test_user_id,
            text="用户有房贷压力，需要保守的投资策略",
            metadata={
                "category": "debt_constraint",
                "tags": ["debt", "conservative"]
            }
        )
        
        if memory1:
            print(f"✓ Created memory 1: ID={memory1.id}")
        else:
            print("✗ Failed to create memory 1")
            return False
        
        # Test 2: Try to create duplicate (should be prevented)
        print("\n--- Test 2: Try to create duplicate (should skip) ---")
        memory2 = await memory_service.add_memory_with_time_window(
            user_id=test_user_id,
            text="用户有房贷压力，需要保守的投资策略和充足的流动性",
            metadata={
                "category": "debt_constraint",
                "tags": ["debt", "liquidity"]
            }
        )
        
        if memory2 and memory2.id == memory1.id:
            print(f"✓ Duplicate prevented: returned existing memory ID={memory2.id}")
        else:
            print(f"✗ Duplicate not prevented: created new memory ID={memory2.id if memory2 else 'None'}")
            return False
        
        # Test 3: Create different category (should succeed)
        print("\n--- Test 3: Create different category (should succeed) ---")
        memory3 = await memory_service.add_memory_with_time_window(
            user_id=test_user_id,
            text="用户计划3年内购买学区房",
            metadata={
                "category": "major_purchase",
                "tags": ["real_estate", "planning"]
            }
        )
        
        if memory3 and memory3.id != memory1.id:
            print(f"✓ Created different category memory: ID={memory3.id}")
        else:
            print("✗ Failed to create different category memory")
            return False
        
        # Test 4: Verify total count
        print("\n--- Test 4: Verify total memory count ---")
        async for session in get_db_session():
            statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
            result = await session.execute(statement)
            all_memories = result.scalars().all()
            
            if len(all_memories) == 2:
                print(f"✓ Correct memory count: {len(all_memories)} (expected 2)")
                for mem in all_memories:
                    print(f"  - {mem.metadata_.get('category')}: {mem.content[:50]}...")
            else:
                print(f"✗ Incorrect memory count: {len(all_memories)} (expected 2)")
                return False
            
            break
        
        print("\n" + "="*80)
        print("🎉 All deduplication tests PASSED!")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_memory_dedup())
    exit(0 if result else 1)
```

### 运行测试

```bash
cd backend
python scripts/test_memory_dedup.py
```

**预期输出**:
```
================================================================================
TEST: Memory Deduplication
================================================================================
✓ Cleaned up 0 test memories

--- Test 1: Create first memory ---
✓ Created memory 1: ID=123

--- Test 2: Try to create duplicate (should skip) ---
✓ Duplicate prevented: returned existing memory ID=123

--- Test 3: Create different category (should succeed) ---
✓ Created different category memory: ID=124

--- Test 4: Verify total memory count ---
✓ Correct memory count: 2 (expected 2)
  - debt_constraint: 用户有房贷压力，需要保守的投资策略...
  - major_purchase: 用户计划3年内购买学区房...

================================================================================
🎉 All deduplication tests PASSED!
================================================================================
```

---

## 🗑️ 清理历史重复数据（可选）

### 备份数据

```sql
-- 创建备份表
CREATE TABLE vector_memory_backup_20260116 AS 
SELECT * FROM vector_memory;

-- 验证备份
SELECT COUNT(*) FROM vector_memory_backup_20260116;
```

### 识别重复记录

```sql
-- 查看重复情况
SELECT 
    user_id,
    metadata->>'category' as category,
    COUNT(*) as count,
    MIN(created_at) as first_created,
    MAX(created_at) as last_created
FROM vector_memory
GROUP BY user_id, metadata->>'category'
HAVING COUNT(*) > 1
ORDER BY count DESC;
```

### 删除重复记录

```sql
-- 删除旧的重复记录（保留最新的）
DELETE FROM vector_memory
WHERE id IN (
    SELECT id
    FROM (
        SELECT 
            id,
            ROW_NUMBER() OVER (
                PARTITION BY user_id, metadata->>'category'
                ORDER BY created_at DESC
            ) as rn
        FROM vector_memory
    ) t
    WHERE rn > 1
);

-- 查看删除结果
SELECT 
    COUNT(*) as remaining_memories,
    COUNT(DISTINCT user_id) as unique_users
FROM vector_memory;
```

---

## 📊 监控指标

### 添加日志监控

在 `memory_service.py` 中添加统计日志：

```python
# 在 add_memory_with_time_window 方法中
if recent_memory:
    logger.info(
        f"DEDUP_STATS: user={user_id}, category={category}, "
        f"action=skipped, reason=duplicate_within_{time_window_hours}h"
    )
else:
    logger.info(
        f"DEDUP_STATS: user={user_id}, category={category}, "
        f"action=created, reason=no_recent_duplicate"
    )
```

### 查询统计

```sql
-- 每日去重统计
SELECT 
    DATE(created_at) as date,
    metadata->>'category' as category,
    COUNT(*) as memory_count
FROM vector_memory
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at), metadata->>'category'
ORDER BY date DESC, memory_count DESC;
```

---

## ✅ 验收标准

修复完成后，应满足以下标准：

1. **功能验证**
   - ✅ 24小时内同类别记忆不重复创建
   - ✅ 不同类别记忆正常创建
   - ✅ 超过24小时后可以创建新记忆

2. **性能验证**
   - ✅ 去重检查耗时 < 10ms
   - ✅ 不影响正常记忆创建流程
   - ✅ 数据库查询效率正常

3. **数据验证**
   - ✅ 重复记录率 < 5%
   - ✅ 无数据丢失
   - ✅ 元数据完整

---

## 🚀 部署步骤

1. **开发环境测试**
   ```bash
   # 运行测试
   python scripts/test_memory_dedup.py
   
   # 验证通过后提交代码
   git add backend/app/services/memory_service.py
   git add backend/app/services/insight_service.py
   git commit -m "feat: add memory deduplication with time window"
   ```

2. **测试环境部署**
   ```bash
   # 部署到测试环境
   git push origin feature/memory-dedup
   
   # 观察日志
   tail -f backend/logs/app.log | grep "DEDUP_STATS"
   ```

3. **生产环境部署**
   ```bash
   # 合并到主分支
   git checkout main
   git merge feature/memory-dedup
   
   # 部署
   git push origin main
   
   # 监控24小时
   ```

---

## 📞 问题排查

### 问题1: 去重不生效

**症状**: 仍然看到重复记录

**排查**:
```python
# 检查日志
grep "DEDUP_STATS" backend/logs/app.log

# 检查数据库
SELECT * FROM vector_memory 
WHERE user_id = <test_user_id>
ORDER BY created_at DESC
LIMIT 10;
```

**可能原因**:
- category字段为空或不一致
- 时间窗口配置过短
- 代码未正确部署

### 问题2: 性能下降

**症状**: 记忆创建变慢

**排查**:
```sql
-- 检查索引
SELECT * FROM pg_indexes 
WHERE tablename = 'vector_memory';

-- 添加索引（如果缺失）
CREATE INDEX IF NOT EXISTS idx_vector_memory_category 
ON vector_memory ((metadata_->>'category'));

CREATE INDEX IF NOT EXISTS idx_vector_memory_created_at 
ON vector_memory (created_at);
```

---

## 📚 相关文档

- [完整分析报告](./LONG_TERM_MEMORY_DUPLICATION_ANALYSIS.md)
- [Phase 4 向量记忆文档](./PHASE4_VECTOR_MEMORY_SUMMARY.md)
- [LLM响应处理分析](../Important/AI_LLM_RESPONSE_PROCESSING_ANALYSIS.md)

---

**最后更新**: 2026-01-16  
**预计工作量**: 2-4小时  
**风险等级**: 低
