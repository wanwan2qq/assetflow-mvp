#!/usr/bin/env python3
"""
Test the frontend chat fix by simulating the complete flow
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime

async def test_frontend_chat_fix():
    """Test that the frontend chat fix works end-to-end"""
    
    print("=== Frontend Chat Fix Test ===")
    
    # Step 1: Get fresh token
    print("\n1. Getting fresh authentication token...")
    
    # Send SMS
    sms_response = requests.post(
        "http://localhost:8000/api/v1/auth/send-sms",
        json={"phone": "13800138000"}
    )
    
    if sms_response.status_code != 200:
        print(f"❌ SMS failed: {sms_response.text}")
        return False
    
    # Login
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login/phone",
        json={"phone": "13800138000", "verification_code": "123456"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    login_data = login_response.json()
    token = login_data["access_token"]
    user_id = login_data["user_id"]
    
    print(f"✅ Fresh token obtained - User ID: {user_id}")
    print(f"   Token: {token[:30]}...")
    
    # Step 2: Test WebSocket with fresh token (simulating what frontend should do)
    print(f"\n2. Testing WebSocket connection with fresh token...")
    
    websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_msg)
            print(f"✅ Welcome: {welcome_data.get('content', '')[:50]}...")
            
            # Step 3: Test conversation flow
            print(f"\n3. Testing AI conversation flow...")
            
            test_messages = [
                "你好，我想了解资产配置",
                "我在北京有一套房产，价值500万",
                "我还有100万现金存款"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n   Testing message {i}: {message}")
                
                # Send message
                msg_data = {
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(msg_data, ensure_ascii=False))
                print(f"   ✅ Message sent")
                
                # Wait for complete response
                response_received = False
                response_count = 0
                
                for _ in range(15):  # Wait up to 15 seconds
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response_data = json.loads(response)
                        
                        msg_type = response_data.get("type")
                        content = response_data.get("content", "")
                        response_count += 1
                        
                        if msg_type == "complete":
                            print(f"   ✅ Complete response received: {content[:50]}...")
                            response_received = True
                            break
                        elif msg_type == "error":
                            print(f"   ❌ Error response: {content}")
                            return False
                        elif msg_type in ["typing", "chunk"]:
                            print(f"   📝 {msg_type}: {content[:30]}...")
                            
                    except asyncio.TimeoutError:
                        continue
                
                if not response_received:
                    print(f"   ❌ No complete response received for message {i} (got {response_count} partial responses)")
                    return False
            
            print(f"\n✅ All conversation tests passed!")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

async def main():
    success = await test_frontend_chat_fix()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ FRONTEND CHAT FIX: WORKING")
        print("Backend AI chat system is fully functional!")
        print("\nThe frontend should now work correctly:")
        print("1. Login with phone 13800138000 and code 123456")
        print("2. Navigate to chat page")
        print("3. WebSocket should connect automatically with fresh token")
        print("4. Send messages and receive AI responses")
        print("\nIf frontend still doesn't work, check browser console for:")
        print("- Token update messages")
        print("- WebSocket connection logs")
        print("- JavaScript errors")
    else:
        print("❌ FRONTEND CHAT FIX: FAILED")
        print("There are still issues with the backend system")
    
    print(f"{'='*60}")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"1. Open http://localhost:8080 in browser")
    print(f"2. Open browser DevTools (F12) and check Console tab")
    print(f"3. Login and navigate to chat page")
    print(f"4. Look for debug messages about token updates and WebSocket connections")
    print(f"5. Send a test message and verify AI responds")

if __name__ == "__main__":
    asyncio.run(main())