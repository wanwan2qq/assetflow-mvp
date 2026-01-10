#!/usr/bin/env python3
"""
Test frontend token management by simulating login and checking token state
"""

import requests
import json

def test_frontend_token_flow():
    """Test the complete frontend token flow"""
    
    print("=== Frontend Token Debug Test ===")
    
    # Step 1: Send SMS
    print("\n1. Sending SMS verification code...")
    sms_response = requests.post(
        "http://localhost:8000/api/v1/auth/send-sms",
        json={"phone": "13800138000"},
        headers={"Content-Type": "application/json"}
    )
    
    if sms_response.status_code == 200:
        print("✅ SMS sent successfully")
    else:
        print(f"❌ SMS failed: {sms_response.status_code} - {sms_response.text}")
        return
    
    # Step 2: Login with verification code
    print("\n2. Logging in with verification code...")
    login_response = requests.post(
        "http://localhost:8000/api/v1/auth/login/phone",
        json={"phone": "13800138000", "verification_code": "123456"},
        headers={"Content-Type": "application/json"}
    )
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data["access_token"]
        user_id = login_data["user_id"]
        print(f"✅ Login successful")
        print(f"   User ID: {user_id}")
        print(f"   Token: {token[:30]}...")
    else:
        print(f"❌ Login failed: {login_response.status_code} - {login_response.text}")
        return
    
    # Step 3: Verify token works
    print("\n3. Verifying token...")
    verify_response = requests.get(
        "http://localhost:8000/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if verify_response.status_code == 200:
        user_data = verify_response.json()
        print(f"✅ Token verified - User: {user_data['phone']}")
    else:
        print(f"❌ Token verification failed: {verify_response.status_code}")
        return
    
    # Step 4: Test WebSocket connection
    print(f"\n4. Testing WebSocket connection...")
    import asyncio
    import websockets
    
    async def test_websocket():
        websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
        
        try:
            async with websockets.connect(websocket_url) as websocket:
                print("✅ WebSocket connected")
                
                # Wait for welcome message
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                welcome_data = json.loads(welcome_msg)
                print(f"✅ Welcome: {welcome_data.get('content', '')[:50]}...")
                
                # Send test message
                test_msg = {"content": "测试消息", "timestamp": "2024-01-01T00:00:00Z"}
                await websocket.send(json.dumps(test_msg, ensure_ascii=False))
                print("✅ Test message sent")
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"✅ Response: {response_data.get('type')} - {response_data.get('content', '')[:50]}...")
                
                return True
                
        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False
    
    websocket_result = asyncio.run(test_websocket())
    
    print(f"\n=== Summary ===")
    print(f"Backend API: ✅ Working")
    print(f"Token Management: ✅ Working")
    print(f"WebSocket: {'✅ Working' if websocket_result else '❌ Failed'}")
    
    print(f"\n=== For Frontend Debugging ===")
    print(f"Use this fresh token in frontend:")
    print(f"Token: {token}")
    print(f"User ID: {user_id}")
    print(f"Phone: 13800138000")
    
    return token, user_id

if __name__ == "__main__":
    test_frontend_token_flow()