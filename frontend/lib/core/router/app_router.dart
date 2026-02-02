import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/chat/presentation/pages/chat_page.dart';
import '../../features/dashboard/presentation/pages/dashboard_page.dart';
import '../../features/profile/presentation/pages/profile_page.dart';
import '../../features/actions/presentation/pages/action_plans_page.dart';
import '../navigation/app_navigation.dart';

part 'app_router.g.dart';

@riverpod
GoRouter appRouter(AppRouterRef ref) {
  return GoRouter(
    initialLocation: AppRoutes.login,
    routes: [
      GoRoute(
        path: AppRoutes.login,
        name: AppRoutes.loginName,
        builder: (context, state) => const LoginPage(),
      ),
      ShellRoute(
        builder: (context, state, child) => AppNavigation(child: child),
        routes: [
          GoRoute(
            path: AppRoutes.chat,
            name: AppRoutes.chatName,
            builder: (context, state) => const ChatPage(),
          ),
          GoRoute(
            path: AppRoutes.actions,
            name: AppRoutes.actionsName,
            builder: (context, state) => const ActionPlansPage(),
          ),
          GoRoute(
            path: AppRoutes.dashboard,
            name: AppRoutes.dashboardName,
            builder: (context, state) => const DashboardPage(),
          ),
          GoRoute(
            path: AppRoutes.profile,
            name: AppRoutes.profileName,
            builder: (context, state) => const ProfilePage(),
          ),
        ],
      ),
    ],
  );
}