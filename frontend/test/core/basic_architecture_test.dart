import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../lib/core/models/user.dart';
import '../../lib/core/models/asset.dart';

void main() {
  group('Basic Frontend Architecture Tests', () {
    group('Data Models', () {
      test('should create and serialize User model', () {
        final user = User(
          id: 1,
          phone: '13800138000',
          createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
        );
        
        expect(user.id, equals(1));
        expect(user.phone, equals('13800138000'));
        expect(user.deviceId, isNull);
        
        // Test JSON serialization
        final json = user.toJson();
        expect(json['id'], equals(1));
        expect(json['phone'], equals('13800138000'));
        
        // Test JSON deserialization
        final userFromJson = User.fromJson(json);
        expect(userFromJson.id, equals(user.id));
        expect(userFromJson.phone, equals(user.phone));
      });

      test('should create and serialize UserAsset model', () {
        final asset = UserAsset(
          id: 1,
          userId: 1,
          assetType: AssetType.realEstate,
          name: '天通苑北一区',
          value: 4500000,
          createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
          updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        );
        
        expect(asset.id, equals(1));
        expect(asset.userId, equals(1));
        expect(asset.assetType, equals(AssetType.realEstate));
        expect(asset.name, equals('天通苑北一区'));
        expect(asset.value, equals(4500000));
        expect(asset.isConfirmed, isFalse);
        
        // Test JSON serialization
        final json = asset.toJson();
        expect(json['id'], equals(1));
        expect(json['assetType'], equals('real_estate'));
        expect(json['name'], equals('天通苑北一区'));
        expect(json['value'], equals(4500000));
        
        // Test JSON deserialization
        final assetFromJson = UserAsset.fromJson(json);
        expect(assetFromJson.id, equals(asset.id));
        expect(assetFromJson.assetType, equals(asset.assetType));
        expect(assetFromJson.name, equals(asset.name));
        expect(assetFromJson.value, equals(asset.value));
      });

      test('should handle AssetType enum serialization', () {
        expect(AssetType.realEstate.name, equals('realEstate'));
        expect(AssetType.cash.name, equals('cash'));
        expect(AssetType.investment.name, equals('investment'));
        expect(AssetType.insurance.name, equals('insurance'));
        expect(AssetType.liability.name, equals('liability'));
      });

      test('should create PortfolioHealth model', () {
        final portfolioHealth = PortfolioHealth(
          netWorth: 3500000,
          realEstateRatio: 0.857,
          liquidityRatio: 2.1,
          riskWarnings: [
            RiskWarning(
              type: 'HIGH_RE_CONCENTRATION',
              message: '房产占比过高',
              severity: 'high',
            ),
          ],
        );
        
        expect(portfolioHealth.netWorth, equals(3500000));
        expect(portfolioHealth.realEstateRatio, closeTo(0.857, 0.001));
        expect(portfolioHealth.liquidityRatio, closeTo(2.1, 0.1));
        expect(portfolioHealth.riskWarnings.length, equals(1));
        expect(portfolioHealth.riskWarnings.first.type, equals('HIGH_RE_CONCENTRATION'));
      });
    });

    group('Riverpod Integration', () {
      test('should create ProviderContainer without errors', () {
        expect(() => ProviderContainer(), returnsNormally);
      });

      test('should dispose ProviderContainer without errors', () {
        final container = ProviderContainer();
        expect(() => container.dispose(), returnsNormally);
      });
    });

    group('Project Structure Validation', () {
      test('should have all required model classes', () {
        // Verify that all model classes can be instantiated
        expect(User, isNotNull);
        expect(UserProfile, isNotNull);
        expect(UserAsset, isNotNull);
        expect(PortfolioHealth, isNotNull);
        expect(RiskWarning, isNotNull);
        expect(AssetType, isNotNull);
      });

      test('should have freezed models working correctly', () {
        final user1 = User(
          id: 1,
          phone: '13800138000',
          createdAt: DateTime.now(),
        );
        
        final user2 = user1.copyWith(phone: '13800138001');
        
        expect(user1.id, equals(user2.id));
        expect(user1.phone, equals('13800138000'));
        expect(user2.phone, equals('13800138001'));
        expect(user1 != user2, isTrue);
      });
    });
  });
}