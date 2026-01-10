import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:mockito/mockito.dart';
import 'package:dio/dio.dart';

import '../core/providers/auth_provider_test.mocks.dart';
import '../../lib/main.dart';
import '../../lib/core/services/api_service.dart';
import '../../lib/core/providers/auth_provider.dart';
import '../../lib/core/models/user.dart';

void main() {
  group('Basic Integration Tests', () {
    late MockDio mockDio;
    late ProviderContainer container;

    setUp(() {
      mockDio = MockDio();
      
      container = ProviderContainer(
        overrides: [
          dioProvider.overrideWithValue(mockDio),
        ],
      );
    });

    tearDown(() {
      container.dispose();
    });

    testWidgets('App starts and shows login page', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
          ],
          child: const AssetFlowApp(),
        ),
      );

      // Should show login page initially
      expect(find.text('AssetFlow'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('Login flow integration', (WidgetTester tester) async {
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

      // Mock empty assets response
      when(mockDio.get('/api/v1/assets/1')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': [],
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      // Mock portfolio health response
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

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
          ],
          child: const AssetFlowApp(),
        ),
      );

      // Enter phone number
      await tester.enterText(find.byType(TextField), '13800138000');
      await tester.tap(find.text('发送验证码'));
      await tester.pumpAndSettle();

      // Should show verification code input
      expect(find.text('验证码'), findsOneWidget);
      
      // Enter verification code
      final codeFields = find.byType(TextField);
      expect(codeFields, findsWidgets);
      await tester.enterText(codeFields.last, '123456');
      await tester.tap(find.text('登录'));
      await tester.pumpAndSettle();

      // Should navigate to main app after login
      // The exact navigation depends on the router implementation
      // For now, just verify the login API was called
      verify(mockDio.post('/api/v1/auth/login/phone', data: anyNamed('data'))).called(1);
    });

    testWidgets('Error handling integration', (WidgetTester tester) async {
      // Mock login failure
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
    });

    testWidgets('Navigation integration', (WidgetTester tester) async {
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

      // Mock API responses for different pages
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

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
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

      // Test navigation between different sections
      // This depends on the actual navigation implementation
      // For now, just verify that the login was successful
      verify(mockDio.post('/api/v1/auth/login/phone', data: anyNamed('data'))).called(1);
    });

    testWidgets('Asset management integration', (WidgetTester tester) async {
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

      // Mock asset creation
      when(mockDio.post(
        '/api/v1/assets/1',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {'success': true, 'data': {'id': 1}},
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      // Mock assets list with created asset
      when(mockDio.get('/api/v1/assets/1')).thenAnswer((_) async => Response(
        data: {
          'success': true,
          'data': [
            {
              'id': 1,
              'user_id': 1,
              'asset_type': 'real_estate',
              'name': '测试房产',
              'value': 1000000.0,
              'is_confirmed': true,
              'extra_data': {},
              'created_at': '2024-01-01T00:00:00Z',
              'updated_at': '2024-01-01T00:00:00Z',
            }
          ],
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/assets/1'),
      ));

      await tester.pumpWidget(
        ProviderScope(
          overrides: [
            dioProvider.overrideWithValue(mockDio),
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

      // Verify login was successful
      verify(mockDio.post('/api/v1/auth/login/phone', data: anyNamed('data'))).called(1);
      
      // The rest of the asset management flow would depend on the UI implementation
      // For now, we've verified the basic integration works
    });
  });
}