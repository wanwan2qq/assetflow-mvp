import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../../lib/shared/widgets/asset_card.dart';

void main() {
  group('AssetCard Widget Tests', () {
    testWidgets('AssetCard displays basic information correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AssetCard(
              name: '北京朝阳区公寓',
              value: 5000000,
              assetType: 'real_estate',
              riskLevel: 'low',
              tags: const ['residential', 'beijing'],
              privacyMode: false,
            ),
          ),
        ),
      );

      // Verify asset name is displayed
      expect(find.text('北京朝阳区公寓'), findsOneWidget);
      
      // Verify formatted value is displayed
      expect(find.text('¥500.0万'), findsOneWidget);
      
      // Verify risk level is displayed
      expect(find.text('低风险'), findsOneWidget);
      
      // Verify tags are displayed
      expect(find.text('residential'), findsOneWidget);
      expect(find.text('beijing'), findsOneWidget);
    });

    testWidgets('AssetCard privacy mode masks values correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AssetCard(
              name: '私密资产',
              value: 15000000, // 1500万
              assetType: 'investment',
              privacyMode: true,
            ),
          ),
        ),
      );

      // Verify value is masked
      expect(find.text('1000万+'), findsOneWidget);
      expect(find.text('¥1500.0万'), findsNothing);
    });

    testWidgets('AssetCard shows correct icon and color for different asset types', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Column(
              children: const [
                AssetCard(
                  name: '房产',
                  value: 1000000,
                  assetType: 'real_estate',
                ),
                AssetCard(
                  name: '现金',
                  value: 100000,
                  assetType: 'cash',
                ),
                AssetCard(
                  name: '投资',
                  value: 500000,
                  assetType: 'investment',
                ),
              ],
            ),
          ),
        ),
      );

      // Verify different asset types are rendered
      expect(find.byIcon(Icons.home), findsOneWidget); // real_estate
      expect(find.byIcon(Icons.account_balance_wallet), findsOneWidget); // cash
      expect(find.byIcon(Icons.trending_up), findsOneWidget); // investment
    });

    testWidgets('AssetCard handles tap callbacks', (WidgetTester tester) async {
      bool tapped = false;
      bool edited = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: AssetCard(
              name: '测试资产',
              value: 1000000,
              assetType: 'cash',
              onTap: () => tapped = true,
              onEdit: () => edited = true,
            ),
          ),
        ),
      );

      // Test main tap
      await tester.tap(find.byType(AssetCard));
      await tester.pump();
      expect(tapped, isTrue);

      // Test edit button tap
      await tester.tap(find.byIcon(Icons.edit));
      await tester.pump();
      expect(edited, isTrue);
    });
  });
}