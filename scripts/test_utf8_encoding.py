#!/usr/bin/env python3
"""
Test UTF-8 encoding/decoding scenarios that might cause WebSocket issues
"""

import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_utf8_scenarios():
    """Test various UTF-8 encoding scenarios"""
    
    test_cases = [
        {
            "name": "Chinese characters",
            "content": "我目前有房贷80万，消费贷20万"
        },
        {
            "name": "Chinese + emojis",
            "content": "感谢您提供这么重要的负债信息！🤝这对您的财务安全分析至关重要。"
        },
        {
            "name": "Mixed content with special chars",
            "content": "## 📊 您的资产配置分析\n\n根据标准普尔四象限模型..."
        },
        {
            "name": "Problematic emoji sequence",
            "content": "📨 Received WebSocket message: 感谢您提供这么重要的负债信息！🤝"
        },
        {
            "name": "Complex mixed content",
            "content": "💡 【ADVISOR STRATEGY NOTE】\n感谢您提供这么重要的负债信息！🤝这对您的财务安全分析至关重要。让我基于最新的完整信息，为您重新做一次全面的资产配置分析。\n\n## 📊"
        }
    ]
    
    logger.info("🧪 Testing UTF-8 encoding scenarios")
    logger.info("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        name = test_case["name"]
        content = test_case["content"]
        
        logger.info(f"\n🔍 Test {i}: {name}")
        logger.info(f"Content: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        try:
            # Test 1: Basic UTF-8 encoding
            encoded = content.encode('utf-8')
            logger.info(f"✅ UTF-8 encoding: {len(encoded)} bytes")
            
            # Test 2: UTF-8 decoding
            decoded = encoded.decode('utf-8')
            logger.info(f"✅ UTF-8 decoding: matches original = {decoded == content}")
            
            # Test 3: JSON serialization with ensure_ascii=False
            message = {
                "type": "chunk",
                "content": content,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            json_str = json.dumps(message, ensure_ascii=False)
            logger.info(f"✅ JSON serialization: {len(json_str)} chars")
            
            # Test 4: JSON + UTF-8 encoding (what WebSocket does)
            json_bytes = json_str.encode('utf-8')
            logger.info(f"✅ JSON + UTF-8: {len(json_bytes)} bytes")
            
            # Test 5: Full round trip
            decoded_json = json_bytes.decode('utf-8')
            parsed = json.loads(decoded_json)
            final_content = parsed['content']
            
            if final_content == content:
                logger.info(f"✅ Full round trip: SUCCESS")
            else:
                logger.error(f"❌ Full round trip: FAILED")
                logger.error(f"Original: {repr(content)}")
                logger.error(f"Final: {repr(final_content)}")
            
            # Test 6: Check for problematic characters
            problematic_chars = []
            for char in content:
                code_point = ord(char)
                if code_point == 0xFFFD:  # Replacement character
                    problematic_chars.append(f"U+FFFD at position {content.index(char)}")
                elif code_point > 0x10FFFF:  # Invalid Unicode
                    problematic_chars.append(f"Invalid Unicode U+{code_point:X} at position {content.index(char)}")
            
            if problematic_chars:
                logger.warning(f"⚠️ Problematic characters found: {problematic_chars}")
            else:
                logger.info(f"✅ No problematic characters detected")
                
        except UnicodeEncodeError as e:
            logger.error(f"❌ UTF-8 encoding failed: {e}")
            logger.error(f"Error at position {e.start}-{e.end}: {repr(content[e.start:e.end])}")
        except UnicodeDecodeError as e:
            logger.error(f"❌ UTF-8 decoding failed: {e}")
        except json.JSONEncodeError as e:
            logger.error(f"❌ JSON encoding failed: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("🏁 UTF-8 encoding tests completed")

def test_error_recovery():
    """Test error recovery scenarios"""
    
    logger.info("\n🔧 Testing error recovery scenarios")
    logger.info("=" * 60)
    
    # Simulate problematic content
    problematic_cases = [
        {
            "name": "Content with replacement character",
            "content": "Hello \uFFFD World"
        },
        {
            "name": "Mixed valid/invalid",
            "content": "正常文字 \uFFFD 更多文字"
        }
    ]
    
    for i, test_case in enumerate(problematic_cases, 1):
        name = test_case["name"]
        content = test_case["content"]
        
        logger.info(f"\n🔍 Recovery Test {i}: {name}")
        
        try:
            # Test error handling with 'replace' strategy
            clean_content = content.encode('utf-8', errors='replace').decode('utf-8')
            logger.info(f"✅ Cleaned content: {repr(clean_content)}")
            
            # Test filtering out replacement characters
            filtered_content = ''.join(char for char in content if ord(char) != 0xFFFD)
            logger.info(f"✅ Filtered content: {repr(filtered_content)}")
            
        except Exception as e:
            logger.error(f"❌ Recovery failed: {e}")

if __name__ == "__main__":
    test_utf8_scenarios()
    test_error_recovery()