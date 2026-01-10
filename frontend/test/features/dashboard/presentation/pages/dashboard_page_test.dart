import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:assetflow_frontend/features/dashboard/presentation/pages/dashboard_page.dart';

void main() {
  group('DashboardPage Widget Tests', () {
    testWidgets('should create DashboardPage widget without errors', (WidgetTester tester) async {
      // Test that the widget can be created and rendered
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      // Verify the widget is created
      expect(find.byType(DashboardPage), findsOneWidget);
    });

    testWidgets('should display app bar with title', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      // Wait for initial render
      await tester.pump();

      // Verify app bar and title
      expect(find.byType(AppBar), findsOneWidget);
      expect(find.text('资产仪表板'), findsOneWidget);
    });

    testWidgets('should display floating action button', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      await tester.pump();

      // Verify floating action button
      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.byIcon(Icons.add), findsOneWidget);
    });

    testWidgets('should display refresh button in app bar', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      await tester.pump();

      // Verify refresh button
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('should have RefreshIndicator for pull-to-refresh', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      await tester.pump();

      // Verify RefreshIndicator exists
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('should display main content sections', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      await tester.pump();

      // Verify main layout components
      expect(find.byType(SingleChildScrollView), findsOneWidget);
      expect(find.byType(Column), findsAtLeastNWidgets(1));
    });
  });

  group('DashboardPage Interaction Tests', () {
    testWidgets('should handle floating action button tap', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      await tester.pump();

      // Tap the floating action button
      await tester.tap(find.byType(FloatingActionButton));
      await tester.pumpAndSettle();

      // Verify dialog appears (add asset dialog)
      expect(find.byType(AlertDialog), findsOneWidget);
      expect(find.text('添加资产'), findsOneWidget);
    });

    testWidgets('should handle refresh button tap', (WidgetTester tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const DashboardPage(),
          ),
        ),
      );

      await tester.pump();

      // Tap the refresh button
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pump();

      // Test passes if no errors occur during refresh
      expect(find.byType(DashboardPage), findsOneWidget);
    });
  });
}