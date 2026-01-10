import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../lib/core/router/app_router.dart';
import '../../../lib/core/navigation/app_navigation.dart';

void main() {
  group('AppRouter Tests', () {
    late ProviderContainer container;

    setUp(() {
      container = ProviderContainer();
    });

    tearDown(() {
      container.dispose();
    });

    testWidgets('should create router with correct initial route', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: Consumer(
            builder: (context, ref, child) {
              final router = ref.watch(appRouterProvider);
              return MaterialApp.router(
                routerConfig: router,
              );
            },
          ),
        ),
      );
      
      await tester.pumpAndSettle();
      
      // Should show login page initially
      expect(find.text('登录 AssetFlow'), findsOneWidget);
    });

    testWidgets('should navigate to login page initially', (tester) async {
      final router = container.read(appRouterProvider);
      
      await tester.pumpWidget(
        ProviderScope(
          parent: container,
          child: MaterialApp.router(
            routerConfig: router,
          ),
        ),
      );

      await tester.pumpAndSettle();
      
      // Should show login page
      expect(find.text('登录 AssetFlow'), findsOneWidget);
      expect(find.byKey(const Key('phone_input')), findsOneWidget);
    });

    testWidgets('should navigate between routes correctly', (tester) async {
      final router = container.read(appRouterProvider);
      
      await tester.pumpWidget(
        ProviderScope(
          parent: container,
          child: MaterialApp.router(
            routerConfig: router,
          ),
        ),
      );

      await tester.pumpAndSettle();
      
      // Navigate to chat
      router.go('/chat');
      await tester.pumpAndSettle();
      
      expect(find.text('AI 资产顾问'), findsOneWidget);
      
      // Navigate to dashboard
      router.go('/dashboard');
      await tester.pumpAndSettle();
      
      expect(find.text('资产仪表板'), findsOneWidget);
      
      // Navigate to profile
      router.go('/profile');
      await tester.pumpAndSettle();
      
      expect(find.text('个人中心'), findsOneWidget);
    });

    test('should have all required routes defined', () {
      final container = ProviderContainer();
      addTearDown(container.dispose);
      
      final router = container.read(appRouterProvider);
      final routes = router.configuration.routes;
      
      expect(routes.length, equals(2)); // Login route + Shell route
      
      // Check login route exists
      final loginRoute = routes.firstWhere((route) => route is GoRoute && (route as GoRoute).path == AppRoutes.login) as GoRoute;
      expect(loginRoute.path, equals('/login'));
      
      // Check shell route with nested routes
      final shellRoute = routes.firstWhere((route) => route is ShellRoute) as ShellRoute;
      expect(shellRoute.routes.length, equals(3)); // chat, dashboard, profile
      
      final chatRoute = shellRoute.routes.firstWhere((route) => route is GoRoute && (route as GoRoute).path == AppRoutes.chat) as GoRoute;
      expect(chatRoute.path, equals('/chat'));
      
      final dashboardRoute = shellRoute.routes.firstWhere((route) => route is GoRoute && (route as GoRoute).path == AppRoutes.dashboard) as GoRoute;
      expect(dashboardRoute.path, equals('/dashboard'));
      
      final profileRoute = shellRoute.routes.firstWhere((route) => route is GoRoute && (route as GoRoute).path == AppRoutes.profile) as GoRoute;
      expect(profileRoute.path, equals('/profile'));
    });
  });
}