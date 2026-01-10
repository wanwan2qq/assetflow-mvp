import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../lib/features/chat/presentation/pages/chat_page.dart';
import '../../../../../lib/core/services/websocket_service.dart';
import '../../../../../lib/core/providers/auth_provider.dart';
import '../../../../../lib/core/models/user.dart';

// Simplified mock WebSocket service for testing
class SimpleWebSocketService extends WebSocketService {
  WebSocketConnectionState _state = WebSocketConnectionState.connected;
  final List<String> sentMessages = [];
  final StreamController<String> _messageController = StreamController<String>.broadcast();
  final StreamController<WebSocketConnectionState> _stateController = StreamController<WebSocketConnectionState>.broadcast();

  @override
  WebSocketConnectionState get connectionState => _state;

  @override
  bool get isConnected => _state == WebSocketConnectionState.connected;

  @override
  Stream<String> get messageStream => _messageController.stream;

  @override
  Stream<WebSocketConnectionState> get connectionStateStream => _stateController.stream;

  @override
  Future<void> connect(int userId, String token) async {
    _state = WebSocketConnectionState.connected;
    _stateController.add(_state);
  }

  @override
  Future<void> sendMessage(String message) async {
    if (!isConnected) {
      throw Exception('WebSocket not connected');
    }
    sentMessages.add(message);
  }

  @override
  Future<void> disconnect() async {
    _state = WebSocketConnectionState.disconnected;
    _stateController.add(_state);
  }

  @override
  Future<void> reconnect() async {
    await connect(1, 'test-token');
  }

  @override
  void dispose() {
    _messageController.close();
    _stateController.close();
    super.dispose();
  }

  // Test helpers
  void simulateMessage(String message) {
    _messageController.add(message);
  }

  void setState(WebSocketConnectionState state) {
    _state = state;
    _stateController.add(state);
  }
}

// Mock AuthState
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
  group('ChatPage WebSocket Simple Tests', () {
    late SimpleWebSocketService mockService;

    setUp(() {
      mockService = SimpleWebSocketService();
    });

    tearDown(() {
      mockService.dispose();
    });

    Widget createTestWidget() {
      return ProviderScope(
        overrides: [
          webSocketServiceProvider.overrideWithValue(mockService),
          authStateProvider.overrideWith(() => MockAuthState()),
          authTokenProvider.overrideWith((ref) => 'test-token'),
        ],
        child: const MaterialApp(
          home: ChatPage(),
        ),
      );
    }

    testWidgets('should render chat page', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      expect(find.byType(ChatPage), findsOneWidget);
      expect(find.text('AI 资产顾问'), findsOneWidget);
    });

    testWidgets('should show connected status', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      expect(find.text('已连接'), findsOneWidget);
    });

    testWidgets('should have input field and send button', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('chat_input')), findsOneWidget);
      expect(find.byKey(const Key('send_button')), findsOneWidget);
    });

    testWidgets('should send message when button is tapped', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      // Enter text
      await tester.enterText(find.byKey(const Key('chat_input')), 'Hello');
      
      // Tap send button
      await tester.tap(find.byKey(const Key('send_button')));
      await tester.pumpAndSettle();

      // Verify message was sent
      expect(mockService.sentMessages, contains('Hello'));
    });

    testWidgets('should display incoming messages', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      // Simulate incoming message
      mockService.simulateMessage('AI response[STREAM_END]');
      await tester.pump();

      // Should find some text content (message might be processed)
      expect(find.textContaining('AI response'), findsOneWidget);
    });

    testWidgets('should show error state', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      // Change to error state
      mockService.setState(WebSocketConnectionState.error);
      await tester.pump();

      expect(find.text('连接错误'), findsOneWidget);
    });

    testWidgets('should disable input when disconnected', (tester) async {
      // Start with disconnected state
      mockService.setState(WebSocketConnectionState.disconnected);
      
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      // Find the input field
      final inputField = find.byKey(const Key('chat_input'));
      expect(inputField, findsOneWidget);
      
      // Check if it's disabled (enabled should be false)
      final textField = tester.widget<TextField>(inputField);
      expect(textField.enabled, isFalse);
    });

    testWidgets('should enable input when connected', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      final textField = tester.widget<TextField>(find.byKey(const Key('chat_input')));
      expect(textField.enabled, isTrue);
    });

    testWidgets('should show refresh button', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('should handle refresh button tap', (tester) async {
      await tester.pumpWidget(createTestWidget());
      await tester.pumpAndSettle();

      // Tap refresh button
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();

      // Should not throw any errors
      expect(find.byType(ChatPage), findsOneWidget);
    });
  });
}