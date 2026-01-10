import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../lib/features/chat/presentation/pages/chat_page.dart';
import '../../../../../lib/core/services/websocket_service.dart';
import '../../../../../lib/core/providers/auth_provider.dart';
import '../../../../../lib/core/models/user.dart';
import '../../../../../lib/shared/widgets/valuation_card.dart';

// Simple mock WebSocket service for testing
class MockWebSocketService extends WebSocketService {
  final StreamController<String> _mockMessageController = StreamController<String>.broadcast();
  final StreamController<WebSocketConnectionState> _mockConnectionController = StreamController<WebSocketConnectionState>.broadcast();
  
  WebSocketConnectionState _mockState = WebSocketConnectionState.disconnected;
  bool _mockConnected = false;
  final List<String> sentMessages = [];
  bool _isConnecting = false;

  @override
  Stream<String> get messageStream => _mockMessageController.stream;

  @override
  Stream<WebSocketConnectionState> get connectionStateStream => _mockConnectionController.stream;

  @override
  WebSocketConnectionState get connectionState => _mockState;

  @override
  bool get isConnected => _mockConnected;

  @override
  Future<void> connect(int userId, String token) async {
    _isConnecting = true;
    _mockState = WebSocketConnectionState.connecting;
    _mockConnected = false;
    _mockConnectionController.add(_mockState);
    
    // Simulate connection delay
    await Future.delayed(const Duration(milliseconds: 50));
    
    _mockState = WebSocketConnectionState.connected;
    _mockConnected = true;
    _isConnecting = false;
    _mockConnectionController.add(_mockState);
  }

  @override
  Future<void> sendMessage(String message) async {
    if (!_mockConnected) {
      throw Exception('WebSocket not connected');
    }
    sentMessages.add(message);
  }

  @override
  Future<void> disconnect() async {
    _mockState = WebSocketConnectionState.disconnected;
    _mockConnected = false;
    _isConnecting = false;
    _mockConnectionController.add(_mockState);
  }

  @override
  Future<void> reconnect() async {
    await disconnect();
    await Future.delayed(const Duration(milliseconds: 10));
    await connect(1, 'test-token');
  }

  @override
  void dispose() {
    _mockMessageController.close();
    _mockConnectionController.close();
    super.dispose();
  }

  // Test helper methods
  void simulateMessage(String message) {
    if (_mockMessageController.hasListener) {
      _mockMessageController.add(message);
    }
  }

  void simulateConnectionError() {
    _mockState = WebSocketConnectionState.error;
    _mockConnected = false;
    _isConnecting = false;
    _mockConnectionController.add(_mockState);
  }

  void simulateReconnecting() {
    _mockState = WebSocketConnectionState.reconnecting;
    _mockConnected = false;
    _isConnecting = false;
    _mockConnectionController.add(_mockState);
  }

  // Additional helper for testing
  bool get isConnecting => _isConnecting;
  
  // Force state change for testing
  void forceState(WebSocketConnectionState state, bool connected) {
    _mockState = state;
    _mockConnected = connected;
    _mockConnectionController.add(state);
  }
}

// Mock AuthState notifier
class MockAuthState extends AuthState {
  @override
  AsyncValue<User?> build() {
    return AsyncValue.data(
      User(
        id: 1,
        phone: '13800138000',
        createdAt: DateTime.now(),
      ),
    );
  }
}

