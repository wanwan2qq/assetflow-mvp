import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:mockito/mockito.dart';

import '../../lib/core/providers/auth_provider.dart';
import '../../lib/core/models/user.dart';
import '../../lib/core/models/asset.dart';
import '../../lib/core/services/api_service.dart';

// 使用之前生成的Mock类
import 'providers/auth_provider_test.mocks.dart';

void main() {
  group('Frontend Architecture Tests', () {
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

    group('State Management', () {
      test('should initialize auth state correctly', () {
        final authState = container.read(authStateProvider);
        
        expect(authState, isA<AsyncData<User?>>());
        expect(authState.value, isNull);
      });

      test('should provide correct initial authentication status', () {
        expect(container.read(isAuthenticatedProvider), isFalse);
        expect(container.read(authTokenProvider), isNull);
      });

      test('should handle auth state changes', () async {
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
        
        // Test login
        await authNotifier.login('13800138000', '123456');
        
        final authState = container.read(authStateProvider);
        expect(authState.value, isNotNull);
        expect(authState.value!.phone, equals('13800138000'));
        expect(container.read(isAuthenticatedProvider), isTrue);
        expect(container.read(authTokenProvider), isNotNull);
        
        // Test logout
        authNotifier.logout();
        expect(container.read(authStateProvider).value, isNull);
        expect(container.read(isAuthenticatedProvider), isFalse);
        expect(container.read(authTokenProvider), isNull);
      });
    });

    group('Data Models', () {
      test('should create User model correctly', () {
        final user = User(
          id: 1,
          phone: '13800138000',
          createdAt: DateTime.now(),
        );
        
        expect(user.id, equals(1));
        expect(user.phone, equals('13800138000'));
        expect(user.deviceId, isNull);
      });

      test('should create UserAsset model correctly', () {
        final asset = UserAsset(
          id: 1,
          userId: 1,
          assetType: AssetType.realEstate,
          name: '天通苑北一区',
          value: 4500000,
          createdAt: DateTime.now(),
          updatedAt: DateTime.now(),
        );
        
        expect(asset.id, equals(1));
        expect(asset.userId, equals(1));
        expect(asset.assetType, equals(AssetType.realEstate));
        expect(asset.name, equals('天通苑北一区'));
        expect(asset.value, equals(4500000));
        expect(asset.isConfirmed, isFalse);
      });

      test('should handle AssetType enum correctly', () {
        expect(AssetType.realEstate.toString(), contains('realEstate'));
        expect(AssetType.cash.toString(), contains('cash'));
        expect(AssetType.investment.toString(), contains('investment'));
        expect(AssetType.insurance.toString(), contains('insurance'));
        expect(AssetType.liability.toString(), contains('liability'));
      });
    });

    group('Provider Dependencies', () {
      test('should have correct provider dependencies', () {
        // Test that providers can be read without errors
        expect(() => container.read(authStateProvider), returnsNormally);
        expect(() => container.read(authTokenProvider), returnsNormally);
        expect(() => container.read(isAuthenticatedProvider), returnsNormally);
      });

      test('should handle provider disposal correctly', () {
        // Create a new container to test disposal
        final mockDio2 = MockDio();
        final testContainer = ProviderContainer(
          overrides: [
            dioProvider.overrideWithValue(mockDio2),
          ],
        );
        
        // Read providers
        testContainer.read(authStateProvider);
        testContainer.read(authTokenProvider);
        testContainer.read(isAuthenticatedProvider);
        
        // Dispose should not throw
        expect(() => testContainer.dispose(), returnsNormally);
      });
    });

    group('Configuration Validation', () {
      test('should have valid project structure', () {
        // This test validates that our project structure is set up correctly
        // by ensuring key providers and models can be imported and instantiated
        
        expect(AuthState, isNotNull);
        expect(User, isNotNull);
        expect(UserAsset, isNotNull);
        expect(AssetType, isNotNull);
      });
    });
  });
}