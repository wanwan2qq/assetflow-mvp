import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.services.property_valuation import get_property_valuation_service

async def verify_valuation():
    print("Checking Property Valuation Service...")
    service = get_property_valuation_service()
    
    # Test Case 1: Beijing Chaoyang (Should hit Tier 2 Benchmark)
    location = "北京市朝阳区"
    area = 100
    
    print(f"\nTest 1: {location}, {area}sqm")
    valuation = await service.get_market_value(location, area)
    
    print(f"Value: {valuation.value:,.2f}")
    print(f"Source: {valuation.source}")
    print(f"Confidence: {valuation.confidence}")
    
    if valuation.value > 0 and valuation.value != 1000000:
        print("✅ Valuation successful (Tier 2/3 functional)")
    else:
        print("❌ Valuation failed or returned default")

    # Test Case 2: Unknown City (Should hit Tier 3 LLM or Tier 2 Default)
    location = "UnknownCity District"
    print(f"\nTest 2: {location}, {area}sqm")
    valuation = await service.get_market_value(location, area)
    print(f"Value: {valuation.value:,.2f}")
    print(f"Source: {valuation.source}")

if __name__ == "__main__":
    asyncio.run(verify_valuation())
