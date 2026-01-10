import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../../lib/shared/widgets/valuation_card.dart';

void main() {
  group('ValuationCard Tests', () {
    testWidgets('should render property information correctly', (tester) async {
      bool confirmCalled = false;
      bool editCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValuationCard(
              propertyName: '天通苑北一区',
              estimatedValue: 4500000,
              pricePerSqm: '¥38,000/平',
              onConfirm: () => confirmCalled = true,
              onEdit: () => editCalled = true,
            ),
          ),
        ),
      );

      // Check property name
      expect(find.text('天通苑北一区'), findsOneWidget);
      
      // Check estimated value (should be displayed in 万)
      expect(find.text('¥450万'), findsOneWidget);
      
      // Check price per sqm
      expect(find.text('¥38,000/平'), findsOneWidget);
      
      // Check title
      expect(find.text('房产估值'), findsOneWidget);
      
      // Check labels
      expect(find.text('估值'), findsOneWidget);
      expect(find.text('单价'), findsOneWidget);
      
      // Check buttons
      expect(find.text('修改'), findsOneWidget);
      expect(find.text('确认'), findsOneWidget);
      
      // Check disclaimer
      expect(find.text('* 估值基于市场数据的保守估算'), findsOneWidget);
      
      // Check icon
      expect(find.byIcon(Icons.home), findsOneWidget);
    });

    testWidgets('should call onConfirm when confirm button is tapped', (tester) async {
      bool confirmCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValuationCard(
              propertyName: '天通苑北一区',
              estimatedValue: 4500000,
              pricePerSqm: '¥38,000/平',
              onConfirm: () => confirmCalled = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('确认'));
      await tester.pumpAndSettle();

      expect(confirmCalled, isTrue);
    });

    testWidgets('should call onEdit when edit button is tapped', (tester) async {
      bool editCalled = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValuationCard(
              propertyName: '天通苑北一区',
              estimatedValue: 4500000,
              pricePerSqm: '¥38,000/平',
              onEdit: () => editCalled = true,
            ),
          ),
        ),
      );

      await tester.tap(find.text('修改'));
      await tester.pumpAndSettle();

      expect(editCalled, isTrue);
    });

    testWidgets('should handle null callbacks gracefully', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValuationCard(
              propertyName: '天通苑北一区',
              estimatedValue: 4500000,
              pricePerSqm: '¥38,000/平',
              // No callbacks provided
            ),
          ),
        ),
      );

      // Should render without errors
      expect(find.text('天通苑北一区'), findsOneWidget);
      expect(find.text('确认'), findsOneWidget);
      expect(find.text('修改'), findsOneWidget);

      // Tapping buttons should not cause errors
      await tester.tap(find.text('确认'));
      await tester.tap(find.text('修改'));
      await tester.pumpAndSettle();
    });

    testWidgets('should format large values correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValuationCard(
              propertyName: '国贸CBD豪宅',
              estimatedValue: 12000000, // 1200万
              pricePerSqm: '¥120,000/平',
            ),
          ),
        ),
      );

      expect(find.text('¥1200万'), findsOneWidget);
      expect(find.text('¥120,000/平'), findsOneWidget);
    });

    testWidgets('should have correct key for confirm button', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ValuationCard(
              propertyName: '天通苑北一区',
              estimatedValue: 4500000,
              pricePerSqm: '¥38,000/平',
            ),
          ),
        ),
      );

      expect(find.byKey(const Key('confirm_valuation_button')), findsOneWidget);
    });
  });
}