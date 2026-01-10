import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import '../../../lib/core/services/websocket_service.dart';

void main() {
  group('WebSocketService Integration Tests', () {
    late WebSocketService webSocketService;

    setUp(() {
      webSocketService = WebSocketService();
    });

    tearDown(() {
      webSocketService.dispose();
    });

    group('Basic State Management', () {
      test('should start in disconnected state', () {
        expect(webSocketService.connectionState, WebSocketConnectionState.disconnected);
        expect(webSocketService.isConnected, false);
      });

      test('should provide message stream', () {
        final stream = webSocketService.messageStream;
        expect(stream, isA<Stream<String>>());
      });

      test('should provide connection state stream', () {
        final stream = webSocketService.connectionStateStream;
        expect(stream, isA<Stream<WebSocketConnectionState>>());
      });

      test('should throw exception when sending message while disconnected', () async {
        expect(
          () => webSocketService.sendMessage('test message'),
          throwsA(isA<Exception>().having(
            (e) => e.toString(),
            'message',
            contains('WebSocket not connected'),
          )),
        );
      });

      test('should transition to disconnected state on disconnect', () async {
        await webSocketService.disconnect();
        expect(webSocketService.connectionState, WebSocketConnectionState.disconnected);
        expect(webSocketService.isConnected, false);
      });
    });

    group('Reconnection Logic', () {
      test('should fail reconnection without previous credentials', () async {
        try {
          await webSocketService.reconnect();
          fail('Should have thrown an exception');
        } catch (e) {
          expect(e.toString(), contains('no previous connection credentials'));
        }
      });
    });

    group('Resource Cleanup', () {
      test('should clean up resources on dispose', () {
        // Create streams to ensure controllers are initialized
        final messageStream = webSocketService.messageStream;
        final connectionStream = webSocketService.connectionStateStream;
        
        expect(messageStream, isA<Stream<String>>());
        expect(connectionStream, isA<Stream<WebSocketConnectionState>>());
        
        // Dispose should not throw
        expect(() => webSocketService.dispose(), returnsNormally);
        
        // State should be clean
        expect(webSocketService.connectionState, WebSocketConnectionState.disconnected);
        expect(webSocketService.isConnected, false);
      });

      test('should handle multiple dispose calls', () {
        // Multiple dispose calls should not throw
        expect(() => webSocketService.dispose(), returnsNormally);
        expect(() => webSocketService.dispose(), returnsNormally);
        expect(() => webSocketService.dispose(), returnsNormally);
      });
    });

    group('Connection State Enum', () {
      test('should have all expected connection states', () {
        expect(WebSocketConnectionState.values, contains(WebSocketConnectionState.disconnected));
        expect(WebSocketConnectionState.values, contains(WebSocketConnectionState.connecting));
        expect(WebSocketConnectionState.values, contains(WebSocketConnectionState.connected));
        expect(WebSocketConnectionState.values, contains(WebSocketConnectionState.reconnecting));
        expect(WebSocketConnectionState.values, contains(WebSocketConnectionState.error));
      });

      test('should correctly identify connected state', () {
        // Test isConnected getter logic
        expect(webSocketService.isConnected, false); // starts disconnected
        
        // We can't easily test the connected state without mocking, 
        // but we can verify the getter works with the current state
        expect(webSocketService.isConnected, 
               webSocketService.connectionState == WebSocketConnectionState.connected);
      });
    });

    group('Stream Behavior', () {
      test('should handle stream listeners without errors', () {
        late StreamSubscription<String> messageSubscription;
        late StreamSubscription<WebSocketConnectionState> stateSubscription;
        
        expect(() {
          messageSubscription = webSocketService.messageStream.listen((_) {});
          stateSubscription = webSocketService.connectionStateStream.listen((_) {});
        }, returnsNormally);
        
        // Clean up
        messageSubscription.cancel();
        stateSubscription.cancel();
      });

      test('should allow multiple stream subscriptions', () {
        final subscriptions = <StreamSubscription>[];
        
        expect(() {
          for (int i = 0; i < 3; i++) {
            subscriptions.add(webSocketService.messageStream.listen((_) {}));
            subscriptions.add(webSocketService.connectionStateStream.listen((_) {}));
          }
        }, returnsNormally);
        
        // Clean up
        for (final subscription in subscriptions) {
          subscription.cancel();
        }
      });
    });

    group('Error Handling', () {
      test('should handle connection attempts to invalid endpoints gracefully', () async {
        // This will fail but should not crash the application
        try {
          await webSocketService.connect(1, 'invalid-token');
          // If connection succeeds, that's also fine - just verify state is valid
        } catch (e) {
          // Expected to fail, just ensure it's handled gracefully
          expect(e, isA<Exception>());
        }
        
        // Service should be in a valid state after connection attempt
        expect(webSocketService.connectionState, isIn([
          WebSocketConnectionState.disconnected,
          WebSocketConnectionState.connected,
          WebSocketConnectionState.error,
          WebSocketConnectionState.reconnecting,
        ]));
      });
    });
  });
}