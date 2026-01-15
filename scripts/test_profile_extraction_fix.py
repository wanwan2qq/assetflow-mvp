#!/usr/bin/env python3
"""
Test script to verify that occupation and income_range are properly extracted and stored
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.information_extraction import extract_information
from app.services.asset_extraction_service import asset_extraction_service
from app.core.database import get_db_session
from app.models.cognition import UserCognition
from sqlmodel import select


async def test_profile_extraction():
    """Test that occupation and income_range are extracted and stored"""
    
    print("=" * 80)
    print("Testing Profile Extraction Fix")
    print("=" * 80)
    
    # Test 1: Extract information from a message with occupation and income
    test_message = "我是一名软件工程师，月收入大概5万元"
    conversation_history = []
    
    print(f"\n📝 Test Message: {test_message}")
    print("\n🔍 Step 1: Extracting information...")
    
    extraction_result = await extract_information(test_message, conversation_history)
    
    print(f"\n✅ Extraction Result:")
    print(f"   - Assets: {extraction_result.get('assets', [])}")
    print(f"   - Goals: {extraction_result.get('goals', [])}")
    print(f"   - Risk Profile: {extraction_result.get('risk_profile', {})}")
    print(f"   - Completeness Update: {extraction_result.get('completeness_update', {})}")
    
    # Check if occupation and income_range are in risk_profile
    risk_profile = extraction_result.get('risk_profile', {})
    
    print("\n🔍 Step 2: Verifying extracted fields...")
    
    has_occupation = 'occupation' in risk_profile
    has_income = 'income_range' in risk_profile
    
    print(f"   - Occupation extracted: {has_occupation}")
    if has_occupation:
        print(f"     Value: {risk_profile['occupation']}")
    
    print(f"   - Income range extracted: {has_income}")
    if has_income:
        print(f"     Value: {risk_profile['income_range']}")
    
    # Test 2: Verify storage to database
    print("\n🔍 Step 3: Testing database storage...")
    
    # Use a test user ID (you may need to adjust this)
    test_user_id = 1
    
    success = await asset_extraction_service.update_user_state(test_user_id, extraction_result)
    
    if success:
        print(f"   ✅ Successfully updated user state for user {test_user_id}")
        
        # Verify the data was stored
        async for session in get_db_session():
            statement = select(UserCognition).where(UserCognition.user_id == test_user_id)
            result = await session.execute(statement)
            cognition = result.scalar_one_or_none()
            
            if cognition and cognition.risk_profile:
                print(f"\n✅ Verified UserCognition.risk_profile:")
                print(f"   - Full risk_profile: {cognition.risk_profile}")
                
                stored_occupation = cognition.risk_profile.get('occupation')
                stored_income = cognition.risk_profile.get('income_range')
                
                print(f"   - Occupation stored: {stored_occupation is not None}")
                if stored_occupation:
                    print(f"     Value: {stored_occupation}")
                
                print(f"   - Income range stored: {stored_income is not None}")
                if stored_income:
                    print(f"     Value: {stored_income}")
                
                # Final verdict
                print("\n" + "=" * 80)
                if stored_occupation and stored_income:
                    print("✅ SUCCESS: Both occupation and income_range are properly stored!")
                elif stored_occupation or stored_income:
                    print("⚠️  PARTIAL: Some fields are stored but not all")
                else:
                    print("❌ FAILURE: occupation and income_range are NOT stored")
                print("=" * 80)
            else:
                print(f"   ⚠️  No UserCognition record found for user {test_user_id}")
            
            break
    else:
        print(f"   ❌ Failed to update user state for user {test_user_id}")
    
    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_profile_extraction())
