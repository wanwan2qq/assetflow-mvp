import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fl_chart/fl_chart.dart';

import 'package:assetflow_frontend/shared/widgets/portfolio_chart.dart';
import 'package:assetflow_frontend/core/models/asset.dart';

void main() {
  group('PortfolioChart Tests', () {
    testWidgets('should display empty state when no assets', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PortfolioChart(assets: []),
          ),
        ),
      );

      expect(find.text('暂无资产数据'), findsOneWidget);
      expect(find.byType(PieChart), findsNothing);
    });

    testWidgets('should display pie chart with asset data', (WidgetTester tester) async {
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

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PortfolioChart(assets: assets),
          ),
        ),
      );

      expect(find.byType(PieChart), findsOneWidget);
      expect(find.text('总资产'), findsOneWidget);
      expect(find.text('¥330.0万'), findsOneWidget);
      expect(find.text('房产'), findsOneWidget);
      expect(find.text('现金'), findsOneWidget);
      expect(find.text('¥300.0万'), findsOneWidget);
      expect(find.text('¥30.0万'), findsOneWidget);
    });
  });
}