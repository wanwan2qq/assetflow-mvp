import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/asset_provider.dart';
import '../../../../core/models/asset.dart';

class FactSheetDrawer extends ConsumerWidget {
  const FactSheetDrawer({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final assetsAsync = ref.watch(assetListProvider);

    return Drawer(
      child: Column(
        children: [
          UserAccountsDrawerHeader(
            accountName: Text(authState.value?.phone ?? '用户'),
            accountEmail: Text(authState.value?.id.toString() ?? ''),
            currentAccountPicture: const CircleAvatar(
              child: Icon(Icons.person, size: 40),
            ),
            decoration: BoxDecoration(
              color: Theme.of(context).primaryColor,
            ),
          ),
          ListTile(
            leading: const Icon(Icons.account_balance_wallet),
            title: const Text('资产概览'),
            onTap: () {
              context.pop(); // Close drawer
              context.go('/dashboard'); // Go to Wealth tab
            },
          ),
          const Divider(),
          Expanded(
            child: assetsAsync.when(
              data: (assets) {
                if (assets.isEmpty) {
                  return const Center(child: Text('暂无资产记录'));
                }
                
                // Group assets by type for summary
                final Map<String, double> summary = {};
                for (var asset in assets) {
                  summary[asset.assetType.name] = (summary[asset.assetType.name] ?? 0) + asset.value;
                }

                return ListView(
                  children: [
                    const Padding(
                      padding: EdgeInsets.all(16.0),
                      child: Text('我的资产', style: TextStyle(fontWeight: FontWeight.bold)),
                    ),
                    ...summary.entries.map((e) => ListTile(
                      title: Text(_getAssetTypeName(e.key)),
                      trailing: Text('¥${e.value.toStringAsFixed(0)}'),
                      dense: true,
                    )),
                  ],
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, stack) => Center(child: Text('加载失败: $err')),
            ),
          ),
          const Divider(),
          ListTile(
            leading: const Icon(Icons.settings),
            title: const Text('个人设置'),
            onTap: () {
              context.pop();
              context.go('/profile');
            },
          ),
        ],
      ),
    );
  }

  String _getAssetTypeName(String type) {
    switch (type) {
      case 'realEstate': return '房产';
      case 'cash': return '现金';
      case 'investment': return '投资';
      case 'liability': return '负债';
      case 'insurance': return '保险';
      default: return type;
    }
  }
}
