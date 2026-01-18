#!/usr/bin/env python3
"""
Verify WebSocket UTF-8 fix by testing the backend chat agent directly
"""

import asyncio
import json
import logging
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.services.chat_agent import get_chat_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chat_agent_utf8():
    """Test chat agent with UTF-8 content"""
    
    logger.info("🧪 Testing Chat Agent UTF-8 handling")
    logger.info("=" * 60)
    
    # Get chat agent
    agent = get_chat_agent()
    
    # Test messages that previously caused issues
    test_messages = [
        "我目前有房贷80万，消费贷20万",
        "我有一套房子在北京🏠，价值500万💰",
        "请帮我分析一下资产配置📊",
    ]
    
    user_id = 999  # Test user ID
    
    for i, message in enumerate(test_messages, 1):
        logger.info(f"\n🔍 Test {i}: {message}")
        
        try:
            # Process message
            response_chunks = []
            async for chunk in agent.process_message(message, user_id, None):
                if chunk.strip():
                    response_chunks.append(chunk)
                    
                    # Test UTF-8 encoding of each chunk
                    try:
                        chunk.encode('utf-8')
                        logger.info(f"✅ Chunk UTF-8 valid: {chunk[:50]}...")
                    except UnicodeEncodeError as e:
                        logger.error(f"❌ Chunk UTF-8 invalid: {e}")
                        logger.error(f"Problematic chunk: {repr(chunk)}")
            
            # Test full response
            full_response = "".join(response_chunks)
            
            if full_response:
                try:
                    full_response.encode('utf-8')
                    logger.info(f"✅ Full response UTF-8 valid ({len(full_response)} chars)")
                    
                    # Test JSON serialization (what WebSocket does)
                    test_message = {
                        "type": "chunk",
                        "content": full_response,
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                    
                    json_str = json.dumps(test_message, ensure_ascii=False)
                    json_str.encode('utf-8')
                    logger.info(f"✅ JSON + UTF-8 encoding successful")
                    
                except UnicodeEncodeError as e:
                    logger.error(f"❌ Full response UTF-8 invalid: {e}")
                except Exception as e:
                    logger.error(f"❌ JSON serialization failed: {e}")
            else:
                logger.warning(f"⚠️ No response generated")
                
        except Exception as e:
            logger.error(f"❌ Test {i} failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 Chat Agent UTF-8 tests completed")

def test_websocket_message_format():
    """Test WebSocket message format with UTF-8 content"""
    
    logger.info("\n🔧 Testing WebSocket message format")
    logger.info("=" * 60)
    
    # Test different message types
    test_messages = [
        {
            "type": "system",
            "content": "欢迎使用AssetFlow！我是您的AI资产配置顾问。",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        {
            "type": "chunk",
            "content": "感谢您提供这么重要的负债信息！🤝",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        {
            "type": "complete",
            "content": "## 📊 您的资产配置分析\n\n根据标准普尔四象限模型...",
            "ui_components": [],
            "timestamp": "2024-01-01T00:00:00Z"
        }
    ]
    
    for i, message in enumerate(test_messages, 1):
        msg_type = message["type"]
        logger.info(f"\n🔍 Message Type Test {i}: {msg_type}")
        
        try:
            # Test JSON serialization with ensure_ascii=False
            json_str = json.dumps(message, ensure_ascii=False)
            logger.info(f"✅ JSON serialization: {len(json_str)} chars")
            
            # Test UTF-8 encoding
            json_bytes = json_str.encode('utf-8')
            logger.info(f"✅ UTF-8 encoding: {len(json_bytes)} bytes")
            
            # Test decoding (what client does)
            decoded_json = json_bytes.decode('utf-8')
            parsed = json.loads(decoded_json)
            
            if parsed == message:
                logger.info(f"✅ Round trip successful")
            else:
                logger.error(f"❌ Round trip failed")
                
        except Exception as e:
            logger.error(f"❌ Message format test {i} failed: {e}")

if __name__ == "__main__":
    try:
        # Run tests
        asyncio.run(test_chat_agent_utf8())
        test_websocket_message_format()
        
        logger.info("\n🎉 All UTF-8 WebSocket fix verification tests completed!")
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)