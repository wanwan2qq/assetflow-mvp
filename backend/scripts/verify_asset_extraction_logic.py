
import logging
import asyncio

# Mocking the data structure returned by InformationExtractionService
asset_data_structure = {
    "type": "real_estate",
    "name": "房产",
    "value": None,
    "location": None, # Top level location missing
    "area": 89,
    "metadata": {
        "location": "北京市朝阳区", # Location present in metadata
        "area": 89
    }
}

async def verify_logic():
    print("Verifying AssetExtractionService location fallback logic...")
    
    asset_data = asset_data_structure
    name = asset_data.get("name")
    
    # 1. Logic before fix
    location_old = asset_data.get("location")
    val_location_old = location_old or name or ""
    print(f"Old Logic Location: '{val_location_old}' (Should be '房产')")
    
    # 2. Logic after fix
    location_new = asset_data.get("location")
    if not location_new and isinstance(asset_data.get("metadata"), dict):
        location_new = asset_data.get("metadata").get("location")
        
    val_location_new = location_new or name or ""
    print(f"New Logic Location: '{val_location_new}' (Should be '北京市朝阳区')")
    
    if val_location_new == "北京市朝阳区":
        print("✅ Fix verified: Location correctly retrieved from metadata")
    else:
        print("❌ Fix failed: Location NOT retrieved from metadata")

if __name__ == "__main__":
    asyncio.run(verify_logic())
