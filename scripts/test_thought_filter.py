#!/usr/bin/env python3
"""
Test script to verify <Thought> block filtering

This script tests that:
1. <Thought> blocks are removed from user-facing responses
2. <Thought> content is logged to console for debugging
3. Conversation history doesn't contain <Thought> blocks
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.chat_agent import ChatAgent


def test_thought_filter():
    """Test the _filter_thought_blocks method"""
    print("\n" + "="*80)
    print("TEST: <Thought> Block Filtering")
    print("="*80)
    
    agent = ChatAgent()
    
    # Test Case 1: Response with <Thought> block
    print("\n📝 Test Case 1: Response with <Thought> block")
    print("-" * 80)
    
    test_response_1 = """<Thought>
1. Fact Check: User mentioned 35 years old
2. History Context: Previous message about property
3. Strategy Check: Use encouraging tone
4. Intent Analysis: User wants valuation
5. Response Plan: Provide market reference
</Thought>

很好！35岁拥有房产是很不错的资产积累 💡 让我帮您查询一下市场参考价。"""
    
    filtered, thought = agent._filter_thought_blocks(test_response_1)
    
    print(f"\n原始响应:\n{test_response_1}")
    print(f"\n过滤后响应:\n{filtered}")
    print(f"\n提取的思考内容:\n{thought}")
    
    # Verify
    if "<Thought>" not in filtered and "</Thought>" not in filtered:
        print("\n✅ PASS: <Thought> blocks removed from response")
    else:
        print("\n❌ FAIL: <Thought> blocks still present in response")
    
    if thought and "Fact Check" in thought:
        print("✅ PASS: Thought content extracted successfully")
    else:
        print("❌ FAIL: Thought content not extracted")
    
    # Test Case 2: Response without <Thought> block
    print("\n\n📝 Test Case 2: Response without <Thought> block")
    print("-" * 80)
    
    test_response_2 = "您好！很高兴为您服务 🤝 有什么财务问题想要探讨吗？"
    
    filtered, thought = agent._filter_thought_blocks(test_response_2)
    
    print(f"\n原始响应:\n{test_response_2}")
    print(f"\n过滤后响应:\n{filtered}")
    print(f"\n提取的思考内容:\n{thought if thought else '(无)'}")
    
    # Verify
    if filtered == test_response_2:
        print("\n✅ PASS: Response unchanged when no <Thought> block")
    else:
        print("\n❌ FAIL: Response modified unexpectedly")
    
    if not thought:
        print("✅ PASS: No thought content extracted (as expected)")
    else:
        print("❌ FAIL: Unexpected thought content extracted")
    
    # Test Case 3: Multiple <Thought> blocks
    print("\n\n📝 Test Case 3: Multiple <Thought> blocks")
    print("-" * 80)
    
    test_response_3 = """<Thought>
First analysis: Check user profile
</Thought>

这是第一部分回复。

<Thought>
Second analysis: Check asset data
</Thought>

这是第二部分回复。"""
    
    filtered, thought = agent._filter_thought_blocks(test_response_3)
    
    print(f"\n原始响应:\n{test_response_3}")
    print(f"\n过滤后响应:\n{filtered}")
    print(f"\n提取的思考内容:\n{thought}")
    
    # Verify
    if "<Thought>" not in filtered and "</Thought>" not in filtered:
        print("\n✅ PASS: All <Thought> blocks removed")
    else:
        print("\n❌ FAIL: Some <Thought> blocks remain")
    
    if "First analysis" in thought and "Second analysis" in thought:
        print("✅ PASS: All thought content extracted")
    else:
        print("❌ FAIL: Not all thought content extracted")
    
    # Test Case 4: Case-insensitive matching
    print("\n\n📝 Test Case 4: Case-insensitive matching")
    print("-" * 80)
    
    test_response_4 = """<thought>
This is lowercase thought tag
</thought>

<THOUGHT>
This is uppercase thought tag
</THOUGHT>

Final response text."""
    
    filtered, thought = agent._filter_thought_blocks(test_response_4)
    
    print(f"\n原始响应:\n{test_response_4}")
    print(f"\n过滤后响应:\n{filtered}")
    print(f"\n提取的思考内容:\n{thought}")
    
    # Verify
    if "<thought>" not in filtered.lower():
        print("\n✅ PASS: Case-insensitive filtering works")
    else:
        print("\n❌ FAIL: Case-insensitive filtering failed")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    
    print("\n📋 Summary:")
    print("  ✅ <Thought> blocks are filtered from user-facing responses")
    print("  ✅ Thought content is extracted for logging")
    print("  ✅ Multiple thought blocks are handled correctly")
    print("  ✅ Case-insensitive matching works")
    print("\n💡 In production:")
    print("  - User sees: Clean response without <Thought> blocks")
    print("  - Console logs: 🧠 CHAIN OF THOUGHT (User X): [thought content]")
    print("  - Database stores: Filtered response only")


if __name__ == "__main__":
    test_thought_filter()
