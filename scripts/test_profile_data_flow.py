#!/usr/bin/env python3
"""
Test script to verify the User Profile data flow fix
Tests: Extraction -> Service -> DB for occupation and income_range
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(backend_path / ".env")

from app.services.information_extraction import extract_information
from app.services.asset_extraction_service import asset_extraction_service
from app.core.database import get_db_session
from app.models.user import User, UserProfile
from app.models.cognition import UserCognition
from sqlmodel import select


async def test_profile_extraction_and_storage():
    """Test that occupation and income_range are extracted and stored correctly"""
    
    print("=" * 80)
    print("Testing User Profile Data Flow Fix")
    print("=" * 80)
    
    # Test message with occupation and income
    test_message = "我是一名软件工程师，年收入大概在30-50万之间，每月支出约1万元"
    
    print(f"\n📝 Test Message: {test_message}")
    
    # Step 1: Test extraction
    print("\n" + "=" * 80)
    print("STEP 1: Testing Extraction (information_extraction.py)")
    print("=" * 80)
    
    extraction_result = await extract_information(test_message, [])
    
    print(f"\n✅ Extraction Result:")
    print(f"   - Assets: {extraction_result.get('assets', [])}")
    print(f"   - Goals: {extraction_result.get('goals', [])}")
    print(f"   - Risk Profile: {extraction_result.get('risk_profile', {})}")
    
    risk_profile = extraction_result.get('risk_profile', {})
    occupation = risk_profile.get('occupation')
    income_range = risk_profile.get('income_range')
    monthly_expense = risk_profile.get('monthly_expense')
    
    print(f"\n🔍 Checking extracted profile fields:")
    print(f"   - Occupation: {occupation}")
    print(f"   - Income Range: {income_range}")
    print(f"   - Monthly Expense: {monthly_expense}")
    
    if not occupation:
        print("   ❌ FAIL: Occupation not extracted!")
        return False
    
    if not income_range:
        print("   ❌ FAIL: Income range not extracted!")
        return False
    
    print("   ✅ PASS: All profile fields extracted correctly")
    
    # Step 2: Test storage
    print("\n" + "=" * 80)
    print("STEP 2: Testing Storage (asset_extraction_service.py)")
    print("=" * 80)
    
    # Create a test user
    async for session in get_db_session():
        # Clean up any existing test user
        test_phone = "13800000999"
        existing_user = await session.execute(
            select(User).where(User.phone == test_phone)
        )
        existing_user = existing_user.scalar_one_or_none()
        
        if existing_user:
            # Delete existing profile and cognition
            existing_profile = await session.execute(
                select(UserProfile).where(UserProfile.user_id == existing_user.id)
            )
            existing_profile = existing_profile.scalar_one_or_none()
            if existing_profile:
                await session.delete(existing_profile)
            
            existing_cognition = await session.execute(
                select(UserCognition).where(UserCognition.user_id == existing_user.id)
            )
            existing_cognition = existing_cognition.scalar_one_or_none()
            if existing_cognition:
                await session.delete(existing_cognition)
            
            await session.delete(existing_user)
            await session.commit()
        
        # Create new test user
        test_user = User(phone=test_phone, device_id="test_device_profile_flow")
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        
        print(f"\n✅ Created test user: ID={test_user.id}, Phone={test_user.phone}")
        
        # Call update_user_state
        print(f"\n📤 Calling update_user_state with extraction_result...")
        success = await asset_extraction_service.update_user_state(
            test_user.id, extraction_result
        )
        
        if not success:
            print("   ❌ FAIL: update_user_state returned False!")
            return False
        
        print("   ✅ update_user_state completed successfully")
        
        # Step 3: Verify database storage
        print("\n" + "=" * 80)
        print("STEP 3: Verifying Database Storage")
        print("=" * 80)
        
        # Check UserCognition table (occupation and income_range should be here)
        cognition_result = await session.execute(
            select(UserCognition).where(UserCognition.user_id == test_user.id)
        )
        cognition = cognition_result.scalar_one_or_none()
        
        if not cognition:
            print("   ❌ FAIL: UserCognition not created!")
            return False
        
        print(f"\n✅ UserCognition found:")
        print(f"   - Risk Profile: {cognition.risk_profile}")
        
        if not cognition.risk_profile:
            print("   ❌ FAIL: risk_profile is empty!")
            return False
        
        cog_occupation = cognition.risk_profile.get('occupation')
        cog_income = cognition.risk_profile.get('income_range')
        cog_expense = cognition.risk_profile.get('monthly_expense')
        
        print(f"   - Occupation in cognition: {cog_occupation}")
        print(f"   - Income range in cognition: {cog_income}")
        print(f"   - Monthly expense in cognition: {cog_expense}")
        
        # Verify occupation and income_range in UserCognition
        if cog_occupation != occupation:
            print(f"   ❌ FAIL: Occupation mismatch in UserCognition! Expected '{occupation}', got '{cog_occupation}'")
            return False
        
        if cog_income != income_range:
            print(f"   ❌ FAIL: Income range mismatch in UserCognition! Expected '{income_range}', got '{cog_income}'")
            return False
        
        if cog_expense != monthly_expense:
            print(f"   ❌ FAIL: Monthly expense mismatch in UserCognition! Expected '{monthly_expense}', got '{cog_expense}'")
            return False
        
        print("\n   ✅ PASS: All profile fields stored correctly in UserCognition.risk_profile!")
        
        # Check UserProfile table (may not exist if required fields are missing)
        profile_result = await session.execute(
            select(UserProfile).where(UserProfile.user_id == test_user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if profile:
            print(f"\n✅ UserProfile also found:")
            print(f"   - Occupation: {profile.occupation}")
            print(f"   - Income Range: {profile.income_range}")
            print(f"   - Monthly Expense: {profile.monthly_expense}")
            print(f"   - Age Range: {profile.age_range}")
            print(f"   - Family Structure: {profile.family_structure}")
            print(f"   - Risk Preference: {profile.risk_preference}")
            
            # Verify occupation and income_range if profile exists
            if profile.occupation == occupation and profile.income_range == income_range:
                print("   ✅ PASS: Profile fields also stored in UserProfile table!")
        else:
            print(f"\n⚠️  UserProfile not created (missing required fields: age_range, family_structure, risk_preference)")
            print(f"   This is expected - occupation and income_range are stored in UserCognition.risk_profile")
        
        # Clean up
        print("\n🧹 Cleaning up test data...")
        if profile:
            await session.delete(profile)
        if cognition:
            await session.delete(cognition)
        await session.delete(test_user)
        await session.commit()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\n✨ Summary:")
        print("   1. ✅ Extraction includes occupation and income_range")
        print("   2. ✅ Service stores data to UserCognition.risk_profile")
        print("   3. ✅ Database contains correct values")
        print("\n🎉 User Profile data flow is working correctly!")
        print("\n📝 Note: UserProfile table requires age_range, family_structure, and risk_preference")
        print("   When these are missing, occupation and income_range are stored in UserCognition.risk_profile")
        
        return True


if __name__ == "__main__":
    result = asyncio.run(test_profile_extraction_and_storage())
    sys.exit(0 if result else 1)
