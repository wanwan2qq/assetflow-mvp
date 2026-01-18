#!/usr/bin/env python3
"""
Test UTF-8 logging fix by simulating problematic messages
"""

import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_problematic_messages():
    """Test messages that previously caused UTF-8 logging issues"""
    
    # These are the types of messages that caused the crash
    problematic_messages = [
        {
            "type": "chunk",
            "content": "明白了！您想了解AI投资的具体产品筛选，这确实是一个很前沿的方向。作为保守型投资者，您对AI投资感兴趣但要求从稳健开始，这个思路非常明智。"
        },
        {
            "type": "chunk", 
            "content": "感谢您提供这么重要的负债信息！🤝这对您的财务安全分析至关重要。让我基于最新的完整信息，为您重新做一次全面的资产配置分析。\n\n## 📊"
        },
        {
            "type": "system",
            "content": "欢迎使用AssetFlow！我是您的AI资产配置顾问 🤝"
        }
    ]
    
    logger.info("🧪 Testing UTF-8 logging scenarios")
    logger.info("=" * 60)
    
    for i, message in enumerate(problematic_messages, 1):
        logger.info(f"\n🔍 Test {i}: {message['type']} message")
        
        try:
            # Simulate the JSON serialization that happens in WebSocket
            json_str = json.dumps(message, ensure_ascii=False)
            logger.info(f"✅ JSON serialization successful: {len(json_str)} chars")
            
            # Simulate the logging that happens in frontend
            content = message['content']
            
            # Test safe logging approach
            def safe_log_string(text, max_length=100):
                try:
                    truncated = text[:max_length] + '...' if len(text) > max_length else text
                    # Validate UTF-8 encoding (simulate Dart's codeUnits check)
                    truncated.encode('utf-8').decode('utf-8')
                    return truncated
                except UnicodeError:
                    return f'Text ({len(text)} chars) - contains invalid UTF-8 characters'
            
            safe_content = safe_log_string(content)
            logger.info(f"✅ Safe logging: {safe_content}")
            
            # Test the problematic approach (what was causing crashes)
            try:
                # This simulates the old approach that could cause issues
                debug_message = content[:100] + '...' if len(content) > 100 else content
                # In Dart, this would be: debug_message.codeUnits
                debug_message.encode('utf-8').decode('utf-8')
                logger.info(f"✅ Direct logging would work: {debug_message}")
            except UnicodeError as e:
                logger.warning(f"⚠️ Direct logging would fail: {e}")
                
        except Exception as e:
            logger.error(f"❌ Test {i} failed: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 UTF-8 logging tests completed")

def test_emoji_combinations():
    """Test specific emoji combinations that might cause issues"""
    
    logger.info("\n🔧 Testing emoji combinations")
    logger.info("=" * 60)
    
    emoji_tests = [
        "📨 Received WebSocket message",
        "🤝 握手emoji测试",
        "📊 图表emoji + 中文",
        "💡 灯泡 + 🏠 房子 + 💰 钱袋",
        "🔹 菱形bullet points",
    ]
    
    for i, test_text in enumerate(emoji_tests, 1):
        logger.info(f"\n🔍 Emoji Test {i}: {test_text}")
        
        try:
            # Test encoding/decoding
            encoded = test_text.encode('utf-8')
            decoded = encoded.decode('utf-8')
            
            if decoded == test_text:
                logger.info(f"✅ Emoji encoding/decoding successful")
            else:
                logger.error(f"❌ Emoji encoding/decoding failed")
                
            # Test safe truncation
            truncated = test_text[:20] + '...' if len(test_text) > 20 else test_text
            truncated.encode('utf-8').decode('utf-8')
            logger.info(f"✅ Safe truncation: {truncated}")
            
        except UnicodeError as e:
            logger.error(f"❌ Emoji test {i} failed: {e}")

if __name__ == "__main__":
    test_problematic_messages()
    test_emoji_combinations()
    
    logger.info("\n🎉 All UTF-8 logging fix tests completed!")
    logger.info("The safe logging approach should prevent frontend crashes.")