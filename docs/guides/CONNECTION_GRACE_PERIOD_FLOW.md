# Connection Status Grace Period Flow

## Overview
This document explains the 3-second grace period implementation that prevents error banner flashing during page loads and tab switches.

## State Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Initial State                            │
│  _currentConnectionState = disconnected                      │
│  _showConnectionError = false                                │
│  _connectionTimer = null                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Connection State Change Event                   │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │ Connected/        │       │ Disconnected/     │
    │ Connecting        │       │ Error             │
    └───────────────────┘       └───────────────────┘
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │ Cancel Timer      │       │ Start 3s Timer    │
    │ Hide Error        │       │ Update State      │
    │ (Immediate)       │       │ (Don't Show Yet)  │
    └───────────────────┘       └───────────────────┘
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │ Clean UI          │       │ Wait 3 seconds... │
    │ No Banner         │       └───────────────────┘
    └───────────────────┘                   │
                                ┌───────────┴───────────┐
                                │                       │
                                ▼                       ▼
                    ┌───────────────────┐   ┌───────────────────┐
                    │ Still Error/      │   │ Connected Before  │
                    │ Disconnected?     │   │ Timer Expired?    │
                    └───────────────────┘   └───────────────────┘
                                │                       │
                                ▼                       ▼
                    ┌───────────────────┐   ┌───────────────────┐
                    │ Show Error Banner │   │ Timer Cancelled   │
                    │ _showError = true │   │ No Banner Shown   │
                    └───────────────────┘   └───────────────────┘
```

## Detailed State Transitions

### Scenario 1: Normal Connection (No Notification)
```
1. App starts → disconnected
2. Timer starts (3s countdown)
3. Connection established in 0.5s → connected
4. Timer cancelled immediately
5. _showConnectionError remains false
6. NO SnackBar shown
7. Result: Clean UI, completely silent success
```

### Scenario 2: Tab Switch (No Notification)
```
1. User switches tab → momentarily disconnected
2. Timer starts (3s countdown)
3. Tab becomes active → reconnecting
4. Timer cancelled
5. Connection restored in 1s → connected
6. _showConnectionError remains false
7. NO SnackBar shown for success
8. Result: Smooth transition, silent reconnection
```

### Scenario 3: Actual Connection Failure (Error Shown)
```
1. Network drops → disconnected
2. Timer starts (3s countdown)
3. 3 seconds pass, still disconnected
4. Timer fires → _showConnectionError = true
5. Error banner appears
6. User sees: "连接已断开" with retry button
7. Result: User informed of actual problem
```

### Scenario 4: Slow Reconnection (Error Briefly Shown)
```
1. Connection drops → disconnected
2. Timer starts (3s countdown)
3. 3 seconds pass → error banner appears
4. Auto-reconnect succeeds at 4s → connected
5. Timer cancelled, _showConnectionError = false
6. Error banner disappears immediately
7. Result: Brief error shown, then cleared
```

### Scenario 5: Authentication Error (Error Shown)
```
1. Token expires → error state
2. Timer starts (3s countdown)
3. 3 seconds pass, still error
4. Timer fires → _showConnectionError = true
5. Error banner appears
6. User sees: "连接失败" with re-login button
7. Result: User prompted to re-authenticate
```

## Code Flow

### 1. State Change Detection
```dart
webSocketService.connectionStateStream.listen((state) {
  if (state == connected || state == connecting) {
    // Path A: Good state - hide error immediately
    _connectionTimer?.cancel();
    setState(() {
      _currentConnectionState = state;
      _showConnectionError = false;
    });
  } else if (state == disconnected || state == error) {
    // Path B: Bad state - start grace period
    setState(() {
      _currentConnectionState = state;
    });
    _startConnectionErrorTimer();
  } else if (state == reconnecting) {
    // Path C: Recovering - hide error but keep trying
    _connectionTimer?.cancel();
    setState(() {
      _currentConnectionState = state;
      _showConnectionError = false;
    });
  }
});
```

### 2. Grace Period Timer
```dart
void _startConnectionErrorTimer() {
  _connectionTimer?.cancel(); // Prevent multiple timers
  
  _connectionTimer = Timer(const Duration(seconds: 3), () {
    // Only show error if still in bad state after 3 seconds
    if (mounted && 
        (_currentConnectionState == disconnected ||
         _currentConnectionState == error)) {
      setState(() {
        _showConnectionError = true;
      });
    }
  });
}
```

### 3. UI Visibility Check
```dart
bool _shouldShowConnectionStatus(WebSocketConnectionState state) {
  if (!_showConnectionError) {
    return false; // Grace period not elapsed
  }
  
  // Only show for error/disconnected states after grace period
  return state == error || state == disconnected;
}
```

### 4. Banner Rendering
```dart
if (_showConnectionError && 
    (connectionState == error || connectionState == disconnected)) {
  // Render error banner with contextual message
}
```

## Timing Examples

| Event | Time | State | Timer | Show Error? |
|-------|------|-------|-------|-------------|
| App starts | 0s | disconnected | Started | No |
| Connecting | 0.2s | connecting | Cancelled | No |
| Connected | 0.5s | connected | - | No |
| **Result** | | | | **No flash!** |

| Event | Time | State | Timer | Show Error? |
|-------|------|-------|-------|-------------|
| Tab switch | 0s | disconnected | Started | No |
| Reconnecting | 0.8s | reconnecting | Cancelled | No |
| Connected | 1.5s | connected | - | No |
| **Result** | | | | **No flash!** |

| Event | Time | State | Timer | Show Error? |
|-------|------|-------|-------|-------------|
| Network drop | 0s | disconnected | Started | No |
| Still disconnected | 3s | disconnected | Fired | Yes |
| User sees error | 3s+ | disconnected | - | Yes |
| **Result** | | | | **Error shown after 3s** |

## Benefits

1. **No Flashing**: Momentary disconnections don't trigger error UI
2. **Smooth UX**: Tab switches and page loads feel seamless
3. **Silent Success**: No notifications when connection works properly
4. **Informative**: Real failures are still communicated to users
5. **Responsive**: Errors disappear immediately when connection restored
6. **Robust**: Handles rapid state changes without race conditions
7. **Clean**: No memory leaks, proper timer cleanup
8. **Unobtrusive**: Users only see messages when action is needed

## Edge Cases Handled

- **Multiple rapid state changes**: Timer cancelled and restarted appropriately
- **Widget disposal during timer**: `mounted` check prevents setState errors
- **Timer cleanup**: Cancelled in dispose to prevent memory leaks
- **Race conditions**: Only one timer active at a time
- **Initial load**: Timer starts but usually connects before expiry
- **Slow networks**: Error shown after grace period, cleared when connected
