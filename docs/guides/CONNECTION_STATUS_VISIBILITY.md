# Connection Status Visibility Optimization

## Problem
The connection status indicator in the AppBar was always visible, showing states like "Connecting...", "Connected", "Reconnecting", etc. This cluttered the UI and distracted users during normal operation.

Additionally, during page loads or tab switches, the connection state momentarily reported `disconnected` before connecting, causing the error banner to flash briefly - poor UX.

## Solution
Implemented smart visibility logic with a **3-second grace period (debounce)** that:
1. Only shows the connection status when there's an actual failure requiring user attention
2. Prevents flashing by waiting 3 seconds before displaying error states
3. Immediately hides errors when connection is restored

## Grace Period Implementation

### State Variables
```dart
Timer? _connectionTimer;
bool _showConnectionError = false;
```

### Logic Flow

**On Connected/Connecting:**
- Immediately cancel any pending timer
- Hide error banner (`_showConnectionError = false`)
- Update connection state

**On Disconnected/Error:**
- Update connection state
- Start 3-second timer
- Only show error banner if state is still disconnected/error after 3 seconds

**On Reconnecting:**
- Cancel timer
- Hide error banner (automatic retry in progress)
- Update connection state

### Helper Method
```dart
void _startConnectionErrorTimer() {
  _connectionTimer?.cancel();
  
  _connectionTimer = Timer(const Duration(seconds: 3), () {
    if (mounted && 
        (_currentConnectionState == WebSocketConnectionState.disconnected ||
         _currentConnectionState == WebSocketConnectionState.error)) {
      setState(() {
        _showConnectionError = true;
      });
    }
  });
}
```

## Visibility Logic

### Hidden States (Clean UI)
- ✅ **Connected** - Everything working normally (error flag cleared immediately)
- ✅ **Connecting** - Initial connection attempt (error flag cleared immediately)
- ✅ **Reconnecting** - Automatic retry in progress (error flag cleared immediately)

### Visible States (User Action May Be Needed - After 3 Second Grace Period)
- ❌ **Error** - Authentication or connection failure
  - Shows: "连接失败" (Connection Failed) - **only after 3 seconds**
  - Banner message: "Token可能已过期，请重新登录后再试"
  - Actions: Re-login button + Retry button
  
- ❌ **Disconnected** (after connection was established)
  - Shows: "连接已断开" (Connection Lost) - **only after 3 seconds**
  - Banner message: "网络连接已断开，请检查网络或重试"
  - Actions: Retry button only

### Grace Period Behavior
- **Initial Load**: If app starts in disconnected state, 3-second timer starts
- **Tab Switch**: If momentarily disconnected, timer starts but usually connects before 3 seconds
- **Actual Failure**: Timer completes and error banner appears
- **Quick Recovery**: If connection restored within 3 seconds, timer cancelled and no error shown

## Implementation Details

### State Variables
```dart
Timer? _connectionTimer;
bool _showConnectionError = false;
```

### Helper Method: `_startConnectionErrorTimer()`
```dart
void _startConnectionErrorTimer() {
  _connectionTimer?.cancel(); // Cancel any existing timer
  
  // Start 3-second grace period
  _connectionTimer = Timer(const Duration(seconds: 3), () {
    if (mounted && 
        (_currentConnectionState == WebSocketConnectionState.disconnected ||
         _currentConnectionState == WebSocketConnectionState.error)) {
      setState(() {
        _showConnectionError = true;
      });
    }
  });
}
```

### Connection State Listener
```dart
webSocketService.connectionStateStream.listen((state) {
  if (state == WebSocketConnectionState.connected || 
      state == WebSocketConnectionState.connecting) {
    // Immediately hide error and cancel timer - SUCCESS IS SILENT
    _connectionTimer?.cancel();
    setState(() {
      _currentConnectionState = state;
      _showConnectionError = false;
    });
    // NO SnackBar shown for success
  } else if (state == WebSocketConnectionState.disconnected || 
             state == WebSocketConnectionState.error) {
    // Start grace period - don't show error immediately
    setState(() {
      _currentConnectionState = state;
    });
    _startConnectionErrorTimer();
  } else if (state == WebSocketConnectionState.reconnecting) {
    // Hide error during automatic reconnection
    _connectionTimer?.cancel();
    setState(() {
      _currentConnectionState = state;
      _showConnectionError = false;
    });
    // Show informational SnackBar (not a success message)
    _showConnectionStatus('正在重新连接...', isError: false);
  }
  
  // Only show SnackBar for errors
  if (state == WebSocketConnectionState.error) {
    _showConnectionStatus('连接失败，正在重试...', isError: true);
  }
});
```

