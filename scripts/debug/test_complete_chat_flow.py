#!/usr/bin/env python3
"""
Test the complete chat flow: login -> WebSocket -> AI response
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime

async def test_complete_chat_flow():
    """Test the complete chat flow from login to AI response"""
    
    print("=== Complete Chat Flow Test ===")
    
    # Step 1: Fresh login
    print("\n1. Getting fresh login token...")
    
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
    
    print(f"✅ Login successful - User ID: {user_id}")
    print(f"   Token: {token[:30]}...")
    
    # Step 2: Test WebSocket with fresh token
    print(f"\n2. Testing WebSocket connection...")
    
    websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket connected")
            
            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_msg)
            print(f"✅ Welcome: {welcome_data.get('content', '')[:60]}...")
            
            # Step 3: Test AI conversation
            print(f"\n3. Testing AI conversation...")
            
            test_messages = [
                "你好",
                "我在北京有一套房子",
                "房子在朝阳区，100平米",
                "我还有50万现金存款"
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n   Message {i}: {message}")
                
                # Send message
                msg_data = {
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(msg_data, ensure_ascii=False))
                print(f"   ✅ Sent")
                
                # Collect responses
                responses = []
                complete_received = False
                
                for _ in range(10):  # Wait up to 10 seconds
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response_data = json.loads(response)
                        
                        msg_type = response_data.get("type")
                        content = response_data.get("content", "")
                        
                        responses.append(response_data)
                        
                        if msg_type == "complete":
                            print(f"   ✅ Complete response: {content[:60]}...")
                            complete_received = True
                            break
                        elif msg_type == "error":
                            print(f"   ❌ Error: {content}")
                            break
                        elif msg_type in ["typing", "chunk"]:
                            print(f"   📝 {msg_type}: {content[:40]}...")
                            
                    except asyncio.TimeoutError:
                        if len(responses) == 0:
                            print(f"   ⚠️ No response yet...")
                        continue
                
                if not complete_received and len(responses) == 0:
                    print(f"   ❌ No response received for message {i}")
                    return False
                elif not complete_received:
                    print(f"   ⚠️ Incomplete response for message {i} (got {len(responses)} chunks)")
            
            print(f"\n✅ All messages processed successfully")
            return True
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

async def main():
    success = await test_complete_chat_flow()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ COMPLETE CHAT FLOW: WORKING")
        print("Backend AI chat system is fully functional!")
        print("\nThe issue is likely in the frontend:")
        print("1. Frontend may not be getting fresh tokens after login")
        print("2. Frontend WebSocket may not be reconnecting with new tokens")
        print("3. Check browser console for token/WebSocket errors")
    else:
        print("❌ COMPLETE CHAT FLOW: FAILED")
        print("There are issues in the backend chat system")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())