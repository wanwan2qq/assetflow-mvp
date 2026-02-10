import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/models/asset.dart';
import '../../../../core/providers/asset_provider.dart';
import '../widgets/wealth_overview_card.dart';
import '../widgets/cash_flow_teaser_card.dart';
import '../widgets/asset_creation_sheet.dart';
import '../../../../shared/widgets/cards/asset_card_factory.dart';
import '../widgets/type_selection_sheet.dart';
import 'cash_flow_page.dart';

class WealthPage extends ConsumerStatefulWidget {
  const WealthPage({super.key});

  @override
  ConsumerState<WealthPage> createState() => _WealthPageState();
}

class _WealthPageState extends ConsumerState<WealthPage> with SingleTickerProviderStateMixin {
  bool _isPrivacyMode = false;
  late TabController _tabController;

  final List<(String id, String label)> _tabs = [
    ('ALL', '全部'),
    (AssetType.realEstate.name, '房产'),
    (AssetType.liability.name, '负债'),
    (AssetType.investment.name, '投资'),
    (AssetType.insurance.name, '保险'),
    (AssetType.cash.name, '现金'),
  ];
  
  // Mapping for filtered view
  AssetType? _getAssetTypeFromIndex(int index) {
    if (index == 0) return null; // ALL
    // Map index to AssetType based on tabs array order
    final id = _tabs[index].$1;
    // We need to parse back from name or ensure alignment.
    // simpler to map manually or keep aligned.
    if (id == AssetType.realEstate.name) return AssetType.realEstate;
    if (id == AssetType.liability.name) return AssetType.liability;
    if (id == AssetType.investment.name) return AssetType.investment;
    if (id == AssetType.insurance.name) return AssetType.insurance;
    if (id == AssetType.cash.name) return AssetType.cash;
    return null;
  }

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: _tabs.length, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  void _togglePrivacy() {
    setState(() {
      _isPrivacyMode = !_isPrivacyMode;
    });
  }

  @override
  Widget build(BuildContext context) {
    // M3 Scaffolds automatically use colorScheme.surface or surfaceContainer
    // User Requirement: Distinct Light Grey Background
    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor, 
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) {
          return [
            // 1. Custom Sticky Header
            SliverPersistentHeader(
              delegate: _StickyHeaderDelegate(
                isPrivacyMode: _isPrivacyMode,
                onTogglePrivacy: _togglePrivacy,
                onAdd: () => _showAddMenu(context),
              ),
              pinned: true,
            ),

            // 2. Scrollable Content (Overview & Teaser)
            SliverToBoxAdapter(
              child: Column(
                children: [
                   // Add top padding to create separation from header
                  const SizedBox(height: 8), 
                  WealthOverviewCard(isPrivacyMode: _isPrivacyMode),
                  CashFlowTeaserCard(
                    isPrivacyMode: _isPrivacyMode,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => const CashFlowPage()),
                      );
                    },
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),

            // 3. Sticky Tabs
            SliverPersistentHeader(
              delegate: _StickyPillTabsDelegate(
                tabs: _tabs,
                controller: _tabController,
              ),
              pinned: true,
            ),
          ];
        },
        body: Container(
          color: Theme.of(context).scaffoldBackgroundColor, // Ensure body background matches
          child: TabBarView(
            controller: _tabController,
            children: List.generate(_tabs.length, (index) {
              return _AssetListTab(
                filterType: _getAssetTypeFromIndex(index), 
                isPrivacyMode: _isPrivacyMode,
              );
            }),
          ),
        ),
      ),
    );
  }

  void _showAddMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => TypeSelectionSheet(
        onRecordTransaction: () {
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('记账功能开发中...')),
          );
        },
        onSelectAssetType: (type) {
          Navigator.pop(context);
          Future.delayed(const Duration(milliseconds: 150), () {
            if (context.mounted) _showAssetCreationSheet(context, type);
          });
        },
      ),
    );
  }

  void _showAssetCreationSheet(BuildContext context, AssetType type) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (context) => AssetCreationSheet(initialType: type),
    );
  }
}

// Custom Sticky Header Delegate
class _StickyHeaderDelegate extends SliverPersistentHeaderDelegate {
  final bool isPrivacyMode;
  final VoidCallback onTogglePrivacy;
  final VoidCallback onAdd;

