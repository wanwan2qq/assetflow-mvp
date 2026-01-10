import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../../../lib/core/navigation/app_navigation.dart';

void main() {
  group('AppNavigation Tests', () {
    testWidgets('should render bottom navigation bar with correct items', (tester) async {
      final router = GoRouter(
        routes: [
          ShellRoute(
            builder: (context, state, child) => AppNavigation(child: child),
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => const Scaffold(body: Text('Chat Page')),
              ),
              GoRoute(
                path: '/dashboard',
                builder: (context, state) => const Scaffold(body: Text('Dashboard Page')),
              ),
              GoRoute(
                path: '/profile',
                builder: (context, state) => const Scaffold(body: Text('Profile Page')),
              ),
            ],
          ),
        ],
        initialLocation: '/chat',
      );

      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
        ),
      );

      await tester.pumpAndSettle();

      // Should have bottom navigation bar
      expect(find.byType(BottomNavigationBar), findsOneWidget);
      
      // Check navigation item labels (they should be present in the widget tree)
      expect(find.text('聊天'), findsOneWidget);
      expect(find.text('仪表板'), findsOneWidget);
      expect(find.text('个人'), findsOneWidget);
      
      // Check navigation item icons
      expect(find.byIcon(Icons.chat), findsOneWidget);
      expect(find.byIcon(Icons.dashboard), findsOneWidget);
      expect(find.byIcon(Icons.person), findsOneWidget);
    });

    testWidgets('should calculate correct selected index for chat route', (tester) async {
      final router = GoRouter(
        routes: [
          ShellRoute(
            builder: (context, state, child) => AppNavigation(child: child),
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => const Scaffold(body: Text('Chat Page')),
              ),
              GoRoute(
                path: '/dashboard',
                builder: (context, state) => const Scaffold(body: Text('Dashboard Page')),
              ),
              GoRoute(
                path: '/profile',
                builder: (context, state) => const Scaffold(body: Text('Profile Page')),
              ),
            ],
          ),
        ],
        initialLocation: '/chat',
      );

      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
        ),
      );

      await tester.pumpAndSettle();

      final bottomNavBar = tester.widget<BottomNavigationBar>(find.byType(BottomNavigationBar));
      expect(bottomNavBar.currentIndex, equals(0)); // Chat is index 0
    });

    testWidgets('should calculate correct selected index for dashboard route', (tester) async {
      final router = GoRouter(
        routes: [
          ShellRoute(
            builder: (context, state, child) => AppNavigation(child: child),
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => const Scaffold(body: Text('Chat Page')),
              ),
              GoRoute(
                path: '/dashboard',
                builder: (context, state) => const Scaffold(body: Text('Dashboard Page')),
              ),
              GoRoute(
                path: '/profile',
                builder: (context, state) => const Scaffold(body: Text('Profile Page')),
              ),
            ],
          ),
        ],
        initialLocation: '/dashboard',
      );

      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
        ),
      );

      await tester.pumpAndSettle();

      final bottomNavBar = tester.widget<BottomNavigationBar>(find.byType(BottomNavigationBar));
      expect(bottomNavBar.currentIndex, equals(1)); // Dashboard is index 1
    });

    testWidgets('should calculate correct selected index for profile route', (tester) async {
      final router = GoRouter(
        routes: [
          ShellRoute(
            builder: (context, state, child) => AppNavigation(child: child),
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => const Scaffold(body: Text('Chat Page')),
              ),
              GoRoute(
                path: '/dashboard',
                builder: (context, state) => const Scaffold(body: Text('Dashboard Page')),
              ),
              GoRoute(
                path: '/profile',
                builder: (context, state) => const Scaffold(body: Text('Profile Page')),
              ),
            ],
          ),
        ],
        initialLocation: '/profile',
      );

      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
        ),
      );

      await tester.pumpAndSettle();

      final bottomNavBar = tester.widget<BottomNavigationBar>(find.byType(BottomNavigationBar));
      expect(bottomNavBar.currentIndex, equals(2)); // Profile is index 2
    });

    testWidgets('should navigate when tapping navigation items', (tester) async {
      final router = GoRouter(
        routes: [
          ShellRoute(
            builder: (context, state, child) => AppNavigation(child: child),
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => const Scaffold(body: Text('Chat Page')),
              ),
              GoRoute(
                path: '/dashboard',
                builder: (context, state) => const Scaffold(body: Text('Dashboard Page')),
              ),
              GoRoute(
                path: '/profile',
                builder: (context, state) => const Scaffold(body: Text('Profile Page')),
              ),
            ],
          ),
        ],
        initialLocation: '/chat',
      );

      await tester.pumpWidget(
        MaterialApp.router(
          routerConfig: router,
        ),
      );

      await tester.pumpAndSettle();

      // Initially on chat page
      expect(find.text('Chat Page'), findsOneWidget);
      
      // Tap dashboard tab
      await tester.tap(find.text('仪表板'));
      await tester.pumpAndSettle();
      
      expect(find.text('Dashboard Page'), findsOneWidget);
      expect(find.text('Chat Page'), findsNothing);
      
      // Tap profile tab
      await tester.tap(find.text('个人'));
      await tester.pumpAndSettle();
      
      expect(find.text('Profile Page'), findsOneWidget);
      expect(find.text('Dashboard Page'), findsNothing);
      
      // Tap chat tab
      await tester.tap(find.text('聊天'));
      await tester.pumpAndSettle();
      
      expect(find.text('Chat Page'), findsOneWidget);
      expect(find.text('Profile Page'), findsNothing);
    });
  });
}