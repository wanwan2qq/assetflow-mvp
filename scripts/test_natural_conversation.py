#!/usr/bin/env python3
"""
Test script to demonstrate natural conversation improvements
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.chat_agent import ChatAgent, ChatContext


async def main():
    print("Testing Natural Conversation Improvements")
    print("=" * 60)
    
    agent = ChatAgent()
    
    # Test 1: Completion Signal
    print("\n[TEST 1] Completion Signal Handling")
    context = ChatContext(user_id=999, current_stage="asset_collection")
    context.extracted_assets = [{"asset_type": "real_estate", "value": 5000000}]
    
    response = agent._generate_mock_response("就这些了", context)
    print(f"User: 就这些了")
    print(f"AI: {response[:150]}...")
    
    if "基于您目前" in response or "明白了" in response:
        print("✅ PASS: Accepts completion signal\n")
    else:
        print("❌ FAIL: Still asking for more\n")
    
    # Test 2: Empathy First
    print("[TEST 2] Emotion-First Response")
    context2 = ChatContext(user_id=999, current_stage="initial")
    
    response2 = agent._generate_mock_response("房贷压力很大", context2)
    print(f"User: 房贷压力很大")
    print(f"AI: {response2[:150]}...")
    
    if "理解" in response2 or "压力" in response2:
        print("✅ PASS: Shows empathy\n")
    else:
        print("❌ FAIL: Lacks empathy\n")
    
    # Test 3: Non-Interrogative
    print("[TEST 3] Consultative Style")
    context3 = ChatContext(user_id=999, current_stage="property_collection")
    
    response3 = agent._generate_mock_response("我想了解配置", context3)
    print(f"User: 我想了解配置")
    print(f"AI: {response3[:150]}...")
    
    interrogative = ["请告诉我您目前的：", "让我们按四象限来梳理："]
    if not any(p in response3 for p in interrogative):
        print("✅ PASS: Uses consultative style\n")
    else:
        print("⚠️  WARNING: Still somewhat interrogative\n")
    
    print("=" * 60)
    print("Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
