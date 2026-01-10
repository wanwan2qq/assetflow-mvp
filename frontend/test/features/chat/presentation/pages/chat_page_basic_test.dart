import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../../lib/features/chat/presentation/pages/chat_page.dart';
import '../../../../../lib/core/services/websocket_service.dart';
import '../../../../../lib/core/providers/auth_provider.dart';
import '../../../../../lib/core/models/user.dart';

// Basic mock for testing core functionality
class BasicMockWebSocketService extends WebSocketService {
  @override
  WebSocketConnectionState get connectionState => WebSocketConnectionState.connected;

  @override
  bool get isConnected => true;

  @override
  Stream<String> get messageStream => const Stream.empty();

  @override
  Stream<WebSocketConnectionState> get connectionStateStream => 
      Stream.value(WebSocketConnectionState.connected);

  @override
  Future<void> connect(int userId, String token) async {}

  @override
  Future<void> sendMessage(String message) async {}

  @override
  Future<void> disconnect() async {}

  @override
  Future<void> reconnect() async {}

  @override
  void dispose() {}
}

class BasicMockAuthState extends AuthState {
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
  group('ChatPage Basic Tests', () {
    testWidgets('should render without crashing', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            webSocketServiceProvider.overrideWithValue(BasicMockWebSocketService()),
            authStateProvider.overrideWith(() => BasicMockAuthState()),
            authTokenProvider.overrideWith((ref) => 'test-token'),
          ],
          child: const MaterialApp(
            home: ChatPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Basic rendering test
      expect(find.byType(ChatPage), findsOneWidget);
      expect(find.text('AI 资产顾问'), findsOneWidget);
    });

    testWidgets('should have required UI elements', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            webSocketServiceProvider.overrideWithValue(BasicMockWebSocketService()),
            authStateProvider.overrideWith(() => BasicMockAuthState()),
            authTokenProvider.overrideWith((ref) => 'test-token'),
          ],
          child: const MaterialApp(
            home: ChatPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Check for key UI elements
      expect(find.byKey(const Key('chat_input')), findsOneWidget);
      expect(find.byKey(const Key('send_button')), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('should show connection status', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            webSocketServiceProvider.overrideWithValue(BasicMockWebSocketService()),
            authStateProvider.overrideWith(() => BasicMockAuthState()),
            authTokenProvider.overrideWith((ref) => 'test-token'),
          ],
          child: const MaterialApp(
            home: ChatPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Should show some connection status
      expect(find.text('已连接'), findsOneWidget);
    });

    testWidgets('should handle text input', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            webSocketServiceProvider.overrideWithValue(BasicMockWebSocketService()),
            authStateProvider.overrideWith(() => BasicMockAuthState()),
            authTokenProvider.overrideWith((ref) => 'test-token'),
          ],
          child: const MaterialApp(
            home: ChatPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Enter text in input field
      await tester.enterText(find.byKey(const Key('chat_input')), 'Test message');
      
      // Verify text was entered
      expect(find.text('Test message'), findsOneWidget);
    });

    testWidgets('should not crash when tapping buttons', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            webSocketServiceProvider.overrideWithValue(BasicMockWebSocketService()),
            authStateProvider.overrideWith(() => BasicMockAuthState()),
            authTokenProvider.overrideWith((ref) => 'test-token'),
          ],
          child: const MaterialApp(
            home: ChatPage(),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Tap refresh button - should not crash
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();

      // Still should be rendered
      expect(find.byType(ChatPage), findsOneWidget);
    });
  });
}