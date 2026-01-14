"""
Fix vector_memory table dimension from 1536 to 1024
This script drops and recreates the vector_memory table with correct dimensions
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.core.database import get_db_session


async def fix_vector_dimension():
    """Drop and recreate vector_memory table with 1024 dimensions"""
    
    print("🔧 Fixing vector_memory table dimension...")
    print("   Old: 1536 dimensions (OpenAI)")
    print("   New: 1024 dimensions (BGE)")
    print()
    
    async for session in get_db_session():
        try:
            # Drop existing table and indexes
            print("1. Dropping existing vector_memory table...")
            await session.execute(text("DROP TABLE IF EXISTS vector_memory CASCADE"))
            await session.commit()
            print("   ✅ Dropped")
            
            # Create new table with 1024 dimensions
            print("\n2. Creating new vector_memory table with 1024 dimensions...")
            await session.execute(text("""
                CREATE TABLE vector_memory (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES "user"(id),
                    content TEXT NOT NULL,
                    embedding vector(1024),
                    metadata JSONB,
                    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
                )
            """))
            await session.commit()
            print("   ✅ Created")
            
            # Create indexes
            print("\n3. Creating indexes...")
            await session.execute(text("""
                CREATE INDEX ix_vector_memory_user_id 
                ON vector_memory(user_id)
            """))
            await session.execute(text("""
                CREATE INDEX ix_vector_memory_user_created 
                ON vector_memory(user_id, created_at)
            """))
            await session.execute(text("""
                CREATE INDEX ix_vector_memory_embedding_cosine 
                ON vector_memory 
                USING hnsw (embedding vector_cosine_ops)
            """))
            await session.commit()
            print("   ✅ Indexes created")
            
            print("\n✅ Vector dimension fix complete!")
            print("   Table: vector_memory")
            print("   Dimension: 1024 (BGE-compatible)")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await session.rollback()
            return False
        
        break
    
    return True


if __name__ == "__main__":
    success = asyncio.run(fix_vector_dimension())
    sys.exit(0 if success else 1)
