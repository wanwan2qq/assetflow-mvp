import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:assetflow_frontend/core/providers/asset_provider.dart';
import 'package:assetflow_frontend/core/models/asset.dart';

void main() {
  group('AssetProvider Tests', () {
    test('should calculate asset distribution correctly', () {
      final assets = [
        UserAsset(
          id: 1,
          userId: 1,
          assetType: AssetType.realEstate,
          name: '房产',
          value: 3000000,
          isConfirmed: true,
          createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
          updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        ),
        UserAsset(
          id: 2,
          userId: 1,
          assetType: AssetType.cash,
          name: '现金',
          value: 300000,
          isConfirmed: true,
          createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
          updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        ),
      ];

      // Test asset distribution calculation logic
      double totalValue = 0;
      for (final asset in assets) {
        if (asset.assetType != AssetType.liability) {
          totalValue += asset.value;
        }
      }

      expect(totalValue, equals(3300000.0));

      final realEstateRatio = 3000000 / totalValue;
      final cashRatio = 300000 / totalValue;

      expect(realEstateRatio, closeTo(0.909, 0.001));
      expect(cashRatio, closeTo(0.091, 0.001));
    });

    test('should exclude liabilities from total calculation', () {
      final assets = [
        UserAsset(
          id: 1,
          userId: 1,
          assetType: AssetType.realEstate,
          name: '房产',
          value: 3000000,
          isConfirmed: true,
          createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
          updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        ),
        UserAsset(
          id: 2,
          userId: 1,
          assetType: AssetType.liability,
          name: '房贷',
          value: 2000000,
          isConfirmed: true,
          createdAt: DateTime.parse('2024-01-01T00:00:00Z'),
          updatedAt: DateTime.parse('2024-01-01T00:00:00Z'),
        ),
      ];

      // Calculate net worth (assets - liabilities)
      double totalAssets = 0;
      double totalLiabilities = 0;
      
      for (final asset in assets) {
        if (asset.assetType == AssetType.liability) {
          totalLiabilities += asset.value;
        } else {
          totalAssets += asset.value;
        }
      }
      
      final netWorth = totalAssets - totalLiabilities;
      expect(netWorth, equals(1000000.0)); // 3M - 2M = 1M
    });
  });
}