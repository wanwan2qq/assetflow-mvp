#!/usr/bin/env python3
"""
Debug script to test mock agent extraction
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.services.chat_agent import get_chat_agent


async def test_mock_extraction():
    """Test mock agent extraction"""
    
    print("🔍 Testing Mock Agent Extraction")
    print("=" * 50)
    
    test_user_id = 88888
    
    # Get chat agent
    chat_agent = get_chat_agent()
    
    print(f"Has real OpenAI key: {chat_agent.has_real_openai_key}")
    print(f"Agent type: {type(chat_agent.agent)}")
    
    # Test real estate extraction
    print("\n1️⃣ Testing real estate message processing")
    message = "我有一套房子在北京朝阳区，120平米"
    
    response_chunks = []
    async for chunk in chat_agent.process_message(message, test_user_id):
        response_chunks.append(chunk)
        print(f"Chunk: {chunk[:50]}...")
    
    print(f"Total response length: {len(''.join(response_chunks))}")


if __name__ == "__main__":
    asyncio.run(test_mock_extraction())