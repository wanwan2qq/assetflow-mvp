#!/usr/bin/env python3
"""
Debug script to test information extraction
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.information_extraction import extract_information


async def test_extraction():
    """Test information extraction for real estate and cash"""
    
    print("🔍 Testing Information Extraction")
    print("=" * 50)
    
    # Test real estate extraction
    print("\n1️⃣ Testing real estate extraction")
    real_estate_message = "我有一套房子在北京朝阳区，120平米"
    conversation_history = []
    
    result1 = await extract_information(real_estate_message, conversation_history)
    print(f"Real estate result: {result1}")
    
    # Test cash extraction
    print("\n2️⃣ Testing cash extraction")
    cash_message = "我还有50万现金"
    conversation_history = [
        {"role": "user", "content": real_estate_message},
        {"role": "assistant", "content": "好的，我了解了您的房产情况"}
    ]
    
    result2 = await extract_information(cash_message, conversation_history)
    print(f"Cash result: {result2}")
    
    # Check if completeness_update is correct
    print("\n3️⃣ Checking completeness_update fields")
    print(f"Real estate completeness_update: {result1.get('completeness_update', {})}")
    print(f"Cash completeness_update: {result2.get('completeness_update', {})}")


if __name__ == "__main__":
    asyncio.run(test_extraction())