
import asyncio
import sys
import os
from unittest.mock import MagicMock, AsyncMock

# Add current directory to path
sys.path.append(os.getcwd())

from app.services.asset_extraction_service import AssetExtractionService
from app.services.information_extraction import ExtractedAsset
from app.models.user import AssetType, UserAsset

async def test_find_similar_asset():
    print("Initializing AssetExtractionService...")
    service = AssetExtractionService()
    
    user_id = 999
    # Simulate an extracted asset
    extracted_asset = ExtractedAsset(
        name="Test House",
        asset_type="real_estate",
        value=1000000.0,
        confidence=0.9,
        extracted_from="test",
        timestamp="2024-01-01T00:00:00"
    )
    # Mock specific attributes that might be accessed
    extracted_asset.location = "Test Location"
    extracted_asset.area = 100.0
    
    session = AsyncMock()
    # Mock session.execute result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [] # No existing assets
    session.execute.return_value = mock_result
    
    print("Calling _store_assets_in_session...")
    try:
        # Check if _find_similar_asset can be called directly first
        print("Testing _find_similar_asset(user_id, extracted_asset, session)...")
        await service._find_similar_asset(user_id, extracted_asset, session)
        print("SUCCESS: _find_similar_asset called without TypeError")
        
        # Now call _store_assets_in_session
        print("Testing _store_assets_in_session(user_id, [extracted_asset], session)...")
        extracted_assets = [extracted_asset]
        # We need to mock _create_asset_from_extracted because _store_assets_in_session calls it if not found, 
        # and it attempts to do DB operations (session.add, session.flush).
        # We can just mock the method on the service instance.
        service._create_asset_from_extracted = AsyncMock(return_value=UserAsset(name="New Asset"))
        
        await service._store_assets_in_session(user_id, extracted_assets, session)
        print("SUCCESS: _store_assets_in_session called without TypeError")
        
    except TypeError as e:
        print(f"FAILED with TypeError: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"FAILED with Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_find_similar_asset())
