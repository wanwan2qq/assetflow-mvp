# Frontend Debug Instructions

## Issue Summary
The backend AI chat system is **fully functional**. The issue is in the frontend token management where the WebSocket connection is using expired tokens instead of fresh ones after login.

## Backend Status ✅
- SMS verification: Working
- Login API: Working  
- Token generation: Working
- WebSocket authentication: Working
- AI chat responses: Working

## Frontend Issue ❌
The frontend is not properly updating the WebSocket connection with fresh tokens after login.

## Debug Steps

### 1. Test Fresh Login
1. Open browser to http://localhost:8080
2. Open browser DevTools (F12)
3. Go to Console tab
4. Login with phone: `13800138000` and code: `123456`
5. Check console for token debug messages

### 2. Check Token State
After login, in the browser console, run:
```javascript
// This should show the current auth state
console.log('Auth state:', window.flutter_app_state);
```

### 3. Monitor WebSocket Connection
1. Go to Network tab in DevTools
2. Filter by "WS" (WebSocket)
3. Try to send a chat message
4. Check if WebSocket connection shows:
   - Connection attempt
   - Authentication success/failure
   - Message frames

### 4. Expected Behavior
After login, you should see:
- Console message: "🔄 Token changed, reconnecting WebSocket..."
- Console message: "🔌 Connecting WebSocket for user X with token..."
- Network tab: New WebSocket connection
- Chat: AI responses appear

## Fresh Token for Testing
If you need to manually test with a fresh token:

**User ID:** 28
**Phone:** 13800138000  
**Fresh Token:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyOCIsImV4cCI6MTc2ODYzOTAzMywiaWF0IjoxNzY3OTQ3ODMzLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiMTc2NzkxOTAzMy4wMjA1ODYifQ.yEgAlNzDIzy-3rdW_L0HTCTCDp3ouSCV7nKT9XrI8iM`

## Code Changes Made
1. **Chat Page**: Made WebSocket connection reactive to auth state changes
2. **Auth Provider**: Added token refresh debugging methods
3. **WebSocket Service**: Added connection logging

## Next Steps
1. Test the frontend login flow
2. Check browser console for debug messages
3. Verify WebSocket reconnection happens after login
4. If still not working, check if the auth provider state is properly updating

## Backend Test Command
To verify backend is working:
```bash
python3 test_complete_chat_flow.py
```