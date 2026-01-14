"""
Phase 4: Database initialization script
Initializes database with all tables including vector_memory
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from sqlmodel import SQLModel

from app.core.database import async_engine, get_db_session
from app.models import *  # Import all models


async def init_database():
    """Initialize database with all tables"""
    print("🔧 Initializing AssetFlow database...")
    
    async with async_engine.begin() as conn:
        # Enable pgvector extension
        print("📦 Enabling pgvector extension...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("✅ pgvector extension enabled")
        
        # Create all tables
        print("📊 Creating database tables...")
        await conn.run_sync(SQLModel.metadata.create_all)
        print("✅ All tables created")
    
    # Verify vector_memory table
    async for session in get_db_session():
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'vector_memory'
        """))
        
        if result.scalar_one_or_none():
            print("✅ vector_memory table verified")
        else:
            print("❌ vector_memory table not found")
            return False
        
        # Check if pgvector extension is enabled
        result = await session.execute(text("""
            SELECT extname FROM pg_extension WHERE extname = 'vector'
        """))
        
        if result.scalar_one_or_none():
            print("✅ pgvector extension verified")
        else:
            print("❌ pgvector extension not found")
            return False
        
        break
    
    print("\n🎉 Database initialization complete!")
    print("\nCreated tables:")
    
    async for session in get_db_session():
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        
        tables = result.scalars().all()
        for table in tables:
            print(f"  - {table}")
        
        break
    
    return True


if __name__ == "__main__":
    success = asyncio.run(init_database())
    sys.exit(0 if success else 1)
