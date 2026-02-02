import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:web_socket_channel/status.dart' as status;

part 'websocket_service.g.dart';

// UTF-8 safe logging utility
String _safeLogString(String text, {int maxLength = 100}) {
  try {
    final truncated = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    // Validate UTF-8 encoding
    truncated.codeUnits;
    return truncated;
  } catch (e) {
    return 'Text (${text.length} chars) - contains invalid UTF-8 characters';
  }
}

@riverpod
WebSocketService webSocketService(WebSocketServiceRef ref) {
  return WebSocketService();
}

enum WebSocketConnectionState {
  disconnected,
  connecting,
  connected,
  reconnecting,
  error,
}

class WebSocketService {
  WebSocketChannel? _channel;
  StreamController<String>? _messageController;
  StreamController<WebSocketConnectionState>? _connectionStateController;
  WebSocketConnectionState _connectionState = WebSocketConnectionState.disconnected;
  
  // Reconnection parameters
  Timer? _reconnectTimer;
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;
  static const Duration _initialReconnectDelay = Duration(seconds: 1);
  static const Duration _maxReconnectDelay = Duration(seconds: 30);
  
  // Connection parameters for reconnection
  int? _userId;
  String? _token;
  
  // Heartbeat mechanism
  Timer? _heartbeatTimer;
  static const Duration _heartbeatInterval = Duration(seconds: 30);
  DateTime? _lastMessageReceived;

  Stream<String> get messageStream => _messageController?.stream ?? const Stream.empty();
  Stream<WebSocketConnectionState> get connectionStateStream => _connectionStateController?.stream ?? Stream.value(_connectionState);
  bool get isConnected => _connectionState == WebSocketConnectionState.connected;
  WebSocketConnectionState get connectionState => _connectionState;

  Future<void> connect(int userId, String token) async {
    _userId = userId;
    _token = token;
    
    if (_connectionState == WebSocketConnectionState.connected) {
      await disconnect();
    }

    _setConnectionState(WebSocketConnectionState.connecting);
    _resetReconnectAttempts();

    try {
      await _establishConnection();
    } catch (error) {
      print('Failed to connect WebSocket: $error');
      _setConnectionState(WebSocketConnectionState.error);
      _scheduleReconnect();
      rethrow;
    }
  }

  /// 动态获取WebSocket URL
  String _getWebSocketUrl() {
    final currentHost = Uri.base.host;
    
    // 如果是localhost，使用localhost:8000
    if (currentHost == 'localhost' || currentHost == '127.0.0.1') {
      return 'ws://localhost:8000';
    }
    
    // 如果是局域网IP，使用相同IP的8000端口
    return 'ws://$currentHost:8000';
  }

  Future<void> _establishConnection() async {
    final wsBaseUrl = _getWebSocketUrl();
    final uri = Uri.parse('$wsBaseUrl/api/v1/chat/ws/chat/$_userId?token=$_token');
    print('🔌 连接WebSocket: $uri');
    
    try {
      _channel = WebSocketChannel.connect(uri);
      
      // Initialize controllers if not already done
      _messageController ??= StreamController<String>.broadcast();
      _connectionStateController ??= StreamController<WebSocketConnectionState>.broadcast();

      // Set up stream listener
      _channel!.stream.listen(
        (data) {
          _lastMessageReceived = DateTime.now();
          if (data is String) {
            // Handle heartbeat response
            if (data == 'pong') {
              print('💓 Received heartbeat response');
              return;
            }
            
            // Handle connection confirmation
            if (data.contains('"type":"connected"') || data.contains('"type": "connected"')) {
               print('✅ Received connection confirmation from server');
               if (_connectionState != WebSocketConnectionState.connected) {
                 _setConnectionState(WebSocketConnectionState.connected);
                 _resetReconnectAttempts();
                 _startHeartbeat();
               }
               return; // Don't forward to message stream
            }
            
            // First message received means connection is truly established
            if (_connectionState != WebSocketConnectionState.connected) {
              _setConnectionState(WebSocketConnectionState.connected);
              _resetReconnectAttempts();
              _startHeartbeat();
              print('✅ WebSocket connection confirmed by first message');
            }
            
            // Validate UTF-8 encoding before processing
            try {
              data.codeUnits; // This will throw if there are invalid UTF-8 sequences
              _messageController?.add(data);
            } catch (e) {
              print('⚠️ Invalid UTF-8 in WebSocket message, attempting to clean: $e');
              try {
                // Try to clean the message by replacing invalid characters
                final cleanData = String.fromCharCodes(
                  data.runes.where((rune) => rune != 0xFFFD).toList()
                );
                _messageController?.add(cleanData);
              } catch (cleanError) {
                print('❌ Failed to clean WebSocket message: $cleanError');
                // Add error message to stream
                _messageController?.add('{"type":"error","content":"消息包含无效字符，已跳过","timestamp":"2024-01-01T00:00:00Z"}');
              }
            }
          }
        },
        onError: (error) {
          print('❌ WebSocket stream error: $error');
          _setConnectionState(WebSocketConnectionState.error);
          _handleConnectionError(error);
        },
        onDone: () {
          print('🔌 WebSocket connection closed');
          _handleConnectionClosed();
        },
      );

      // Don't set connected state immediately - wait for first message
      print('🔄 WebSocket channel created, waiting for confirmation...');
      
      // Set a timeout to detect connection failures
      Timer(const Duration(seconds: 10), () {
        if (_connectionState == WebSocketConnectionState.connecting || 
            _connectionState == WebSocketConnectionState.reconnecting) {
          print('❌ WebSocket connection timeout - likely authentication failed');
          _setConnectionState(WebSocketConnectionState.error);
          _handleConnectionError('认证失败：Token可能已过期，请重新登录', isFatal: true);
        }
      });
      
    } catch (error) {
      print('❌ WebSocket connection failed: $error');
      _setConnectionState(WebSocketConnectionState.error);
      rethrow;
    }
  }

