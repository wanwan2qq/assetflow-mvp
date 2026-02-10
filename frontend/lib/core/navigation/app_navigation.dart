import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppNavigation extends StatelessWidget {
  final Widget child;

  const AppNavigation({
    super.key,
    required this.child,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _calculateSelectedIndex(context),
        onTap: (index) => _onItemTapped(index, context),
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.chat_bubble_outline),
            activeIcon: Icon(Icons.chat_bubble),
            label: 'inW',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.account_balance_wallet_outlined),
            activeIcon: Icon(Icons.account_balance_wallet),
            label: '财富',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            activeIcon: Icon(Icons.person),
            label: '我的',
          ),
        ],
      ),
    );
  }

  static int _calculateSelectedIndex(BuildContext context) {
    final String location = GoRouterState.of(context).uri.toString();
    if (location.startsWith('/chat')) {
      return 0;
    }
    if (location.startsWith('/dashboard')) {
      return 1;
    }
    if (location.startsWith('/profile')) {
      return 2;
    }
    return 0;
  }

  void _onItemTapped(int index, BuildContext context) {
    switch (index) {
      case 0:
        GoRouter.of(context).go('/chat');
        break;
      case 1:
        GoRouter.of(context).go('/dashboard');
        break;
      case 2:
        GoRouter.of(context).go('/profile');
        break;
    }
  }
}

class AppRoutes {
  static const String login = '/login';
  static const String loginName = 'login';
  
  static const String chat = '/chat';
  static const String chatName = 'chat';
  
  static const String actions = '/actions';
  static const String actionsName = 'actions';

  static const String dashboard = '/dashboard';
  static const String dashboardName = 'dashboard';
  
  static const String profile = '/profile';
  static const String profileName = 'profile';
}