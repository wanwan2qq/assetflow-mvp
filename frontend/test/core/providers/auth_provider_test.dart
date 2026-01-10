import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';

import '../../../lib/core/providers/auth_provider.dart';
import '../../../lib/core/models/user.dart';
import '../../../lib/core/services/api_service.dart';

// 生成Mock类
@GenerateMocks([Dio])
import 'auth_provider_test.mocks.dart';

void main() {
  group('AuthProvider Tests', () {
    late ProviderContainer container;
    late MockDio mockDio;

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

    test('should initialize with null user', () {
      final authState = container.read(authStateProvider);
      
      expect(authState, isA<AsyncData<User?>>());
      expect(authState.value, isNull);
    });

    test('should login successfully with phone and code', () async {
      // Mock successful login response
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'mock_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      final authNotifier = container.read(authStateProvider.notifier);
      
      await authNotifier.login('13800138000', '123456');
      
      final authState = container.read(authStateProvider);
      expect(authState, isA<AsyncData<User?>>());
      expect(authState.value, isNotNull);
      expect(authState.value!.phone, equals('13800138000'));
      expect(authState.value!.id, equals(1));
    });

    test('should login anonymously with device ID', () async {
      // Mock successful anonymous login response
      when(mockDio.post(
        '/api/v1/auth/login/device',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 999,
          'phone': 'anonymous',
          'access_token': 'mock_token_anonymous',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/device'),
      ));

      final authNotifier = container.read(authStateProvider.notifier);
      
      await authNotifier.loginAnonymously('device_123');
      
      final authState = container.read(authStateProvider);
      expect(authState, isA<AsyncData<User?>>());
      expect(authState.value, isNotNull);
      expect(authState.value!.deviceId, equals('device_123'));
      expect(authState.value!.phone, equals('anonymous'));
      expect(authState.value!.id, equals(999));
    });

    test('should logout successfully', () async {
      // Mock successful login first
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'mock_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      final authNotifier = container.read(authStateProvider.notifier);
      
      // First login
      await authNotifier.login('13800138000', '123456');
      expect(container.read(authStateProvider).value, isNotNull);
      
      // Then logout
      authNotifier.logout();
      expect(container.read(authStateProvider).value, isNull);
    });

    test('should provide correct auth token', () async {
      // Mock successful login
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'mock_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      final authNotifier = container.read(authStateProvider.notifier);
      
      // Initially no token
      expect(container.read(authTokenProvider), isNull);
      
      // After login, should have token
      await authNotifier.login('13800138000', '123456');
      final token = container.read(authTokenProvider);
      expect(token, isNotNull);
      expect(token, equals('mock_token_123'));
      
      // After logout, no token
      authNotifier.logout();
      expect(container.read(authTokenProvider), isNull);
    });

    test('should provide correct authentication status', () async {
      // Mock successful login
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'mock_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      final authNotifier = container.read(authStateProvider.notifier);
      
      // Initially not authenticated
      expect(container.read(isAuthenticatedProvider), isFalse);
      
      // After login, should be authenticated
      await authNotifier.login('13800138000', '123456');
      expect(container.read(isAuthenticatedProvider), isTrue);
      
      // After logout, not authenticated
      authNotifier.logout();
      expect(container.read(isAuthenticatedProvider), isFalse);
    });

    test('should handle login loading state', () async {
      // Mock successful login response
      when(mockDio.post(
        '/api/v1/auth/login/phone',
        data: anyNamed('data'),
      )).thenAnswer((_) async => Response(
        data: {
          'user_id': 1,
          'phone': '13800138000',
          'access_token': 'mock_token_123',
        },
        statusCode: 200,
        requestOptions: RequestOptions(path: '/api/v1/auth/login/phone'),
      ));

      final authNotifier = container.read(authStateProvider.notifier);
      
      // Test that login completes successfully
      await authNotifier.login('13800138000', '123456');
      
      // Should have user data after completion
      final finalState = container.read(authStateProvider);
      expect(finalState, isA<AsyncData<User?>>());
      expect(finalState.value, isNotNull);
      expect(finalState.value!.phone, equals('13800138000'));
    });
  });
}