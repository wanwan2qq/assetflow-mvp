#!/usr/bin/env python3
"""
Test if frontend hot reload is working
"""

import requests
import time

def test_frontend_hot_reload():
    """Test if the frontend is running and can be updated"""
    
    print("=== Frontend Hot Reload Test ===")
    
    # Test if frontend is accessible
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible on port 8080")
        else:
            print(f"⚠️ Frontend responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return
    
    print("\n📋 Next Steps:")
    print("1. In the terminal where Flutter is running, press 'r' for hot reload")
    print("2. Or press 'R' for hot restart")
    print("3. Wait for 'Hot reload/restart completed' message")
    print("4. Then refresh the browser page (Ctrl+F5)")
    print("5. Navigate to chat page and check console again")
    
    print("\n🔍 What to look for in console after hot reload:")
    print("- 🔍 Chat page loaded - Auth check:")
    print("- 🔌 Connecting WebSocket for user...")
    print("- 🚀 Attempting WebSocket connection...")
    
    print("\n⚠️ If still no WebSocket debug messages:")
    print("1. The chat page code might not be updated")
    print("2. Try stopping Flutter (Ctrl+C) and restart with:")
    print("   cd frontend && flutter run -d chrome --web-port 8080")

if __name__ == "__main__":
    test_frontend_hot_reload()