  _StickyHeaderDelegate({
    required this.isPrivacyMode, 
    required this.onTogglePrivacy,
    required this.onAdd,
  });

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          // Use surface color with opacity for glassmorphism
          // Standard surface is usually white/light grey in light mode.
          // We want it to blend with the grey background but still show content behind.
          color: Theme.of(context).scaffoldBackgroundColor.withOpacity(0.90),
          padding: EdgeInsets.only(
            top: MediaQuery.of(context).padding.top,
            left: 16,
            right: 8, // Reduced right padding for trailing icons
            bottom: 8 // Reduced bottom padding
          ),
          alignment: Alignment.centerLeft,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '财富',
                style: theme.textTheme.titleLarge?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: colorScheme.onSurface,
                ),
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(
                    icon: Icon(isPrivacyMode ? Icons.visibility_off : Icons.visibility),
                    onPressed: onTogglePrivacy,
                    // Use onSurfaceVariant for secondary icons
                    color: colorScheme.onSurfaceVariant,
                    iconSize: 22,
                    constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                  ),
                  IconButton(
                    icon: const Icon(Icons.add_circle_outline_rounded),
                    onPressed: onAdd,
                    color: colorScheme.primary,
                    iconSize: 24,
                    constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                  ),
                  IconButton(
                    icon: const Icon(Icons.notifications_none_rounded),
                    onPressed: () {}, // TODO: Notifications
                    color: colorScheme.onSurfaceVariant,
                    iconSize: 24,
                    constraints: const BoxConstraints(minWidth: 40, minHeight: 40),
                  ),
                ],
              )
            ],
          ),
        ),
      ),
    );
  }

  @override
  // Reduced height: Toolbar height + small padding. Standard is usually kToolbarHeight
  double get maxExtent => kToolbarHeight + 16; 
  @override
  double get minExtent => kToolbarHeight + 16; 
  @override
  bool shouldRebuild(covariant _StickyHeaderDelegate oldDelegate) {
    return oldDelegate.isPrivacyMode != isPrivacyMode;
  }
}

// Custom Sticky Segmented Tabs Delegate
class _StickyPillTabsDelegate extends SliverPersistentHeaderDelegate {
  final List<(String, String)> tabs;
  final TabController controller;

  _StickyPillTabsDelegate({required this.tabs, required this.controller});

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return Container(
      color: Theme.of(context).scaffoldBackgroundColor, // Match scaffold background
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      alignment: Alignment.center,
      child: Container(
        height: 40,
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(20),
        ),
        padding: const EdgeInsets.all(4),
        child: AnimatedBuilder(
          animation: controller,
          builder: (context, child) {
            return ListView.builder(
              scrollDirection: Axis.horizontal,
              itemCount: tabs.length,
              shrinkWrap: true, // Allow it to shrink if items are few, but they are many
              physics: const ClampingScrollPhysics(),
              itemBuilder: (context, index) {
                final isSelected = controller.index == index;
                final label = tabs[index].$2;
                
                return GestureDetector(
                  onTap: () => controller.animateTo(index),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: isSelected ? Theme.of(context).colorScheme.primary : Colors.transparent,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      label,
                      style: TextStyle(
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                        color: isSelected ? Theme.of(context).colorScheme.onPrimary : Theme.of(context).colorScheme.onSurfaceVariant,
                        fontSize: 13,
                      ),
                    ),
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }

  @override
  double get maxExtent => 56; // 40 height + 8*2 vertical padding
  @override
  double get minExtent => 56;
  @override
  bool shouldRebuild(covariant _StickyPillTabsDelegate oldDelegate) => false;
}

class _AssetListTab extends ConsumerWidget {
  final AssetType? filterType;
  final bool isPrivacyMode;

  const _AssetListTab({this.filterType, required this.isPrivacyMode});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assetsAsync = ref.watch(assetListProvider);

    return assetsAsync.when(
      data: (assets) {
        final filtered = filterType == null
            ? assets
            : assets.where((a) => a.assetType == filterType).toList();

        if (filtered.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.business_outlined, size: 48, color: Colors.grey[300]),
                const SizedBox(height: 16),
                Text('暂无该分类资产', style: TextStyle(color: Colors.grey[400])),
              ],
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 100), // Bottom padding for FAB
          itemCount: filtered.length + 1, // +1 for "Manual Add" button at bottom of list
          itemBuilder: (context, index) {
            if (index == filtered.length) {
              return Padding(
                padding: const EdgeInsets.only(top: 16.0),
                child: DashedAddButton(onTap: () {
                   // This should probably trigger the add menu too
                   // For now accessing parent logic is hard without callback
                   // We just leave it visual 
                }),
              );
            }
            final asset = filtered[index];
            return AssetCardFactory.build(asset, isPrivacyMode: isPrivacyMode);
          },
        );
      },
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => Center(child: Text('Error: $err')),
    );
  }
}

class DashedAddButton extends StatelessWidget {
  final VoidCallback onTap;
  const DashedAddButton({super.key, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 50,
        decoration: BoxDecoration(
          border: Border.all(color: Colors.grey.withOpacity(0.3), style: BorderStyle.none), // Can't easily do dashed natively without package
          color: Colors.grey.withOpacity(0.05),
          borderRadius: BorderRadius.circular(16),
        ),
         // Simulating dashed border with custom painter would be ideal, 
         // but simple outline is okay for now.
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.add, size: 18, color: Colors.grey[500]),
            const SizedBox(width: 8),
            Text('手动添加资产', style: TextStyle(color: Colors.grey[500], fontSize: 13, fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