void main() {
  group('ChatPage WebSocket Integration Tests', () {
    late MockWebSocketService mockWebSocketService;

    setUp(() {
      mockWebSocketService = MockWebSocketService();
    });

    tearDown(() {
      mockWebSocketService.dispose();
    });

    Widget createTestWidget({MockWebSocketService? customService}) {
      final service = customService ?? mockWebSocketService;
      return ProviderScope(
        overrides: [
          webSocketServiceProvider.overrideWithValue(service),
          authStateProvider.overrideWith(() => MockAuthState()),
          authTokenProvider.overrideWith((ref) => 'test-token'),
        ],
        child: const MaterialApp(
          home: ChatPage(),
        ),
      );
    }

    group('Connection Management', () {
      testWidgets('should show connection status in app bar', (tester) async {
        await tester.pumpWidget(createTestWidget());
        
        // Wait for initial connection
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Should show connected status
        expect(find.text('已连接'), findsOneWidget);
      });

      testWidgets('should update UI when connection state changes', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Initially should be connected
        expect(find.text('已连接'), findsOneWidget);

        // Simulate connection error
        mockWebSocketService.simulateConnectionError();
        await tester.pump();

        // Should show error status
        expect(find.text('连接错误'), findsOneWidget);
      });

      testWidgets('should disable input when not connected', (tester) async {
        // Create a service that starts disconnected
        final disconnectedService = MockWebSocketService();
        disconnectedService.forceState(WebSocketConnectionState.disconnected, false);

        await tester.pumpWidget(createTestWidget(customService: disconnectedService));
        await tester.pumpAndSettle();

        final inputFinder = find.byKey(const Key('chat_input'));
        expect(inputFinder, findsOneWidget);
        
        final textField = tester.widget<TextField>(inputFinder);
        expect(textField.enabled, isFalse);

        final sendButton = tester.widget<IconButton>(find.byKey(const Key('send_button')));
        expect(sendButton.onPressed, isNull);
        
        disconnectedService.dispose();
      });

      testWidgets('should enable input when connected', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        final textField = tester.widget<TextField>(find.byKey(const Key('chat_input')));
        expect(textField.enabled, isTrue);

        final sendButton = tester.widget<IconButton>(find.byKey(const Key('send_button')));
        expect(sendButton.onPressed, isNotNull);
      });
    });

    group('Message Handling', () {
      testWidgets('should send message via WebSocket when connected', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Enter message and send
        await tester.enterText(find.byKey(const Key('chat_input')), 'Test message');
        await tester.tap(find.byKey(const Key('send_button')), warnIfMissed: false);
        await tester.pumpAndSettle();

        // Verify message was sent
        expect(mockWebSocketService.sentMessages, contains('Test message'));
      });

      testWidgets('should display incoming messages', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Simulate incoming message
        mockWebSocketService.simulateMessage('Hello from AI[STREAM_END]');
        await tester.pump();
        await tester.pumpAndSettle();

        // Should display the message
        expect(find.textContaining('Hello from AI'), findsOneWidget);
      });

      testWidgets('should handle streaming messages', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Simulate streaming message parts
        mockWebSocketService.simulateMessage('Hello ');
        await tester.pump();
        
        mockWebSocketService.simulateMessage('from ');
        await tester.pump();
        
        mockWebSocketService.simulateMessage('AI[STREAM_END]');
        await tester.pump();
        await tester.pumpAndSettle();

        // Should display the complete message
        expect(find.textContaining('Hello from AI'), findsOneWidget);
      });

      testWidgets('should parse and display embedded widgets', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Simulate message with embedded widget
        mockWebSocketService.simulateMessage('Here is your valuation: <WIDGET:VALUATION_CARD>[STREAM_END]');
        await tester.pump();
        await tester.pumpAndSettle();

        // Should display the valuation card
        expect(find.byType(ValuationCard), findsOneWidget);
      });
    });

    group('Error Recovery', () {
      testWidgets('should handle WebSocket send errors gracefully', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Disconnect to simulate send error
        await mockWebSocketService.disconnect();
        await tester.pump();

        // Try to send message
        await tester.enterText(find.byKey(const Key('chat_input')), 'Test message');
        await tester.tap(find.byKey(const Key('send_button')), warnIfMissed: false);
        await tester.pumpAndSettle();

        // Should show error snackbar
        expect(find.byType(SnackBar), findsOneWidget);
      });

      testWidgets('should attempt reconnection when refresh button is tapped', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Simulate error state
        mockWebSocketService.simulateConnectionError();
        await tester.pump();

        // Tap refresh button
        await tester.tap(find.byIcon(Icons.refresh));
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Should be connected again
        expect(mockWebSocketService.connectionState, WebSocketConnectionState.connected);
      });
    });

    group('Connection State Indicators', () {
      testWidgets('should show correct icon for different connection states', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Test connected state
        expect(find.byIcon(Icons.wifi), findsOneWidget);

        // Test error state
        mockWebSocketService.simulateConnectionError();
        await tester.pump();
        expect(find.byIcon(Icons.error), findsOneWidget);

        // Test reconnecting state
        mockWebSocketService.simulateReconnecting();
        await tester.pump();
        expect(find.byIcon(Icons.wifi_off), findsOneWidget);
      });

      testWidgets('should show loading indicator when connecting', (tester) async {
        // Create a service that starts in connecting state
        final connectingService = MockWebSocketService();
        connectingService.forceState(WebSocketConnectionState.connecting, false);

        await tester.pumpWidget(createTestWidget(customService: connectingService));
        await tester.pump();

        // Should show loading indicator in send button
        expect(find.byType(CircularProgressIndicator), findsOneWidget);
        
        connectingService.dispose();
      });
    });

    group('Message Display and Interaction', () {
      testWidgets('should clear input after sending message', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Enter message and send
        await tester.enterText(find.byKey(const Key('chat_input')), 'Test message');
        await tester.tap(find.byKey(const Key('send_button')), warnIfMissed: false);
        await tester.pumpAndSettle();

        // Input should be cleared
        final textField = tester.widget<TextField>(find.byKey(const Key('chat_input')));
        expect(textField.controller?.text, isEmpty);
      });

      testWidgets('should handle refresh button to clear messages', (tester) async {
        await tester.pumpWidget(createTestWidget());
        await tester.pumpAndSettle(const Duration(milliseconds: 100));

        // Add a message first
        mockWebSocketService.simulateMessage('Test message[STREAM_END]');
        await tester.pump();
        await tester.pumpAndSettle();
        
        // Verify message is displayed
        expect(find.textContaining('Test message'), findsOneWidget);

        // When connected, refresh should clear messages
        await tester.tap(find.byIcon(Icons.refresh));
        await tester.pumpAndSettle();

        // Message should be gone
        expect(find.textContaining('Test message'), findsNothing);
      });
    });
  });
}