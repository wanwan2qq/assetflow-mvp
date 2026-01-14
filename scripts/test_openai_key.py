"""
Test OpenAI API Key
Verifies that the OpenAI API key is valid and can generate embeddings
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings


async def test_openai_key():
    """Test OpenAI API key for embeddings"""
    print("\n" + "="*80)
    print("🔑 OPENAI API KEY VERIFICATION")
    print("="*80)
    
    # 1. Check configuration
    print("\n1️⃣ Checking configuration...")
    print(f"   OPENAI_API_KEY: {settings.OPENAI_API_KEY[:20]}...{settings.OPENAI_API_KEY[-10:]}")
    print(f"   OPENAI_API_BASE: {settings.OPENAI_API_BASE}")
    
    if not settings.OPENAI_API_KEY:
        print("   ❌ OPENAI_API_KEY is not set")
        return False
    
    if settings.OPENAI_API_KEY.startswith("sk-mock"):
        print("   ⚠️ Using mock API key")
        return False
    
    print("   ✅ API key is configured")
    
    # 2. Test embedding generation
    print("\n2️⃣ Testing embedding generation...")
    try:
        from langchain_openai import OpenAIEmbeddings
        
        embedding_kwargs = {
            "model": "text-embedding-3-small",
            "api_key": settings.OPENAI_API_KEY,
        }
        
        if settings.OPENAI_API_BASE:
            embedding_kwargs["base_url"] = settings.OPENAI_API_BASE
        
        embeddings = OpenAIEmbeddings(**embedding_kwargs)
        
        # Test with a simple text
        test_text = "这是一个测试文本，用于验证 OpenAI embedding API"
        print(f"   Testing with: '{test_text}'")
        
        embedding = await embeddings.aembed_query(test_text)
        
        print(f"   ✅ Embedding generated successfully")
        print(f"   ✅ Embedding dimensions: {len(embedding)}")
        print(f"   ✅ First 5 values: {embedding[:5]}")
        
        if len(embedding) != 1536:
            print(f"   ⚠️ Warning: Expected 1536 dimensions, got {len(embedding)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Embedding generation failed: {e}")
        
        # Check for common errors
        error_str = str(e)
        if "401" in error_str or "Unauthorized" in error_str:
            print("   💡 Hint: API key is invalid or expired")
        elif "404" in error_str or "Not Found" in error_str:
            print("   💡 Hint: API endpoint does not support embeddings")
        elif "429" in error_str or "Rate limit" in error_str:
            print("   💡 Hint: Rate limit exceeded, try again later")
        elif "quota" in error_str.lower():
            print("   💡 Hint: API quota exceeded, check your OpenAI account")
        
        return False
    
    # 3. Test with memory service
    print("\n3️⃣ Testing with MemoryService...")
    try:
        from app.services.memory_service import get_memory_service
        
        memory_service = get_memory_service()
        
        # Test embedding generation through memory service
        embedding = await memory_service._generate_embedding("测试记忆内容")
        
        if embedding:
            print(f"   ✅ MemoryService can generate embeddings")
            print(f"   ✅ Embedding dimensions: {len(embedding)}")
        else:
            print(f"   ❌ MemoryService failed to generate embedding")
            return False
        
    except Exception as e:
        print(f"   ❌ MemoryService test failed: {e}")
        return False
    
    # 4. Test actual memory storage with embedding
    print("\n4️⃣ Testing memory storage with embedding...")
    try:
        from app.models.user import User
        from app.core.database import get_db_session
        from sqlmodel import select
        
        test_user_id = 1000
        
        # Create test user if not exists
        async for session in get_db_session():
            result = await session.execute(select(User).where(User.id == test_user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    id=test_user_id,
                    phone="+8613800139000",
                    hashed_password="test_hash",
                    is_active=True
                )
                session.add(user)
                await session.commit()
            break
        
        # Add memory with embedding
        memory = await memory_service.add_memory(
            user_id=test_user_id,
            text="OpenAI API 测试：用户关注投资组合优化和风险管理",
            metadata={"category": "test", "tags": ["openai_test"]}
        )
        
        if memory and memory.embedding:
            print(f"   ✅ Memory stored with embedding (ID: {memory.id})")
            print(f"   ✅ Embedding dimensions: {len(memory.embedding)}")
        elif memory:
            print(f"   ⚠️ Memory stored but without embedding")
            return False
        else:
            print(f"   ❌ Failed to store memory")
            return False
        
    except Exception as e:
        print(f"   ❌ Memory storage test failed: {e}")
        return False
    
    # 5. Test semantic search
    print("\n5️⃣ Testing semantic search...")
    try:
        results = await memory_service.retrieve_relevant(
            user_id=test_user_id,
            query_text="投资风险",
            limit=3,
            similarity_threshold=0.5
        )
        
        if results:
            print(f"   ✅ Semantic search returned {len(results)} results")
            for i, result in enumerate(results, 1):
                print(f"      {i}. [{result['similarity']:.3f}] {result['content'][:50]}...")
        else:
            print(f"   ⚠️ No results found (may need more test data)")
        
    except Exception as e:
        print(f"   ❌ Semantic search test failed: {e}")
        return False
    
    # Summary
    print("\n" + "="*80)
    print("📊 VERIFICATION SUMMARY")
    print("="*80)
    print("✅ API key configuration: OK")
    print("✅ Embedding generation: OK")
    print("✅ MemoryService integration: OK")
    print("✅ Memory storage with embedding: OK")
    print("✅ Semantic search: OK")
    print("\n🎉 OpenAI API key is working correctly!")
    print("="*80)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_openai_key())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