### Helper Method: `_shouldShowConnectionStatus()`
```dart
bool _shouldShowConnectionStatus(WebSocketConnectionState state) {
  if (!_showConnectionError) {
    return false; // Grace period not elapsed yet
  }
  
  switch (state) {
    case WebSocketConnectionState.error:
    case WebSocketConnectionState.disconnected:
      return true; // Show after grace period
      
    case WebSocketConnectionState.connected:
    case WebSocketConnectionState.connecting:
    case WebSocketConnectionState.reconnecting:
      return false; // Hide during normal operation
  }
}
```

### AppBar Status Indicator
```dart
// Only rendered when _shouldShowConnectionStatus() returns true
if (_shouldShowConnectionStatus(connectionState))
  Container(
    // ... status indicator widget
  ),
```

### Error Banner
```dart
// Shows only after grace period for both error and disconnected states
if (_showConnectionError && 
    (connectionState == WebSocketConnectionState.error ||
     connectionState == WebSocketConnectionState.disconnected))
  Container(
    // ... error banner with contextual message and actions
  ),
```

### Lifecycle Management
```dart
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    final webSocketService = ref.read(webSocketServiceProvider);
    setState(() {
      _currentConnectionState = webSocketService.connectionState;
    });
    
    // Start grace period if initially disconnected
    if (webSocketService.connectionState == WebSocketConnectionState.disconnected ||
        webSocketService.connectionState == WebSocketConnectionState.error) {
      _startConnectionErrorTimer();
    }
    
    _loadChatHistory();
  });
}

@override
void dispose() {
  _connectionTimer?.cancel(); // Clean up timer
  // ... other cleanup
  super.dispose();
}
```

## User Experience Improvements

### Before
- AppBar always showed connection status
- "Connecting..." visible on every app start
- "Connected" label cluttered the UI
- **"Connected" SnackBar appeared on successful connection**
- "Reconnecting..." appeared during automatic retries
- Users saw unnecessary technical details
- **Error banner flashed during page loads/tab switches**

### After
- Clean AppBar during normal operation
- No status indicator when everything works
- **No "Connected" SnackBar - success is completely silent**
- Status only appears when user action may be needed
- Clear, actionable error messages
- Unobtrusive reconnection handling
- **3-second grace period prevents flashing during momentary disconnections**
- **Smooth experience during tab switches and page loads**
- **Users only see notifications when something needs attention**

## Edge Cases Handled

1. **Initial App Load**: 3-second timer starts, but usually connects before timer completes - **no success notification shown**
2. **Successful Connection**: Error flag cleared immediately, timer cancelled - **completely silent**
3. **Automatic Reconnection**: Hidden from user, handled silently - **informational SnackBar only during reconnecting state**
4. **Connection Drop**: 3-second grace period, then shows "连接已断开" with retry option
5. **Authentication Failure**: 3-second grace period, then shows "连接失败" with re-login option
6. **Network Issues**: Appropriate message based on error type after grace period
7. **Tab Switch**: Momentary disconnection doesn't trigger error (reconnects within 3 seconds) - **no success notification when reconnected**
8. **Quick Recovery**: If connection restored within 3 seconds, no error shown at all - **success is silent**
9. **Widget Disposal**: Timer properly cancelled to prevent memory leaks

## Testing Scenarios

| Scenario | Expected Behavior |
|----------|------------------|
| App starts, connects successfully | No status indicator visible (connects within 3 seconds) |
| App starts, connection fails | Error indicator appears after 3 seconds |
| Connected, then network drops | 3-second grace period, then "连接已断开" appears |
| Auto-reconnect succeeds within 3s | No error shown, status remains hidden |
| Auto-reconnect takes >3s | Error appears, then disappears when connected |
| Token expires | "连接失败" with re-login button after 3 seconds |
| User switches tabs | No error flash (reconnects within grace period) |
| User switches tabs slowly | If >3s disconnected, error appears appropriately |
| User taps retry | Timer resets, status updates based on result |
| Multiple rapid state changes | Timer properly cancelled/restarted, no race conditions |
| Widget disposed during timer | Timer cancelled, no memory leak or setState errors |
