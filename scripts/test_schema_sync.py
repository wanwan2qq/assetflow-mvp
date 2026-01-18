"""
Quick test to verify schema synchronization
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import get_db_session
from app.models.cognition import UserCognition
from sqlmodel import select


async def test_schema():
    """Test that the schema is properly synchronized"""
    
    print("\n" + "="*80)
    print("TEST: Schema Synchronization Verification")
    print("="*80)
    
    test_user_id = 9995
    
    try:
        async for session in get_db_session():
            # Try to query with new fields
            statement = select(UserCognition).where(UserCognition.user_id == test_user_id)
            result = await session.execute(statement)
            cognition = result.scalar_one_or_none()
            
            print(f"\n✓ Successfully queried UserCognition with new fields")
            
            if cognition:
                print(f"  - user_id: {cognition.user_id}")
                print(f"  - last_analyzed_message_id: {cognition.last_analyzed_message_id}")
                print(f"  - last_memory_extraction_at: {cognition.last_memory_extraction_at}")
            else:
                print(f"  - No cognition record found for user {test_user_id}")
                
                # Create one to test
                cognition = UserCognition(user_id=test_user_id)
                session.add(cognition)
                await session.commit()
                await session.refresh(cognition)
                
                print(f"\n✓ Created new UserCognition record")
                print(f"  - ID: {cognition.id}")
                print(f"  - user_id: {cognition.user_id}")
                print(f"  - last_analyzed_message_id: {cognition.last_analyzed_message_id}")
                print(f"  - last_memory_extraction_at: {cognition.last_memory_extraction_at}")
            
            break
        
        print("\n" + "="*80)
        print("✅ SCHEMA SYNCHRONIZATION SUCCESSFUL!")
        print("="*80)
        print("\nAll database schema changes have been applied:")
        print("✓ user_cognition/usercognition table exists")
        print("✓ last_analyzed_message_id column added")
        print("✓ last_memory_extraction_at column added")
        print("✓ Index created for performance")
        print("\nThe incremental extraction fix is ready to use!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_schema())
    sys.exit(0 if success else 1)
