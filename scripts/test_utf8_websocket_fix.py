#!/usr/bin/env python3
"""
Test script to verify UTF-8 WebSocket message handling fix
"""

import asyncio
import json
import logging
import websockets
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, base_url: str = "ws://localhost:8000"):
        self.base_url = base_url
        self.websocket = None
        
    async def connect(self, user_id: int, token: str):
        """Connect to WebSocket endpoint"""
        uri = f"{self.base_url}/api/v1/chat/ws/chat/{user_id}?token={token}"
        logger.info(f"Connecting to: {uri}")
        
        try:
            self.websocket = await websockets.connect(uri)
            logger.info("✅ WebSocket connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    async def send_message(self, content: str):
        """Send a message to the WebSocket"""
        if not self.websocket:
            logger.error("WebSocket not connected")
            return False
            
        message = {
            "content": content,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        try:
            message_json = json.dumps(message, ensure_ascii=False)
            # Validate UTF-8 encoding
            message_json.encode('utf-8')
            
            await self.websocket.send(message_json)
            logger.info(f"✅ Sent message: {content[:50]}...")
            return True
        except UnicodeEncodeError as e:
            logger.error(f"❌ UTF-8 encoding error: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
    
    async def listen_for_messages(self, timeout: int = 30):
        """Listen for incoming messages"""
        if not self.websocket:
            logger.error("WebSocket not connected")
            return []
            
        messages = []
        try:
            async for message in asyncio.wait_for(
                self.websocket, timeout=timeout
            ):
                try:
                    # Validate UTF-8 encoding
                    message.encode('utf-8')
                    
                    # Parse JSON
                    data = json.loads(message)
                    messages.append(data)
                    
                    msg_type = data.get('type', 'unknown')
                    content = data.get('content', '')[:100]
                    logger.info(f"📨 Received [{msg_type}]: {content}...")
                    
                    # Stop listening after complete message
                    if msg_type == 'complete':
                        break
                        
                except UnicodeDecodeError as e:
                    logger.error(f"❌ UTF-8 decode error: {e}")
                    logger.error(f"Raw bytes: {message.encode('utf-8', errors='replace')}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    logger.error(f"Raw message: {message[:200]}...")
                except Exception as e:
                    logger.error(f"❌ Message processing error: {e}")
                    
        except asyncio.TimeoutError:
            logger.warning("⏰ Timeout waiting for messages")
        except Exception as e:
            logger.error(f"❌ Error listening for messages: {e}")
            
        return messages
    
    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 WebSocket disconnected")

async def test_utf8_messages():
    """Test various UTF-8 message scenarios"""
    
    # Test messages with different character sets
    test_messages = [
        "我目前有房贷80万，消费贷20万",  # Chinese characters
        "我有一套房子在北京🏠，价值500万💰",  # Chinese + emojis
        "Hello world! 你好世界! 🌍",  # Mixed languages + emoji
        "Special chars: ñáéíóú çüß αβγ",  # Various accented characters
        "Math symbols: ∑∏∫∆∇∂",  # Mathematical symbols
        "Currency: $¥€£₹₽",  # Currency symbols
    ]
    
    tester = WebSocketTester()
    
    # Mock user credentials (replace with actual test credentials)
    user_id = 20
    token = "test-token-here"  # You'll need a valid token for testing
    
    try:
        # Connect
        if not await tester.connect(user_id, token):
            logger.error("Failed to connect, skipping tests")
            return
        
        # Wait for welcome message
        logger.info("Waiting for welcome message...")
        welcome_messages = await tester.listen_for_messages(timeout=5)
        
        # Test each message
        for i, message in enumerate(test_messages, 1):
            logger.info(f"\n🧪 Test {i}/{len(test_messages)}: {message}")
            
            # Send message
            if await tester.send_message(message):
                # Listen for response
                responses = await tester.listen_for_messages(timeout=15)
                
                if responses:
                    logger.info(f"✅ Test {i} passed - received {len(responses)} responses")
                    
                    # Check for UTF-8 issues in responses
                    for resp in responses:
                        content = resp.get('content', '')
                        try:
                            content.encode('utf-8')
                            logger.info(f"✅ Response UTF-8 valid")
                        except UnicodeEncodeError as e:
                            logger.error(f"❌ Response UTF-8 invalid: {e}")
                else:
                    logger.warning(f"⚠️ Test {i} - no responses received")
            else:
                logger.error(f"❌ Test {i} failed - couldn't send message")
            
            # Small delay between tests
            await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
    finally:
        await tester.disconnect()

async def main():
    """Main test function"""
    logger.info("🚀 Starting UTF-8 WebSocket fix verification")
    logger.info("=" * 60)
    
    await test_utf8_messages()
    
    logger.info("=" * 60)
    logger.info("🏁 UTF-8 WebSocket test completed")

if __name__ == "__main__":
    asyncio.run(main())