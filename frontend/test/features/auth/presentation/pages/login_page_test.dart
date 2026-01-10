import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../../../lib/features/auth/presentation/pages/login_page.dart';

void main() {
  group('LoginPage Tests', () {
    testWidgets('should render login form correctly', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const LoginPage(),
          ),
        ),
      );

      // Check app title
      expect(find.text('登录 AssetFlow'), findsOneWidget);
      
      // Check logo and branding
      expect(find.byIcon(Icons.account_balance_wallet), findsOneWidget);
      expect(find.text('AssetFlow'), findsOneWidget);
      expect(find.text('AI 原生家庭资产配置顾问'), findsOneWidget);
      
      // Check form fields
      expect(find.byKey(const Key('phone_input')), findsOneWidget);
      expect(find.text('手机号'), findsOneWidget);
      expect(find.byIcon(Icons.phone), findsOneWidget);
      
      // Check buttons
      expect(find.byKey(const Key('send_code_button')), findsOneWidget);
      expect(find.text('发送验证码'), findsOneWidget);
      expect(find.text('匿名体验'), findsOneWidget);
      
      // Verification code field should not be visible initially
      expect(find.text('验证码'), findsNothing);
    });

    testWidgets('should show verification code field after sending code', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const LoginPage(),
          ),
        ),
      );

      // Enter phone number
      await tester.enterText(find.byKey(const Key('phone_input')), '13800138000');
      
      // Tap send code button
      await tester.tap(find.byKey(const Key('send_code_button')));
      await tester.pumpAndSettle();

      // Verification code field should now be visible
      expect(find.text('验证码'), findsOneWidget);
      expect(find.byIcon(Icons.security), findsOneWidget);
      
      // Button should change to login
      expect(find.byKey(const Key('login_button')), findsOneWidget);
      expect(find.text('登录'), findsOneWidget);
      expect(find.text('发送验证码'), findsNothing);
      
      // Should show snackbar
      expect(find.text('验证码已发送'), findsOneWidget);
    });

    testWidgets('should not send code with empty phone number', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const LoginPage(),
          ),
        ),
      );

      // Tap send code button without entering phone number
      await tester.tap(find.byKey(const Key('send_code_button')));
      await tester.pumpAndSettle();

      // Verification code field should not appear
      expect(find.text('验证码'), findsNothing);
      expect(find.text('发送验证码'), findsOneWidget);
    });

    testWidgets('should navigate to chat on anonymous login', (tester) async {
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const LoginPage(),
          ),
          GoRoute(
            path: '/chat',
            builder: (context, state) => const Scaffold(body: Text('Chat Page')),
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp.router(
            routerConfig: router,
          ),
        ),
      );

      // Tap anonymous login
      await tester.tap(find.text('匿名体验'));
      await tester.pumpAndSettle();

      // Should navigate to chat page
      expect(find.text('Chat Page'), findsOneWidget);
    });

    testWidgets('should navigate to chat after successful login', (tester) async {
      final router = GoRouter(
        routes: [
          GoRoute(
            path: '/',
            builder: (context, state) => const LoginPage(),
          ),
          GoRoute(
            path: '/chat',
            builder: (context, state) => const Scaffold(body: Text('Chat Page')),
          ),
        ],
      );

      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp.router(
            routerConfig: router,
          ),
        ),
      );

      // Enter phone number and send code
      await tester.enterText(find.byKey(const Key('phone_input')), '13800138000');
      await tester.tap(find.byKey(const Key('send_code_button')));
      await tester.pumpAndSettle();

      // Enter verification code and login
      await tester.enterText(find.byType(TextField).last, '123456');
      await tester.tap(find.byKey(const Key('login_button')));
      await tester.pumpAndSettle();

      // Should navigate to chat page
      expect(find.text('Chat Page'), findsOneWidget);
    });

    testWidgets('should not login with empty verification code', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: const LoginPage(),
          ),
        ),
      );

      // Enter phone number and send code
      await tester.enterText(find.byKey(const Key('phone_input')), '13800138000');
      await tester.tap(find.byKey(const Key('send_code_button')));
      await tester.pumpAndSettle();

      // Try to login without entering verification code
      await tester.tap(find.byKey(const Key('login_button')));
      await tester.pumpAndSettle();

      // Should still be on login page
      expect(find.text('登录 AssetFlow'), findsOneWidget);
    });
  });
}