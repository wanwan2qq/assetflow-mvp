import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:assetflow_frontend/shared/widgets/sp_quadrant_chart.dart';
import 'package:assetflow_frontend/core/models/asset.dart';

void main() {
  group('SPQuadrantChart Tests', () {
    testWidgets('should create SPQuadrantChart widget without errors', (WidgetTester tester) async {
      const portfolioHealth = PortfolioHealth(
        netWorth: 1000000,
        realEstateRatio: 0.4,
        liquidityRatio: 3.0,
        riskWarnings: [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SPQuadrantChart(portfolioHealth: portfolioHealth),
          ),
        ),
      );

      // Verify the widget is created without errors
      expect(find.byType(SPQuadrantChart), findsOneWidget);
    });

    testWidgets('should display chart title', (WidgetTester tester) async {
      const portfolioHealth = PortfolioHealth(
        netWorth: 1000000,
        realEstateRatio: 0.4,
        liquidityRatio: 3.0,
        riskWarnings: [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SPQuadrantChart(portfolioHealth: portfolioHealth),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify chart title
      expect(find.text('标准普尔四象限分析'), findsOneWidget);
    });

    testWidgets('should display card container', (WidgetTester tester) async {
      const portfolioHealth = PortfolioHealth(
        netWorth: 1000000,
        realEstateRatio: 0.4,
        liquidityRatio: 3.0,
        riskWarnings: [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SPQuadrantChart(portfolioHealth: portfolioHealth),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify card container
      expect(find.byType(Card), findsOneWidget);
    });

    testWidgets('should handle zero net worth', (WidgetTester tester) async {
      const portfolioHealth = PortfolioHealth(
        netWorth: 0,
        realEstateRatio: 0,
        liquidityRatio: 0,
        riskWarnings: [],
      );

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SPQuadrantChart(portfolioHealth: portfolioHealth),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Should still display the chart for educational purposes
      expect(find.byType(SPQuadrantChart), findsOneWidget);
      expect(find.text('标准普尔四象限分析'), findsOneWidget);
    });

    testWidgets('should accept onTap callback', (WidgetTester tester) async {
      const portfolioHealth = PortfolioHealth(
        netWorth: 1000000,
        realEstateRatio: 0.4,
        liquidityRatio: 3.0,
        riskWarnings: [],
      );

      bool tapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SPQuadrantChart(
              portfolioHealth: portfolioHealth,
              onTap: () {
                tapped = true;
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Verify the callback parameter is accepted
      expect(find.byType(SPQuadrantChart), findsOneWidget);
    });
  });
}