  Future<void> sendMessage(String message) async {
    if (!isConnected || _channel == null) {
      print('❌ WebSocket sendMessage failed: not connected');
      throw Exception('WebSocket not connected');
    }

    try {
      print('🚀 WebSocket sending message: ${_safeLogString(message)}');
      _channel!.sink.add(message);
      print('✅ WebSocket message sent to sink');
    } catch (error) {
      print('❌ WebSocket sendMessage error: $error');
      _handleConnectionError(error);
      rethrow;
    }
  }

  Future<void> disconnect() async {
    _stopReconnectTimer();
    _stopHeartbeat();
    _setConnectionState(WebSocketConnectionState.disconnected);
    
    // Use 1000 (normal closure) instead of 1001 (going away) 
    // because browsers only allow 1000 or 3000-4999 range for client-initiated close
    await _channel?.sink.close(status.normalClosure);
    _channel = null;
    
    // Don't close controllers here as they might be reused
    print('WebSocket disconnected');
  }

  void dispose() {
    _stopReconnectTimer();
    _stopHeartbeat();
    _channel?.sink.close(status.normalClosure);
    _messageController?.close();
    _connectionStateController?.close();
    _messageController = null;
    _connectionStateController = null;
    _channel = null;
  }

  void _setConnectionState(WebSocketConnectionState state) {
    if (_connectionState != state) {
      _connectionState = state;
      _connectionStateController?.add(state);
      print('WebSocket connection state changed to: $state');
    }
  }

  void _handleConnectionError(dynamic error, {bool isFatal = false}) {
    _setConnectionState(WebSocketConnectionState.error);
    _messageController?.addError('Connection error: $error');
    
    if (isFatal) {
      print('⛔ Fatal error: $error - stopping reconnection attempts');
      _stopReconnectTimer();
      // Optionally clear credentials to prevent accidental retries
      // _token = null; 
    } else {
      _scheduleReconnect();
    }
  }

  void _handleConnectionClosed() {
    if (_connectionState == WebSocketConnectionState.disconnected) {
      // Intentional disconnect, don't reconnect
      return;
    }
    
    _setConnectionState(WebSocketConnectionState.error);
    _scheduleReconnect();
  }

  void _resetReconnectAttempts() {
    _reconnectAttempts = 0;
    _stopReconnectTimer();
  }

  void _scheduleReconnect() {
    if (_reconnectAttempts >= _maxReconnectAttempts) {
      print('Max reconnect attempts reached. Giving up.');
      _setConnectionState(WebSocketConnectionState.error);
      return;
    }

    if (_userId == null || _token == null) {
      print('Cannot reconnect: missing user credentials');
      return;
    }

    _stopReconnectTimer();
    
    // Exponential backoff with jitter
    final delay = Duration(
      milliseconds: (_initialReconnectDelay.inMilliseconds * 
        (1 << _reconnectAttempts)).clamp(
          _initialReconnectDelay.inMilliseconds,
          _maxReconnectDelay.inMilliseconds,
        ),
    );

    print('Scheduling reconnect attempt ${_reconnectAttempts + 1} in ${delay.inSeconds}s');
    
    _reconnectTimer = Timer(delay, () {
      _attemptReconnect();
    });
  }

  Future<void> _attemptReconnect() async {
    if (_connectionState == WebSocketConnectionState.disconnected) {
      return; // User disconnected intentionally
    }

    _reconnectAttempts++;
    _setConnectionState(WebSocketConnectionState.reconnecting);
    
    try {
      await _establishConnection();
      print('Reconnection connection initiated for attempt $_reconnectAttempts (waiting for confirmation)');
    } catch (error) {
      print('Reconnection attempt $_reconnectAttempts failed: $error');
      _scheduleReconnect();
    }
  }

  void _stopReconnectTimer() {
    _reconnectTimer?.cancel();
    _reconnectTimer = null;
  }

  void _startHeartbeat() {
    _stopHeartbeat();
    _lastMessageReceived = DateTime.now();
    
    _heartbeatTimer = Timer.periodic(_heartbeatInterval, (timer) {
      _sendHeartbeat();
    });
  }

  void _stopHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
  }

  void _sendHeartbeat() {
    if (!isConnected) {
      return;
    }

    // Check if we've received any message recently
    final now = DateTime.now();
    if (_lastMessageReceived != null && 
        now.difference(_lastMessageReceived!) > Duration(seconds: 60)) {
      print('No messages received for too long, connection might be dead');
      _handleConnectionError('Heartbeat timeout');
      return;
    }

    try {
      print('💓 Sending heartbeat ping');
      _channel?.sink.add('ping');
    } catch (error) {
      print('❌ Failed to send heartbeat: $error');
      _handleConnectionError(error);
    }
  }

  // Manual reconnect method for user-initiated reconnection
  Future<void> reconnect() async {
    if (_userId == null || _token == null) {
      throw Exception('Cannot reconnect: no previous connection credentials');
    }

    _stopReconnectTimer();
    _resetReconnectAttempts();
    
    await disconnect();
    await Future.delayed(const Duration(milliseconds: 500));
    await connect(_userId!, _token!);
  }
}