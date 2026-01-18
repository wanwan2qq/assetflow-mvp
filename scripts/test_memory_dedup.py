"""
Test memory deduplication functionality

This script tests:
1. Current behavior (duplicate creation)
2. Fixed behavior (deduplication)
3. Performance comparison
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import get_db_session
from app.services.memory_service import get_memory_service
from app.models.memory import VectorMemory
from sqlmodel import select


async def cleanup_test_data(test_user_id: int):
    """Clean up test data"""
    try:
        async for session in get_db_session():
            statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
            result = await session.execute(statement)
            test_memories = result.scalars().all()
            
            for mem in test_memories:
                await session.delete(mem)
            await session.commit()
            
            print(f"✓ Cleaned up {len(test_memories)} test memories")
            break
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")


async def test_current_behavior():
    """Test 1: Demonstrate current duplicate creation behavior"""
    
    print("\n" + "="*80)
    print("TEST 1: Current Behavior (Duplicate Creation)")
    print("="*80)
    
    memory_service = get_memory_service()
    test_user_id = 9999  # Test user
    
    try:
        # Clean up first
        await cleanup_test_data(test_user_id)
        
        # Simulate 3 times user mentions "房贷压力"
        print("\n--- Simulating user mentioning '房贷压力' 3 times ---")
        
        for i in range(3):
            print(f"\nAttempt {i+1}: Creating memory...")
            memory = await memory_service.add_memory(
                user_id=test_user_id,
                text="用户有房贷或债务压力，需要保守的投资策略和充足的流动性",
                metadata={
                    "category": "debt_constraint",
                    "tags": ["debt", "conservative"],
                    "source": "test",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            if memory:
                print(f"  ✓ Created memory ID={memory.id}")
            else:
                print(f"  ✗ Failed to create memory")
        
        # Check total count
        print("\n--- Checking database ---")
        async for session in get_db_session():
            statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
            result = await session.execute(statement)
            all_memories = result.scalars().all()
            
            print(f"\nTotal memories in database: {len(all_memories)}")
            
            if len(all_memories) == 3:
                print("⚠️  PROBLEM CONFIRMED: Created 3 duplicate memories!")
                print("\nMemory details:")
                for i, mem in enumerate(all_memories, 1):
                    print(f"  {i}. ID={mem.id}, Category={mem.metadata_.get('category')}")
                    print(f"     Content: {mem.content[:60]}...")
                    print(f"     Created: {mem.created_at}")
                
                return True
            else:
                print(f"✗ Unexpected count: {len(all_memories)} (expected 3)")
                return False
            
            break
            
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dedup_behavior():
    """Test 2: Test deduplication with time window"""
    
    print("\n" + "="*80)
    print("TEST 2: Deduplication Behavior (Time Window)")
    print("="*80)
    
    memory_service = get_memory_service()
    test_user_id = 9998  # Different test user
    
    try:
        # Clean up first
        await cleanup_test_data(test_user_id)
        
        # Check if dedup method exists
        if not hasattr(memory_service, 'add_memory_with_time_window'):
            print("\n⚠️  DEDUP METHOD NOT IMPLEMENTED YET")
            print("Expected method: memory_service.add_memory_with_time_window()")
            print("\nTo fix this, implement the method in backend/app/services/memory_service.py")
            print("See: docs/Memory/MEMORY_DEDUP_QUICK_FIX.md for implementation guide")
            return False
        
        # Test deduplication
        print("\n--- Testing deduplication logic ---")
        
        # First attempt - should create
        print("\nAttempt 1: Creating first memory...")
        memory1 = await memory_service.add_memory_with_time_window(
            user_id=test_user_id,
            text="用户有房贷或债务压力，需要保守的投资策略和充足的流动性",
            metadata={
                "category": "debt_constraint",
                "tags": ["debt", "conservative"],
                "source": "test"
            },
            time_window_hours=24
        )
        
        if memory1:
            print(f"  ✓ Created memory ID={memory1.id}")
        else:
            print(f"  ✗ Failed to create memory")
            return False
        
        # Second attempt - should skip (duplicate)
        print("\nAttempt 2: Trying to create duplicate...")
        memory2 = await memory_service.add_memory_with_time_window(
            user_id=test_user_id,
            text="用户有房贷或债务压力，需要保守的投资策略",
            metadata={
                "category": "debt_constraint",
                "tags": ["debt", "liquidity"],
                "source": "test"
            },
            time_window_hours=24
        )
        
        if memory2 and memory2.id == memory1.id:
            print(f"  ✓ Duplicate prevented: returned existing memory ID={memory2.id}")
        else:
            print(f"  ✗ Duplicate not prevented: created new memory ID={memory2.id if memory2 else 'None'}")
            return False
        
        # Third attempt - different category, should create
        print("\nAttempt 3: Creating different category...")
        memory3 = await memory_service.add_memory_with_time_window(
            user_id=test_user_id,
            text="用户计划3年内购买学区房，预算500万",
            metadata={
                "category": "major_purchase",
                "tags": ["real_estate", "planning"],
                "source": "test"
            },
            time_window_hours=24
        )
        
        if memory3 and memory3.id != memory1.id:
            print(f"  ✓ Created different category memory ID={memory3.id}")
        else:
            print(f"  ✗ Failed to create different category memory")
            return False
        
        # Verify final count
        print("\n--- Verifying database state ---")
        async for session in get_db_session():
            statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
            result = await session.execute(statement)
            all_memories = result.scalars().all()
            
            print(f"\nTotal memories in database: {len(all_memories)}")
            
            if len(all_memories) == 2:
                print("✓ DEDUPLICATION WORKING: Only 2 unique memories created!")
                print("\nMemory details:")
                for i, mem in enumerate(all_memories, 1):
                    print(f"  {i}. ID={mem.id}, Category={mem.metadata_.get('category')}")
                    print(f"     Content: {mem.content[:60]}...")
                
                return True
            else:
                print(f"✗ Unexpected count: {len(all_memories)} (expected 2)")
                return False
            
            break
            
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_comparison():
    """Test 3: Compare performance of duplicate vs dedup"""
    
    print("\n" + "="*80)
    print("TEST 3: Performance Comparison")
    print("="*80)
    
    memory_service = get_memory_service()
    test_user_id = 9997
    
    try:
        await cleanup_test_data(test_user_id)
        
        # Test 1: Without dedup (current behavior)
        print("\n--- Test A: Without deduplication ---")
        start_time = datetime.utcnow()
        
        for i in range(10):
            await memory_service.add_memory(
                user_id=test_user_id,
                text=f"测试记忆 {i}",
                metadata={"category": "test", "source": "perf_test"}
            )
        
        time_without_dedup = (datetime.utcnow() - start_time).total_seconds()
        
        async for session in get_db_session():
            statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
            result = await session.execute(statement)
            count_without_dedup = len(result.scalars().all())
            break
        
        print(f"  Time: {time_without_dedup:.3f}s")
        print(f"  Records created: {count_without_dedup}")
        print(f"  Avg time per record: {time_without_dedup/10*1000:.1f}ms")
        
        # Clean up
        await cleanup_test_data(test_user_id)
        
        # Test 2: With dedup (if implemented)
        if hasattr(memory_service, 'add_memory_with_time_window'):
            print("\n--- Test B: With deduplication ---")
            start_time = datetime.utcnow()
            
            for i in range(10):
                await memory_service.add_memory_with_time_window(
                    user_id=test_user_id,
                    text=f"测试记忆 {i % 3}",  # Only 3 unique categories
                    metadata={"category": f"test_{i % 3}", "source": "perf_test"},
                    time_window_hours=24
                )
            
            time_with_dedup = (datetime.utcnow() - start_time).total_seconds()
            
            async for session in get_db_session():
                statement = select(VectorMemory).where(VectorMemory.user_id == test_user_id)
                result = await session.execute(statement)
                count_with_dedup = len(result.scalars().all())
                break
            
            print(f"  Time: {time_with_dedup:.3f}s")
            print(f"  Records created: {count_with_dedup}")
            print(f"  Avg time per record: {time_with_dedup/10*1000:.1f}ms")
            
            # Comparison
            print("\n--- Performance Comparison ---")
            print(f"  Storage reduction: {(1 - count_with_dedup/count_without_dedup)*100:.1f}%")
            print(f"  Time overhead: {(time_with_dedup/time_without_dedup - 1)*100:.1f}%")
            
            if count_with_dedup < count_without_dedup:
                print("  ✓ Deduplication is working and reducing storage!")
            
            if time_with_dedup < time_without_dedup * 1.2:
                print("  ✓ Performance overhead is acceptable (<20%)")
        else:
            print("\n⚠️  Dedup method not implemented, skipping comparison")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await cleanup_test_data(test_user_id)


async def main():
    """Run all tests"""
    
    print("\n" + "="*80)
    print("MEMORY DEDUPLICATION TEST SUITE")
    print("="*80)
    print("\nThis test suite will:")
    print("1. Demonstrate the current duplicate creation problem")
    print("2. Test the deduplication fix (if implemented)")
    print("3. Compare performance")
    print("\n" + "="*80)
    
    results = []
    
    # Test 1: Current behavior
    try:
        result1 = await test_current_behavior()
        results.append(("Current Behavior Test", result1))
    except Exception as e:
        print(f"\n✗ Test 1 failed: {e}")
        results.append(("Current Behavior Test", False))
    
    # Test 2: Dedup behavior
    try:
        result2 = await test_dedup_behavior()
        results.append(("Deduplication Test", result2))
    except Exception as e:
        print(f"\n✗ Test 2 failed: {e}")
        results.append(("Deduplication Test", False))
    
    # Test 3: Performance
    try:
        result3 = await test_performance_comparison()
        results.append(("Performance Test", result3))
    except Exception as e:
        print(f"\n✗ Test 3 failed: {e}")
        results.append(("Performance Test", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests PASSED!")
    elif passed > 0:
        print("\n⚠️  Some tests FAILED - see details above")
    else:
        print("\n❌ All tests FAILED - implementation needed")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    
    if not results[1][1]:  # Dedup test failed
        print("\n1. Implement deduplication method:")
        print("   File: backend/app/services/memory_service.py")
        print("   Method: add_memory_with_time_window()")
        print("   Guide: docs/Memory/MEMORY_DEDUP_QUICK_FIX.md")
        print("\n2. Update insight_service.py to use new method")
        print("\n3. Re-run this test to verify")
    else:
        print("\n✓ Deduplication is working!")
        print("\nOptional improvements:")
        print("1. Implement similarity-based deduplication")
        print("2. Add monitoring and metrics")
        print("3. Clean up historical duplicate data")
    
    print("\n" + "="*80)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
