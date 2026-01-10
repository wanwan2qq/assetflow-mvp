#!/usr/bin/env python3
"""
Monitor backend WebSocket in real-time to see if messages are being received
"""

import asyncio
import json
import requests
import websockets
from datetime import datetime

async def monitor_backend_websocket():
    """Monitor backend WebSocket to see what's happening"""
    
    print("=== Backend WebSocket Monitor ===")
    
    # Get fresh token for user ID 9 (the frontend user)
    phone = "18602552212"
    
    print(f"\n1. Getting token for user with phone: {phone}")
    
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
    
    print(f"✅ Login successful")
    print(f"   User ID: {user_id}")
    print(f"   Phone: {phone}")
    
    # Connect to WebSocket and monitor
    print(f"\n2. Connecting to WebSocket for monitoring...")
    
    websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print(f"✅ WebSocket connected for monitoring user {user_id}")
            
            # Wait for welcome message
            welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            welcome_data = json.loads(welcome_msg)
            print(f"✅ Welcome: {welcome_data.get('content', '')[:50]}...")
            
            print(f"\n3. 🔍 MONITORING MODE - Waiting for messages from frontend...")
            print(f"   Now send a message from the frontend and I'll show what backend receives")
            print(f"   Monitoring for 60 seconds...")
            
            # Monitor for incoming messages
            message_count = 0
            
            for i in range(60):  # Monitor for 60 seconds
                try:
                    # Check if there are any messages
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    message_count += 1
                    
                    try:
                        message_data = json.loads(message)
                        msg_type = message_data.get("type", "unknown")
                        content = message_data.get("content", "")
                        
                        print(f"\n📨 [{message_count}] Received from backend:")
                        print(f"   Type: {msg_type}")
                        print(f"   Content: {content[:100]}...")
                        print(f"   Full message: {message}")
                        
                    except json.JSONDecodeError:
                        print(f"\n📨 [{message_count}] Received raw message: {message}")
                        
                except asyncio.TimeoutError:
                    # No message received in this second
                    if i % 10 == 0 and i > 0:
                        print(f"   ... still monitoring ({i}s elapsed, {message_count} messages received)")
                    continue
                except Exception as e:
                    print(f"❌ Error receiving message: {e}")
                    break
            
            print(f"\n📊 Monitoring complete:")
            print(f"   Total messages received: {message_count}")
            
            if message_count == 0:
                print(f"\n❌ NO MESSAGES RECEIVED FROM BACKEND")
                print(f"   This suggests:")
                print(f"   1. Frontend messages are not reaching backend")
                print(f"   2. Backend is not processing messages")
                print(f"   3. Backend AI system has issues")
                
                # Test if backend AI works by sending a direct message
                print(f"\n4. Testing backend AI directly...")
                test_message = {
                    "content": "测试消息",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(test_message, ensure_ascii=False))
                print(f"✅ Sent test message to backend")
                
                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    print(f"✅ Backend responded: {response[:100]}...")
                    print(f"   Backend AI is working!")
                except asyncio.TimeoutError:
                    print(f"❌ Backend did not respond to test message")
                    print(f"   Backend AI system has issues")
            
            else:
                print(f"✅ Backend is receiving and processing messages")
                
    except Exception as e:
        print(f"❌ WebSocket monitoring failed: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_backend_websocket())