#!/usr/bin/env python3
"""
Debug WebSocket messages in real-time
"""

import asyncio
import json
import websockets
import requests

async def debug_websocket_messages():
    """Debug WebSocket message flow"""
    
    print("=== WebSocket Message Debug ===")
    
    # Use fresh token from login
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyOCIsImV4cCI6MTc2ODYzODk4NCwiaWF0IjoxNzY3OTQ3Nzg0LCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiMTc2NzkxODk4NC45MzU3MDMifQ.qbOPyD1XUyyrnh8C9Ylkgb3lVmVQp2vMjPSNiV6givA"
    user_id = 28
    
    print(f"Using User ID: {user_id}")
    print(f"Token: {token[:30]}...")
    
    # First verify token is valid
    print("\n1. Verifying token...")
    try:
        response = requests.get(
            "http://localhost:8000/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token is valid - User: {user_data}")
        else:
            print(f"❌ Token is invalid - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Token validation failed: {e}")
        return False
    
    # Connect to WebSocket
    print(f"\n2. Connecting to WebSocket...")
    websocket_url = f"ws://localhost:8000/api/v1/chat/ws/chat/{user_id}?token={token}"
    
    try:
        async with websockets.connect(websocket_url) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Wait for welcome message
            print("\n3. Waiting for welcome message...")
            try:
                welcome_msg = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome_msg)
                print(f"✅ Welcome received: {welcome_data.get('type')} - {welcome_data.get('content', '')[:50]}...")
            except asyncio.TimeoutError:
                print("❌ No welcome message received")
                return False
            
            # Send test message and monitor
            print(f"\n4. Sending test message and monitoring...")
            
            test_message = {
                "content": "你好",
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            print(f"Sending: {json.dumps(test_message, ensure_ascii=False)}")
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            print("✅ Message sent to backend")
            
            # Monitor responses for 15 seconds
            print("\n5. Monitoring responses...")
            responses = []
            
            for i in range(15):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    response_data = json.loads(response)
                    
                    msg_type = response_data.get("type")
                    content = response_data.get("content", "")
                    
                    responses.append(response_data)
                    print(f"[{len(responses)}] Received {msg_type}: {content[:60]}...")
                    
                    if msg_type == "complete":
                        print("✅ Complete response received")
                        break
                    elif msg_type == "error":
                        print(f"❌ Error received: {content}")
                        break
                        
                except asyncio.TimeoutError:
                    if i > 5 and len(responses) == 0:
                        print(f"⚠️ No responses after {i+1} seconds...")
                    continue
                except json.JSONDecodeError as e:
                    print(f"❌ JSON decode error: {e}")
                    continue
            
            print(f"\n=== Results ===")
            print(f"Total responses: {len(responses)}")
            
            if len(responses) > 0:
                print("Response types:", [r.get("type") for r in responses])
                print("✅ Backend is responding to WebSocket messages")
                return True
            else:
                print("❌ No responses received from backend")
                print("This suggests the message is not reaching the AI agent")
                return False
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(debug_websocket_messages())
    
    print(f"\n{'='*60}")
    if result:
        print("✅ BACKEND WEBSOCKET: WORKING")
        print("The issue is likely in the frontend:")
        print("1. Frontend may not be sending messages correctly")
        print("2. Frontend may not be receiving/displaying responses")
        print("3. Check browser console for JavaScript errors")
    else:
        print("❌ BACKEND WEBSOCKET: NOT WORKING")
        print("The issue is in the backend WebSocket handling")
    
    print(f"{'='*60}")
    
    print("\nNEXT STEPS:")
    print("1. Check if frontend is actually sending WebSocket messages")
    print("2. Monitor browser Network tab for WebSocket frames")
    print("3. Check frontend console for errors")
    print("4. Verify frontend message handling logic")