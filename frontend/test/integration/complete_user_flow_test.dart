import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';

import '../core/providers/auth_provider_test.mocks.dart';
import '../../lib/main.dart';
import '../../lib/core/services/api_service.dart';
import '../../lib/core/providers/auth_provider.dart';
import '../../lib/core/providers/asset_provider.dart';
import '../../lib/core/services/websocket_service.dart';
import '../../lib/core/models/user.dart';
import '../../lib/core/models/asset.dart';

// Generate mocks for integration testing
@GenerateMocks([Dio, WebSocketService])
void main() {
  group('Complete User Flow Integration Tests', () {
    late MockDio mockDio;
    late MockWebSocketService mockWebSocketService;
    late ProviderContainer container;

    setUp(() {
      mockDio = MockDio();
      mockWebSocketService = MockWebSocketService();
      
      container = ProviderContainer(
        overrides: [
          dioProvider.overrideWithValue(mockDio),
          webSocketServiceProvider.overrideWithValue(mockWebSocketService),
        ],
      );
    });

    tearDown(() {
      container.dispose();
    });

    testWidgets('Complete asset onboarding flow', (WidgetTester tester) async {
      // Mock successful login response
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'test_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      // Mock user profile response
      when(mockDio.get('/api/v1/profiles/1')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': {
            'id': 1,
            'user_id': 1,
            'age_range': '30-40',
            'family_structure': 'married_with_kids',
            'risk_preference': 'moderate',
            'monthly_expense': 15000.0,
          },
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/profiles/1'),
      ));

      // Mock empty assets initially
      when(mockDio.get('/api/v1/assets/1')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': [],
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      // Mock portfolio health with empty portfolio
      when(mockDio.get('/api/v1/assets/1/portfolio/health')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': {
            'net_worth': 0.0,
            'real_estate_ratio': 0.0,
            'liquidity_ratio': 0.0,
            'risk_warnings': [],
          },
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1/portfolio/health'),
      ));

      // Mock WebSocket connection
      when(mockWebSocketService.connect(any, any)).thenAnswer((_) async {});
      when(mockWebSocketService.isConnected).thenReturn(true);
      when(mockWebSocketService.connectionState).thenReturn(WebSocketConnectionState.connected);
      when(mockWebSocketService.messageStream).thenAnswer((_) => Stream.fromIterable([
        '{"type": "system", "content": "欢迎使用AssetFlow！", "timestamp": "2024-01-01T00:00:00Z"}',
      ]));
      when(mockWebSocketService.connectionStateStream).thenAnswer((_) => Stream.value(WebSocketConnectionState.connected));

      // Build the app with provider overrides
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
            webSocketServiceProvider.overrideWithValue(mockWebSocketService),
          ],
          child: const AssetFlowApp(),
        ),
      );

      // Step 1: Should start at login page
      expect(find.text('AssetFlow'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget); // Phone input

      // Step 2: Enter phone number and login
      await tester.enterText(find.byType(TextField), '13800138000');
      await tester.tap(find.text('发送验证码'));
      await tester.pumpAndSettle();

      // Should show code input
      expect(find.text('验证码'), findsOneWidget);
      
      // Enter verification code
      final codeFields = find.byType(TextField);
      expect(codeFields, findsWidgets);
      await tester.enterText(codeFields.last, '123456');
      await tester.tap(find.text('登录'));
      await tester.pumpAndSettle();

      // Step 3: Should navigate to chat page after successful login
      expect(find.byKey(const Key('chat_page')), findsOneWidget);
      expect(find.text('欢迎使用AssetFlow！'), findsOneWidget);

      // Step 4: Test chat interaction
      final chatInput = find.byKey(const Key('chat_input'));
      final sendButton = find.byKey(const Key('send_button'));
      
      expect(chatInput, findsOneWidget);
      expect(sendButton, findsOneWidget);

      // Mock chat response with UI components
      when(mockWebSocketService.sendMessage(any)).thenAnswer((_) async {});
      
      // Simulate AI response with valuation card
      when(mockWebSocketService.messageStream).thenAnswer((_) => Stream.fromIterable([
        '{"type": "chunk", "content": "我来帮您评估房产价值。", "timestamp": "2024-01-01T00:00:00Z"}',
        '{"type": "chunk", "content": "<WIDGET:VALUATION_CARD>", "timestamp": "2024-01-01T00:00:00Z"}',
        '{"type": "complete", "content": "我来帮您评估房产价值。<WIDGET:VALUATION_CARD>", "ui_components": [{"type": "VALUATION_CARD", "data": {"price": 4500000, "area": 120, "community": "天通苑北一区"}, "position": 0}], "timestamp": "2024-01-01T00:00:00Z"}',
      ]));

      // Send property information
      await tester.enterText(chatInput, '我有套北京天通苑的房子，120平米');
      await tester.tap(sendButton);
      await tester.pumpAndSettle();

      // Should show valuation card
      expect(find.byType(ValuationCard), findsOneWidget);
      expect(find.text('天通苑北一区'), findsOneWidget);

      // Step 5: Confirm valuation and create asset
      when(mockDio.post(
        '/api/v1/assets/1',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {'success': true, 'data': {'id': 1}},
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      // Mock updated assets list after creation
      when(mockDio.get('/api/v1/assets/1')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'user_id': 1,
              'asset_type': 'real_estate',
              'name': '北京天通苑北一区',
              'value': 4500000.0,
              'is_confirmed': true,
              'extra_data': {
                'area': 120.0,
                'city': '北京',
                'community': '天通苑北一区',
              },
              'created_at': '2024-01-01T00:00:00Z',
              'updated_at': '2024-01-01T00:00:00Z',
            }
          ],
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      // Tap confirm button on valuation card
      await tester.tap(find.text('确认估值'));
      await tester.pumpAndSettle();

      // Step 6: Navigate to dashboard to see assets
      await tester.tap(find.byIcon(Icons.dashboard));
      await tester.pumpAndSettle();

      // Should show dashboard with asset data
      expect(find.byKey(const Key('dashboard_page')), findsOneWidget);
      expect(find.text('资产总览'), findsOneWidget);

      // Should show pie chart with asset distribution
      expect(find.byType(PieChart), findsOneWidget);
      expect(find.text('房产'), findsOneWidget);
      expect(find.text('¥4,500,000'), findsOneWidget);

      // Step 7: Add more assets through chat
      await tester.tap(find.byIcon(Icons.chat));
      await tester.pumpAndSettle();

      // Mock response for adding cash asset
      when(mockWebSocketService.messageStream).thenAnswer((_) => Stream.fromIterable([
        '{"type": "chunk", "content": "好的，我已记录您的现金资产。", "timestamp": "2024-01-01T00:00:00Z"}',
        '{"type": "complete", "content": "好的，我已记录您的现金资产。", "ui_components": [], "timestamp": "2024-01-01T00:00:00Z"}',
      ]));

      await tester.enterText(chatInput, '我还有50万现金存款');
      await tester.tap(sendButton);
      await tester.pumpAndSettle();

      // Mock updated assets with cash
      when(mockDio.get('/api/v1/assets/1')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'user_id': 1,
              'asset_type': 'real_estate',
              'name': '北京天通苑北一区',
              'value': 4500000.0,
              'is_confirmed': true,
              'extra_data': {'area': 120.0, 'city': '北京', 'community': '天通苑北一区'},
              'created_at': '2024-01-01T00:00:00Z',
              'updated_at': '2024-01-01T00:00:00Z',
            },
            {
              'id': 2,
              'user_id': 1,
              'asset_type': 'cash',
              'name': '银行存款',
              'value': 500000.0,
              'is_confirmed': true,
              'extra_data': {'account_type': 'savings'},
              'created_at': '2024-01-01T00:00:00Z',
              'updated_at': '2024-01-01T00:00:00Z',
            }
          ],
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      // Mock updated portfolio health
      when(mockDio.get('/api/v1/assets/1/portfolio/health')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': {
            'net_worth': 5000000.0,
            'real_estate_ratio': 0.9, // 90%
            'liquidity_ratio': 5.56,
            'risk_warnings': [
              {
                'type': 'HIGH_RE_CONCENTRATION',
                'message': '房产占比过高，建议适当分散投资',
                'severity': 'high',
              }
            ],
          },
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1/portfolio/health'),
      ));

      // Step 8: Check updated dashboard
      await tester.tap(find.byIcon(Icons.dashboard));
      await tester.pumpAndSettle();

      // Should show updated asset distribution
      expect(find.text('¥5,000,000'), findsOneWidget); // Total net worth
      expect(find.text('现金'), findsOneWidget);

      // Step 9: Test portfolio analysis with recommendations
      when(mockWebSocketService.messageStream).thenAnswer((_) => Stream.fromIterable([
        '{"type": "chunk", "content": "根据分析，您的房产占比过高。", "timestamp": "2024-01-01T00:00:00Z"}',
        '{"type": "chunk", "content": "<WIDGET:PORTFOLIO_CHART>", "timestamp": "2024-01-01T00:00:00Z"}',
        '{"type": "chunk", "content": "<WIDGET:ACTION_CARD data=\\"{\\\"type\\\": \\\"investment\\\", \\\"title\\\": \\\"投资建议\\\", \\\"description\\\": \\\"考虑增加股票投资\\\"}\\\">", "timestamp": "2024-01-01T00:00:00Z"}',
        '{"type": "complete", "content": "根据分析，您的房产占比过高。<WIDGET:PORTFOLIO_CHART><WIDGET:ACTION_CARD>", "ui_components": [{"type": "PORTFOLIO_CHART", "data": {"chart_type": "pie"}, "position": 0}, {"type": "ACTION_CARD", "data": {"type": "investment", "title": "投资建议", "description": "考虑增加股票投资"}, "position": 1}], "timestamp": "2024-01-01T00:00:00Z"}',
      ]));

      await tester.tap(find.byIcon(Icons.chat));
      await tester.pumpAndSettle();

      await tester.enterText(chatInput, '请分析我的资产配置');
      await tester.tap(sendButton);
      await tester.pumpAndSettle();

      // Should show portfolio chart and action cards
      expect(find.byType(PortfolioChart), findsOneWidget);
      expect(find.byType(ActionCard), findsOneWidget);
      expect(find.text('投资建议'), findsOneWidget);
      expect(find.text('考虑增加股票投资'), findsOneWidget);

      // Step 10: Test error handling
      when(mockDio.get('/api/v1/assets/1')).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: '/api/v1/assets/1'),
          message: 'Network error',
        ),
      );

      await tester.tap(find.byIcon(Icons.dashboard));
      await tester.pumpAndSettle();

      // Should show error state
      expect(find.text('加载失败'), findsOneWidget);

      // Verify all mocked calls were made
      verify(mockDio.post('/api/v1/auth/login/phone', data: anyNamed('data'))).called(1);
      verify(mockDio.get('/api/v1/assets/1')).called(atLeast(1));
      verify(mockWebSocketService.connect(any, any)).called(1);
      verify(mockWebSocketService.sendMessage(any)).called(atLeast(1));
    });

    testWidgets('Error handling throughout user flow', (WidgetTester tester) async {
      // Test login failure
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenThrow(
        DioException(
          requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
          response: Response(
            statusCode: 401,
            data: {'detail': 'Invalid credentials'},
            requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
          ),
        ),
      );

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
            webSocketServiceProvider.overrideWithValue(mockWebSocketService),
          ],
          child: const AssetFlowApp(),
        ),
      );

      // Try to login with invalid credentials
      await tester.enterText(find.byType(TextField), '13800138000');
      await tester.tap(find.text('发送验证码'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).last, '000000');
      await tester.tap(find.text('登录'));
      await tester.pumpAndSettle();

      // Should show error message
      expect(find.text('登录失败'), findsOneWidget);
      
      // Should remain on login page
      expect(find.byType(TextField), findsWidgets);
    });

    testWidgets('WebSocket connection handling', (WidgetTester tester) async {
      // Mock successful login
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'test_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      when(mockDio.get('/api/v1/assets/1')).thenAnswer((_) async => Response(
        data: {'success': true, 'data': []},
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      when(mockDio.get('/api/v1/assets/1/portfolio/health')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': {
            'net_worth': 0.0,
            'real_estate_ratio': 0.0,
            'liquidity_ratio': 0.0,
            'risk_warnings': [],
          },
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1/portfolio/health'),
      ));

      // Test WebSocket connection states
      when(mockWebSocketService.connect(any, any)).thenAnswer((_) async {});
      when(mockWebSocketService.connectionStateStream).thenAnswer((_) => Stream.fromIterable([
        WebSocketConnectionState.connecting,
        WebSocketConnectionState.connected,
        WebSocketConnectionState.error,
        WebSocketConnectionState.reconnecting,
        WebSocketConnectionState.connected,
      ]));
      when(mockWebSocketService.messageStream).thenAnswer((_) => const Stream.empty());

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
            webSocketServiceProvider.overrideWithValue(mockWebSocketService),
          ],
          child: const AssetFlowApp(),
        ),
      );

      // Login first
      await tester.enterText(find.byType(TextField), '13800138000');
      await tester.tap(find.text('发送验证码'));
      await tester.pumpAndSettle();

      await tester.enterText(find.byType(TextField).last, '123456');
      await tester.tap(find.text('登录'));
      await tester.pumpAndSettle();

      // Should be on chat page
      expect(find.byKey(const Key('chat_page')), findsOneWidget);

      // Test connection state indicators
      when(mockWebSocketService.isConnected).thenReturn(false);
      when(mockWebSocketService.connectionState).thenReturn(WebSocketConnectionState.connecting);
      await tester.pump();

      // Should show connecting indicator
      expect(find.text('连接中...'), findsOneWidget);

      // Test connected state
      when(mockWebSocketService.isConnected).thenReturn(true);
      when(mockWebSocketService.connectionState).thenReturn(WebSocketConnectionState.connected);
      await tester.pump();

      // Should enable input
      final textField = tester.widget<TextField>(find.byKey(const Key('chat_input')));
      expect(textField.enabled, isTrue);

      // Test error state
      when(mockWebSocketService.isConnected).thenReturn(false);
      when(mockWebSocketService.connectionState).thenReturn(WebSocketConnectionState.error);
      await tester.pump();

      // Should show error indicator and disable input
      expect(find.text('连接失败'), findsOneWidget);
      final disabledTextField = tester.widget<TextField>(find.byKey(const Key('chat_input')));
      expect(disabledTextField.enabled, isFalse);
    });
  });
}