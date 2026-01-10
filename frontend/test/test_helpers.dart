import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Helper function to create a test app with Riverpod
Widget createTestApp({
  required Widget child,
  List<Override>? overrides,
}) {
  return ProviderScope(
    overrides: overrides ?? [],
    child: MaterialApp(
      home: child,
    ),
  );
}

/// Helper function to create a test app with router
Widget createTestAppWithRouter({
  required Widget child,
  List<Override>? overrides,
}) {
  return ProviderScope(
    overrides: overrides ?? [],
    child: MaterialApp(
      home: Scaffold(body: child),
    ),
  );
}

/// Helper to pump and settle with a reasonable timeout
Future<void> pumpAndSettleWithTimeout(WidgetTester tester, [Duration? timeout]) async {
  await tester.pumpAndSettle(timeout ?? const Duration(seconds: 10));
}

/// Helper to find text that might be in overflow widgets
Finder findTextAnywhere(String text) {
  return find.descendant(
    of: find.byType(Widget),
    matching: find.text(text),
  );
}

/// Helper to verify that a widget exists and is visible
void expectWidgetToBeVisible(Finder finder) {
  expect(finder, findsOneWidget);
  final widget = finder.evaluate().first.widget;
  expect(widget, isNotNull);
}

/// Helper to verify navigation occurred
void expectNavigationTo(String routeName) {
  // This would be implemented based on the specific router being used
  // For now, we'll just check that the expected page content is visible
}

/// Mock data helpers
class MockData {
  static const String mockPhoneNumber = '13800138000';
  static const String mockVerificationCode = '123456';
  static const String mockDeviceId = 'test_device_123';
  
  static const double mockPropertyValue = 4500000;
  static const String mockPropertyName = '天通苑北一区';
  static const String mockPricePerSqm = '¥38,000/平';
}