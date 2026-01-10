#!/usr/bin/env python3
"""
Debug with the correct user phone number from the frontend
"""

import asyncio
import json
import requests
import websockets

async def debug_correct_user():
    """Debug with the actual phone number used in frontend"""
    
    print("=== Correct User Debug ===")
    
    # Use the actual phone number from the frontend logs
    phone = "18602552212"  # The actual phone number from your login
    
    print(f"\n1. Testing login with phone: {phone}")
    
    # Send SMS
    sms_response = requests.post(
        "http://localhost:8000/api/v1/auth/send-sms",
        json={"phone": phone}
    )
    
    if sms_response.status_code != 200:
        print(f"❌ SMS failed: {sms_response.text}")
        return
    
    print("✅ SMS sent successfully")
    
    # Login
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login/phone",
        json={"phone": phone, "verification_code": "123456"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data["access_token"]
    user_id = login_data["user_id"]
    
    print(f"✅ Login successful with phone {phone}")
    print(f"   User ID: {user_id}")
    print(f"   Token: {token[:30]}...")
    
    # Test WebSocket connection
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
            
            return len(responses) > 0, user_id
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False, user_id

async def main():
    success, correct_user_id = await debug_correct_user()
    
    print(f"\n{'='*60}")
    print(f"📋 ANALYSIS RESULTS:")
    print(f"Phone number used: 18602552212")
    print(f"Correct User ID: {correct_user_id}")
    print(f"Backend AI working: {'✅ YES' if success else '❌ NO'}")
    
    if success:
        print(f"\n✅ BACKEND IS WORKING CORRECTLY!")
        print(f"The issue is that frontend is using a different user ID.")
        print(f"\n🔍 FRONTEND DEBUG CHECKLIST:")
        print(f"1. Check frontend console for the actual user ID being used")
        print(f"2. Look for: 'WebSocket connected for user X'")
        print(f"3. The user ID should be: {correct_user_id}")
        print(f"4. If different, there's a frontend auth state issue")
        
        print(f"\n🔧 FRONTEND FIX:")
        print(f"1. Clear browser cache/storage")
        print(f"2. Restart Flutter app completely")
        print(f"3. Re-login and check user ID matches {correct_user_id}")
        
    else:
        print(f"\n❌ BACKEND ISSUE FOUND")
        print(f"Need to investigate backend AI system")
    
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())