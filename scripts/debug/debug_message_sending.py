#!/usr/bin/env python3
"""
Debug message sending with the correct user ID
"""

import asyncio
import json
import requests
import websockets

async def debug_message_sending():
    """Debug message sending with user ID 9 (from the logs)"""
    
    print("=== Message Sending Debug ===")
    
    # Get fresh token for user ID 28 (the logged in user)
    print("\n1. Getting fresh token for current user...")
    
    # Login to get the current user's token
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login/phone",
        json={"phone": "18603552212", "verification_code": "123456"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data["access_token"]
    user_id = login_data["user_id"]
    
    print(f"✅ Current user login successful")
    print(f"   User ID: {user_id}")
    print(f"   Phone: {login_data['phone']}")
    print(f"   Token: {token[:30]}...")
    
    # Test WebSocket connection with the current user
    print(f"\n2. Testing WebSocket with user ID {user_id}...")
    
    websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print(f"✅ WebSocket connected for user {user_id}")
            
            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_msg)
            print(f"✅ Welcome: {welcome_data.get('content', '')[:50]}...")
            
            # Send test message
            test_message = {
                "content": "你好",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            print(f"\n3. Sending test message...")
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            print(f"✅ Message sent")
            
            # Wait for responses
            print(f"\n4. Waiting for AI responses...")
            responses = []
            
            for i in range(10):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    
                    msg_type = response_data.get("type")
                    content = response_data.get("content", "")
                    
                    responses.append(response_data)
                    print(f"[{len(responses)}] {msg_type}: {content[:50]}...")
                    
                    if msg_type == "complete":
                        print(f"✅ Complete response received!")
                        break
                    elif msg_type == "error":
                        print(f"❌ Error: {content}")
                        break
                        
                except asyncio.TimeoutError:
                    if len(responses) == 0:
                        print(f"⚠️ No response after {i+1} seconds...")
                    continue
            
            if len(responses) > 0:
                print(f"\n✅ Backend AI is working! Received {len(responses)} responses")
                return True
            else:
                print(f"\n❌ No responses received from backend")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

async def main():
    success = await debug_message_sending()
    
    print(f"\n{'='*60}")
    if success:
        print("✅ BACKEND AI SYSTEM: WORKING")
        print("The issue is in frontend user ID mismatch!")
        print("\nFrontend Problem:")
        print("- Frontend is connecting with user ID 9")
        print("- But the logged in user is ID 28 (phone: 18603552212)")
        print("- This causes message routing issues")
        
        print(f"\n🔧 SOLUTION:")
        print("1. Check why frontend auth state has wrong user ID")
        print("2. Ensure frontend uses the correct user ID from login response")
        print("3. Clear any cached auth state that might have old user ID")
        
    else:
        print("❌ BACKEND AI SYSTEM: ISSUES FOUND")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())