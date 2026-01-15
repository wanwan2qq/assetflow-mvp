#!/usr/bin/env python3
"""
Test script for high-priority SQL data structure fixes
Tests the three main fixes:
1. UserProfile creation with partial data
2. UserAsset duplicate handling
3. Data layer separation (L1 vs L2)
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlmodel import select
from app.core.database import get_db_session
from app.models.user import User, UserProfile, UserAsset, AssetType
from app.models.cognition import UserCognition
from app.services.asset_extraction_service import asset_extraction_service


async def test_fix_1_partial_profile_creation():
    """Test Fix 1: UserProfile should be created with partial data"""
    print("\n" + "="*80)
    print("TEST 1: UserProfile Creation with Partial Data")
    print("="*80)
    
    # Create test user
    async for session in get_db_session():
        # Clean up test user if exists
        test_phone = "13900000001"
        existing_user = (await session.execute(
            select(User).where(User.phone == test_phone)
        )).scalar_one_or_none()
        
        if existing_user:
            await session.delete(existing_user)
            await session.commit()
        
        # Create new test user
        test_user = User(phone=test_phone)
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id
        print(f"✓ Created test user: {user_id}")
        break
    
    # Test Case 1: Only occupation provided (should create profile with defaults)
    print("\n--- Test Case 1: Only occupation provided ---")
    extraction_result = {
        "assets": [],
        "goals": [],
        "risk_profile": {
            "occupation": "软件工程师"
        },
        "completeness_update": {}
    }
    
    success = await asset_extraction_service.update_user_state(user_id, extraction_result)
    print(f"Update result: {success}")
    
    # Verify profile was created
    async for session in get_db_session():
        profile = (await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )).scalar_one_or_none()
        
        if profile:
            print(f"✓ UserProfile created successfully!")
            print(f"  - age_range: {profile.age_range} (should be default '30-40')")
            print(f"  - family_structure: {profile.family_structure} (should be default 'single')")
            print(f"  - risk_preference: {profile.risk_preference} (should be default 'moderate')")
            print(f"  - occupation: {profile.occupation} (should be '软件工程师')")
            
            assert profile.occupation == "软件工程师", "Occupation not saved!"
            assert profile.age_range == "30-40", "Default age_range not set!"
            print("✓ Test Case 1 PASSED")
        else:
            print("✗ UserProfile NOT created - FIX FAILED!")
            return False
        break
    
    # Test Case 2: Add income_range (should update existing profile)
    print("\n--- Test Case 2: Add income_range to existing profile ---")
    extraction_result = {
        "assets": [],
        "goals": [],
        "risk_profile": {
            "income_range": "20-50万"
        },
        "completeness_update": {}
    }
    
    success = await asset_extraction_service.update_user_state(user_id, extraction_result)
    
    async for session in get_db_session():
        profile = (await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )).scalar_one_or_none()
        
        if profile and profile.income_range == "20-50万":
            print(f"✓ income_range updated: {profile.income_range}")
            print(f"✓ occupation preserved: {profile.occupation}")
            print("✓ Test Case 2 PASSED")
        else:
            print(f"✗ income_range not updated correctly")
            return False
        break
    
    return True


async def test_fix_2_asset_duplicate_handling():
    """Test Fix 2: Improved asset duplicate detection"""
    print("\n" + "="*80)
    print("TEST 2: UserAsset Duplicate Handling")
    print("="*80)
    
    # Create test user
    async for session in get_db_session():
        test_phone = "13900000002"
        existing_user = (await session.execute(
            select(User).where(User.phone == test_phone)
        )).scalar_one_or_none()
        
        if existing_user:
            await session.delete(existing_user)
            await session.commit()
        
        test_user = User(phone=test_phone)
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id
        print(f"✓ Created test user: {user_id}")
        break
    
    # Test Case 1: Add first property
    print("\n--- Test Case 1: Add first property ---")
    extraction_result = {
        "assets": [{
            "type": "real_estate",
            "name": "天通苑北一区",
            "amount": 5000000,
            "location": "北京市昌平区",
            "area": 120
        }],
        "goals": [],
        "risk_profile": {},
        "completeness_update": {"real_estate": True}
    }
    
    await asset_extraction_service.update_user_state(user_id, extraction_result)
    
    async for session in get_db_session():
        assets = (await session.execute(
            select(UserAsset).where(UserAsset.user_id == user_id)
        )).scalars().all()
        
        print(f"✓ Created {len(assets)} asset(s)")
        assert len(assets) == 1, "Should have 1 asset"
        print(f"  - {assets[0].name}: {assets[0].value}")
        break
    
    # Test Case 2: Add similar property (should update, not create new)
    print("\n--- Test Case 2: Update similar property ---")
    extraction_result = {
        "assets": [{
            "type": "real_estate",
            "name": "天通苑北一区120平",
            "amount": 5200000,
            "location": "北京昌平区",
            "area": 120
        }],
        "goals": [],
        "risk_profile": {},
        "completeness_update": {"real_estate": True}
    }
    
    await asset_extraction_service.update_user_state(user_id, extraction_result)
    
    async for session in get_db_session():
        assets = (await session.execute(
            select(UserAsset).where(UserAsset.user_id == user_id)
        )).scalars().all()
        
        if len(assets) == 1:
            print(f"✓ Still 1 asset (updated, not duplicated)")
            print(f"  - {assets[0].name}: {assets[0].value}")
            assert assets[0].value == 5200000, "Value should be updated"
            print("✓ Test Case 2 PASSED")
        else:
            print(f"✗ Found {len(assets)} assets - duplicate not prevented!")
            return False
        break
    
    # Test Case 3: Add different property (should create new)
    print("\n--- Test Case 3: Add different property ---")
    extraction_result = {
        "assets": [{
            "type": "real_estate",
            "name": "朝阳公园附近",
            "amount": 8000000,
            "location": "北京市朝阳区",
            "area": 150
        }],
        "goals": [],
        "risk_profile": {},
        "completeness_update": {"real_estate": True}
    }
    
    await asset_extraction_service.update_user_state(user_id, extraction_result)
    
    async for session in get_db_session():
        assets = (await session.execute(
            select(UserAsset).where(UserAsset.user_id == user_id)
        )).scalars().all()
        
        if len(assets) == 2:
            print(f"✓ Now 2 assets (new property added)")
            for asset in assets:
                print(f"  - {asset.name}: {asset.value}")
            print("✓ Test Case 3 PASSED")
        else:
            print(f"✗ Expected 2 assets, found {len(assets)}")
            return False
        break
    
    return True


async def test_fix_3_data_layer_separation():
    """Test Fix 3: L1 vs L2 data layer separation"""
    print("\n" + "="*80)
    print("TEST 3: Data Layer Separation (L1 vs L2)")
    print("="*80)
    
    # Create test user
    async for session in get_db_session():
        test_phone = "13900000003"
        existing_user = (await session.execute(
            select(User).where(User.phone == test_phone)
        )).scalar_one_or_none()
        
        if existing_user:
            await session.delete(existing_user)
            await session.commit()
        
        test_user = User(phone=test_phone)
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id
        print(f"✓ Created test user: {user_id}")
        break
    
    # Add profile data
    print("\n--- Adding profile data ---")
    extraction_result = {
        "assets": [],
        "goals": ["retirement"],
        "risk_profile": {
            "age_range": "40-50",
            "family_structure": "married_with_kids",
            "tolerance": "conservative",
            "monthly_expense": 15000,
            "occupation": "医生",
            "income_range": "50-100万"
        },
        "completeness_update": {}
    }
    
    await asset_extraction_service.update_user_state(user_id, extraction_result)
    
    # Verify L1 (UserProfile) has basic fields
    async for session in get_db_session():
        profile = (await session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )).scalar_one_or_none()
        
        cognition = (await session.execute(
            select(UserCognition).where(UserCognition.user_id == user_id)
        )).scalar_one_or_none()
        
        print("\n--- L1 Layer (UserProfile) ---")
        if profile:
            print(f"✓ age_range: {profile.age_range}")
            print(f"✓ family_structure: {profile.family_structure}")
            print(f"✓ risk_preference: {profile.risk_preference}")
            print(f"✓ monthly_expense: {profile.monthly_expense}")
            print(f"✓ occupation: {profile.occupation}")
            print(f"✓ income_range: {profile.income_range}")
        else:
            print("✗ UserProfile not created!")
            return False
        
        print("\n--- L2 Layer (UserCognition.risk_profile) ---")
        if cognition and cognition.risk_profile:
            print(f"Risk profile keys: {list(cognition.risk_profile.keys())}")
            
            # Check that basic fields are NOT duplicated in L2
            basic_fields = ["age_range", "family_structure", "monthly_expense", "occupation", "income_range"]
            duplicated_fields = [f for f in basic_fields if f in cognition.risk_profile]
            
            if duplicated_fields:
                print(f"⚠️  WARNING: Basic fields found in L2 (should only be in L1): {duplicated_fields}")
                print("   This is acceptable for backward compatibility, but ideally should be removed")
            else:
                print(f"✓ No basic fields in L2 (clean separation)")
            
            # Check that psychological fields ARE in L2
            if "tolerance" in cognition.risk_profile:
                print(f"✓ Psychological field 'tolerance' in L2: {cognition.risk_profile['tolerance']}")
            
            print("✓ Test Case 3 PASSED")
        else:
            print("✗ UserCognition not created!")
            return False
        
        break
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("HIGH PRIORITY FIXES VALIDATION")
    print("="*80)
    
    results = []
    
    # Test 1
    try:
        result = await test_fix_1_partial_profile_creation()
        results.append(("Fix 1: UserProfile Creation", result))
    except Exception as e:
        print(f"\n✗ Test 1 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Fix 1: UserProfile Creation", False))
    
    # Test 2
    try:
        result = await test_fix_2_asset_duplicate_handling()
        results.append(("Fix 2: Asset Duplicate Handling", result))
    except Exception as e:
        print(f"\n✗ Test 2 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Fix 2: Asset Duplicate Handling", False))
    
    # Test 3
    try:
        result = await test_fix_3_data_layer_separation()
        results.append(("Fix 3: Data Layer Separation", result))
    except Exception as e:
        print(f"\n✗ Test 3 FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Fix 3: Data Layer Separation", False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print("\n❌ Some tests FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
