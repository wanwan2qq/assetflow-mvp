#!/usr/bin/env python3
"""
Debug frontend connection issues
"""

import requests
import json

def debug_frontend_connection():
    """Debug why frontend shows 'not connected' after login"""
    
    print("=== Frontend Connection Debug ===")
    
    # Step 1: Test backend is running
    print("\n1. Checking backend status...")
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running on port 8000")
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return
    
    # Step 2: Test fresh login
    print("\n2. Testing fresh login...")
    try:
        # Send SMS
        sms_response = requests.post(
            "http://localhost:8000/api/v1/auth/send-sms",
            json={"phone": "13800138000"},
            timeout=5
        )
        
        if sms_response.status_code != 200:
            print(f"❌ SMS failed: {sms_response.text}")
            return
        
        print("✅ SMS sent successfully")
        
        # Login
        login_response = requests.post(
            "http://localhost:8000/api/v1/auth/login/phone",
            json={"phone": "13800138000", "verification_code": "123456"},
            timeout=5
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return
        
        login_data = login_response.json()
        token = login_data["access_token"]
        user_id = login_data["user_id"]
        
        print(f"✅ Login successful")
        print(f"   User ID: {user_id}")
        print(f"   Token: {token[:30]}...")
        
        # Step 3: Test token validation
        print(f"\n3. Testing token validation...")
        auth_response = requests.get(
            "http://localhost:8000/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if auth_response.status_code == 200:
            user_data = auth_response.json()
            print(f"✅ Token is valid - User: {user_data['phone']}")
        else:
            print(f"❌ Token validation failed: {auth_response.status_code} - {auth_response.text}")
            return
        
        # Step 4: Test WebSocket URL accessibility
        print(f"\n4. Testing WebSocket endpoint...")
        websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
        print(f"   WebSocket URL: {websocket_url[:80]}...")
        
        # Test if the endpoint exists (HTTP version)
        try:
            test_response = requests.get(f"http://localhost:8000/api/v1/chat/context/{user_id}", 
                                       headers={"Authorization": f"Bearer {token}"}, 
                                       timeout=5)
            if test_response.status_code in [200, 404]:  # 404 is OK, means endpoint exists
                print("✅ Chat endpoints are accessible")
            else:
                print(f"⚠️ Chat endpoint responded with: {test_response.status_code}")
        except Exception as e:
            print(f"❌ Chat endpoint test failed: {e}")
        
        print(f"\n=== Frontend Debug Instructions ===")
        print(f"1. Open browser DevTools (F12)")
        print(f"2. Go to Console tab")
        print(f"3. Look for these messages after login:")
        print(f"   - '🔄 Token changed, reconnecting WebSocket...'")
        print(f"   - '🔌 Connecting WebSocket for user {user_id}...'")
        print(f"   - WebSocket connection success/failure messages")
        print(f"")
        print(f"4. Go to Network tab")
        print(f"5. Filter by 'WS' (WebSocket)")
        print(f"6. Navigate to chat page and check if WebSocket connection appears")
        print(f"")
        print(f"7. If no WebSocket connection, check for JavaScript errors in Console")
        print(f"")
        print(f"=== Expected Token Info ===")
        print(f"User ID: {user_id}")
        print(f"Phone: 13800138000")
        print(f"Token (first 50 chars): {token[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

if __name__ == "__main__":
    debug_frontend_connection()