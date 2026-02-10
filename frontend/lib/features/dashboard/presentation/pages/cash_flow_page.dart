import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../core/models/cash_flow_item.dart';
import '../../../../core/providers/wealth_provider.dart';
import '../widgets/net_cash_flow_card.dart';
import '../widgets/structure_chart.dart';
import '../widgets/sheets/cash_flow_edit_sheet.dart';
import '../../../../core/theme/app_theme.dart';

class CashFlowPage extends ConsumerStatefulWidget {
  const CashFlowPage({super.key});

  @override
  ConsumerState<CashFlowPage> createState() => _CashFlowPageState();
}

class _CashFlowPageState extends ConsumerState<CashFlowPage> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isMonthly = true; // Toggle state
  
  // Mock data for now (preserved)
  double get _fixedIncome => 30000;
  double get _variableIncome => 5000;
  double get _fixedExpense => 10000;
  double get _variableExpense => 2000;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _tabController.addListener(() {
      if (_tabController.indexIsChanging) {
        HapticFeedback.selectionClick();
        setState(() {}); // Rebuild to update FAB color
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cashFlowAsync = ref.watch(cashFlowProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    // Design Colors from AppTheme
    final incomeColor = isDark ? AppTheme.incomeColorDark : AppTheme.incomeColorLight;
    final expenseColor = isDark ? AppTheme.expenseColorDark : AppTheme.expenseColorLight;
    final fabColor = _tabController.index == 0 ? incomeColor : expenseColor;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      // 1. Header & Filter (Sticky style)
      body: SafeArea(
        child: Column(
          children: [
             // Header
            _buildHeader(context),
            
            // Scrollable Content
            Expanded(
              child: CustomScrollView(
                physics: const BouncingScrollPhysics(),
                slivers: [
                   // Sticky Date Filter
                   SliverPersistentHeader(
                     delegate: _StickyDateFilterDelegate(
                       child: _buildDateFilterBar(context),
                       height: 56, // Slightly reduced height
                       backgroundColor: theme.scaffoldBackgroundColor,
                     ),
                     pinned: true,
                   ),

                   const SliverToBoxAdapter(child: SizedBox(height: 16)),
                   
                   // Hero Card: Net Cash Flow
                   SliverToBoxAdapter(
                     child: NetCashFlowCard(
                       income: _fixedIncome + _variableIncome,
                       expense: _fixedExpense + _variableExpense,
                       isPrivacyMode: false,
                     ),
                   ),
                   const SliverToBoxAdapter(child: SizedBox(height: 24)),
                   
                   // Structural Chart
                   SliverPadding(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                      sliver: SliverToBoxAdapter(
                      child: StructureChart(
                        fixedIncome: _fixedIncome,
                        variableIncome: _variableIncome,
                        fixedExpense: _fixedExpense,
                        variableExpense: _variableExpense,
                      ),
                    ),
                   ),
                   const SliverToBoxAdapter(child: SizedBox(height: 24)),

                   // Sticky Structure Tabs (Segmented Pill)
                   SliverPersistentHeader(
                     delegate: _StickyPillTabBarDelegate(
                       child: _buildPillTabs(context),
                       height: 60,
                       backgroundColor: theme.scaffoldBackgroundColor, 
                     ),
                     pinned: true,
                   ),

                   // Grouped List Content based on active tab
                   cashFlowAsync.when(
                    data: (flows) {
                       final isIncome = _tabController.index == 0;
                       
                       // Filter flows
                       final relevantFlows = flows.where((f) => f.type == (isIncome ? CashFlowType.income : CashFlowType.expense)).toList();
                       final recurring = relevantFlows.where((f) => f.frequency != CashFlowFrequency.oneTime).toList();
                       final oneTime = relevantFlows.where((f) => f.frequency == CashFlowFrequency.oneTime).toList();

                       return SliverPadding(
                         padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                         sliver: SliverList(
                           delegate: SliverChildListDelegate([
                             if (recurring.isNotEmpty) ...[
                               const SizedBox(height: 24), // Added spacing
                               _buildSectionHeader(context, '固定/周期性 (Recurring)', Icons.repeat, isIncome),
                               ...recurring.map((item) => _buildAssetStyleListItem(context, item, isIncome, true)),
                               const SizedBox(height: 24),
                             ],
                             if (oneTime.isNotEmpty) ...[
                               _buildSectionHeader(context, '变动/一次性 (Variable)', Icons.flash_on, isIncome),
                               ...oneTime.map((item) => _buildAssetStyleListItem(context, item, isIncome, false)),
                             ],
                             if (recurring.isEmpty && oneTime.isEmpty)
                               Padding(
                                 padding: const EdgeInsets.all(32),
                                 child: Center(
                                   child: Text(
                                     '暂无${isIncome ? '收入' : '支出'}记录',
                                     style: TextStyle(color: Colors.grey.shade400),
                                   ),
                                 ),
                               ),
                             
                             const SizedBox(height: 100), // Bottom padding for FAB
                           ]),
                         ),
                       );
                    },
                    loading: () => const SliverToBoxAdapter(child: Center(child: CircularProgressIndicator())),
                    error: (err, _) => SliverToBoxAdapter(child: Center(child: Text('Error: $err'))),
                   ),
                ],
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          showModalBottomSheet(
            context: context,
            isScrollControlled: true,
            useSafeArea: true,
            builder: (context) => const CashFlowEditSheet(),
          );
        },
        backgroundColor: fabColor,
        elevation: 4,
        highlightElevation: 8,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)), // Circular
        child: const Icon(Icons.add, color: Colors.white, size: 28),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(bottom: BorderSide(color: Theme.of(context).dividerColor.withOpacity(0.05))),
      ),
      child: Row(
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left, size: 28),
            onPressed: () => Navigator.pop(context),
            color: Theme.of(context).textTheme.bodyLarge?.color,
          ),
          const SizedBox(width: 8),
          Text(
            '现金流结构',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Theme.of(context).textTheme.bodyLarge?.color,
            ),
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.search, size: 24),
            onPressed: () {},
            color: Theme.of(context).textTheme.bodyMedium?.color?.withOpacity(0.5),
          ),
        ],
      ),
    );
  }
  
  Widget _buildDateFilterBar(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      alignment: Alignment.center,
       decoration: BoxDecoration(
        color: theme.scaffoldBackgroundColor.withOpacity(0.95),
        border: Border(bottom: BorderSide(color: theme.dividerColor.withOpacity(0.05))),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // Date Selector
          Container(
             padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
             decoration: BoxDecoration(
               color: isDark ? Colors.white.withOpacity(0.05) : Colors.grey.shade200,
               borderRadius: BorderRadius.circular(20),
             ),
             child: Row(
              children: [
                Icon(Icons.calendar_today_rounded, size: 14, color: isDark ? Colors.white70: Colors.grey.shade600),
                const SizedBox(width: 8),
                Text(
                  '2026年 2月',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: theme.textTheme.bodyLarge?.color,
                  ),
                ),
                const SizedBox(width: 4),
                Icon(Icons.arrow_drop_down, size: 18, color: theme.textTheme.bodyMedium?.color),
              ],
            ),
          ),

          // Segmented Control (Sliding Toggle Style)
          Container(
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF2C2C2C) : Colors.grey[200], // The Track
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.all(4),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildFilterButton(context, '按月', _isMonthly, () => setState(() => _isMonthly = true)),
                _buildFilterButton(context, '按年', !_isMonthly, () => setState(() => _isMonthly = false)),
              ],
            ),
          )
        ],
      ),
    );
  }

  Widget _buildFilterButton(BuildContext context, String text, bool isActive, VoidCallback onTap) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return GestureDetector(
      onTap: () {
        HapticFeedback.selectionClick();
        onTap();
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        decoration: BoxDecoration(
          color: isActive 
              ? (isDark ? const Color(0xFF4DB6AC) : const Color(0xFF00695C)) // Brand Color for Selected
              : Colors.transparent,
          borderRadius: BorderRadius.circular(16),
          boxShadow: isActive
              ? [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.1),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  )
                ]
              : null,
        ),
        child: Text(
          text,
          style: TextStyle(
            fontSize: 13,
            fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
            color: isActive 
                ? Colors.white
                : (isDark ? Colors.white54 : Colors.grey),
          ),
        ),
      ),
    );
  }

  Widget _buildPillTabs(BuildContext context) {
    final isIncome = _tabController.index == 0;
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final containerColor = isDark ? Colors.grey.shade900 : const Color(0xFFF0F2F5); 
    
    // Determine indicator color based on current tab
    final indicatorColor = isIncome 
        ? (isDark ? AppTheme.incomeColorDark : AppTheme.incomeColorLight)
        : (isDark ? AppTheme.expenseColorDark : AppTheme.expenseColorLight);

    // Text color for selected tab (always white as per design)
    // Text color for unselected tab (grey)
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Container(
        height: 44,
         decoration: BoxDecoration(
          color: containerColor,
          borderRadius: BorderRadius.circular(22), // Full rounded
        ),
        padding: const EdgeInsets.all(4),
        child: Stack(
          children: [
            // Sliding Indicator
            AnimatedAlign(
              alignment: isIncome ? Alignment.centerLeft : Alignment.centerRight,
              duration: const Duration(milliseconds: 250),
              curve: Curves.easeOutCubic,
              child: FractionallySizedBox(
                widthFactor: 0.5,
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  decoration: BoxDecoration(
                    color: indicatorColor,
                    borderRadius: BorderRadius.circular(18),
                    boxShadow: [
                      BoxShadow(
                        color: indicatorColor.withOpacity(0.3),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            // Text Labels
            Row(
              children: [
                Expanded(
                  child: GestureDetector(
                    onTap: () => _tabController.animateTo(0),
                    behavior: HitTestBehavior.translucent,
                    child: Center(
                      child: Text(
                        '收入结构',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: isIncome ? Colors.white : Colors.grey.shade500,
                        ),
                      ),
                    ),
                  ),
                ),
                Expanded(
                  child: GestureDetector(
                    onTap: () => _tabController.animateTo(1),
                    behavior: HitTestBehavior.translucent,
                    child: Center(
                      child: Text(
                        '支出结构',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: !isIncome ? Colors.white : Colors.grey.shade500,
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildSectionHeader(BuildContext context, String title, IconData icon, bool isIncome) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 8),
      child: Row(
        children: [
          Icon(icon, size: 16, color: theme.textTheme.bodySmall?.color?.withOpacity(0.5)),
          const SizedBox(width: 8),
          Text(
            title,
            style: theme.textTheme.titleMedium?.copyWith(
              color: theme.textTheme.bodyMedium?.color?.withOpacity(0.8),
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAssetStyleListItem(BuildContext context, CashFlowItem item, bool isIncome, bool isRecurring) {
     final theme = Theme.of(context);
     final isDark = theme.brightness == Brightness.dark;
     final currencyFormat = NumberFormat.simpleCurrency(locale: 'zh_CN', decimalDigits: 0);

     // Card Background Color Strategy
     final cardColor = isDark ? const Color(0xFF1E1E1E) : Colors.white;
     
     // Icon Background
     final iconBg = isIncome 
         ? const Color(0xFF00695C).withOpacity(0.1) 
         : const Color(0xFFE53935).withOpacity(0.1);
     final iconColor = isIncome 
         ? const Color(0xFF00695C) 
         : const Color(0xFFE53935);

     return Container(
       margin: const EdgeInsets.only(bottom: 12),
       decoration: BoxDecoration(
         color: cardColor,
         borderRadius: BorderRadius.circular(16),
         boxShadow: isDark ? [] : [
           BoxShadow(
             color: Colors.black.withOpacity(0.03),
             blurRadius: 10,
             offset: const Offset(0, 4),
           ),
         ],
         border: Border.all(
           color: theme.dividerColor.withOpacity(isDark ? 0.05 : 0),
         ),
       ),
       child: Material(
         color: Colors.transparent,
         child: InkWell(
           onTap: () {
             showModalBottomSheet(
                context: context,
                isScrollControlled: true,
                useSafeArea: true,
                builder: (context) => CashFlowEditSheet(item: item),
              );
           },
           borderRadius: BorderRadius.circular(16),
           child: Padding(
             padding: const EdgeInsets.all(16),
             child: Row(
               children: [
                 // 1. Icon in Circle
                 Container(
                   width: 44,
                   height: 44,
                   decoration: BoxDecoration(
                     color: iconBg,
                     shape: BoxShape.circle,
                   ),
                   child: Icon(
                     isRecurring ? Icons.repeat_rounded : Icons.flash_on_rounded,
                     color: iconColor,
                     size: 22,
                   ),
                 ),
                 const SizedBox(width: 16),
                 
                 // 2. Title & Subtitle
                 Expanded(
                   child: Column(
                     crossAxisAlignment: CrossAxisAlignment.start,
                     children: [
                       Text(
                         item.name,
                         style: theme.textTheme.titleMedium?.copyWith(
                           fontWeight: FontWeight.w600,
                           fontSize: 16,
                         ),
                       ),
                       const SizedBox(height: 4),
                       Text(
                         isRecurring ? '每月 • 自动入账' : '2月9日 • 一次性', // Mocked detail
                         style: theme.textTheme.bodySmall?.copyWith(
                           color: theme.textTheme.bodySmall?.color?.withOpacity(0.6),
                           fontSize: 12,
                         ),
                       ),
                     ],
                   ),
                 ),
                 
                 // 3. Amount (Tabular)
                 Text(
                   currencyFormat.format(item.amount),
                   style: theme.textTheme.titleMedium?.copyWith(
                     fontWeight: FontWeight.w700,
                     fontSize: 16,
                     fontFeatures: const [FontFeature.tabularFigures()],
                     color: isIncome ? const Color(0xFF00695C) : theme.textTheme.bodyLarge?.color,
                   ),
                 ),
                 const SizedBox(width: 8),
                 Icon(Icons.chevron_right, size: 18, color: theme.dividerColor.withOpacity(0.5)),
               ],
             ),
           ),
         ),
       ),
     );
  }
}

// Delegate for Sticky Date Filter
class _StickyDateFilterDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double height;
  final Color backgroundColor;

  _StickyDateFilterDelegate({
    required this.child,
    required this.height,
    required this.backgroundColor,
  });

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return Container(
      color: backgroundColor,
      child: SizedBox.expand(child: child),
    );
  }

  @override
  double get maxExtent => height;
  @override
  double get minExtent => height;
  @override
  bool shouldRebuild(_StickyDateFilterDelegate oldDelegate) {
    return oldDelegate.child != child;
  }
}

// Delegate for Sticky Tabs
class _StickyPillTabBarDelegate extends SliverPersistentHeaderDelegate {
  final Widget child;
  final double height;
  final Color backgroundColor;

  _StickyPillTabBarDelegate({
    required this.child,
    required this.height,
    required this.backgroundColor,
  });

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    return Container(
      color: backgroundColor,
      child: SizedBox.expand(child: child),
    );
  }

  @override
  double get maxExtent => height;
  @override
  double get minExtent => height;
  @override
  bool shouldRebuild(_StickyPillTabBarDelegate oldDelegate) {
    return oldDelegate.child != child;
  }
}
