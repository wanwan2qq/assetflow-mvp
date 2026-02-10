import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../../shared/widgets/money_text.dart';

class CashFlowTeaserCard extends StatelessWidget {
  final bool isPrivacyMode;
  final VoidCallback onTap;

  const CashFlowTeaserCard({
    super.key,
    required this.isPrivacyMode,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    // Mock data for now - should be replaced with real data provider
    const double income = 15000;
    const double expense = 8500;
    const double balance = income - expense;
    final currencyFormat = NumberFormat.simpleCurrency(locale: 'zh_CN', decimalDigits: 0);

    // Calculate progress bar
    final total = income + expense;
    final incomeRatio = total > 0 ? (income / total) : 0.5;

    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16.0).copyWith(bottom: 8),
      child: Card(
        elevation: 0,
        color: Theme.of(context).cardTheme.color, // Adapts to Dark Mode
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          // No border for cleaner look, or very subtle
          side: BorderSide(color: Colors.grey.withOpacity(0.1)),
        ),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onTap,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                // Header
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: colorScheme.surfaceContainerHighest.withOpacity(0.5),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(Icons.account_balance_wallet_outlined, size: 16, color: colorScheme.onSurface),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          '本月收支',
                          style: theme.textTheme.titleSmall?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        Text(
                          '查看详情',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: colorScheme.onSurfaceVariant,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(
                          Icons.chevron_right,
                          size: 16,
                          color: colorScheme.onSurfaceVariant,
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 16),

                // Numbers Row
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    _buildStatColumn(
                      context, 
                      '收入', 
                      income, 
                      Theme.of(context).brightness == Brightness.dark ? const Color(0xFF81C784) : const Color(0xFF2E7D32),
                      isPrivacyMode, 
                      currencyFormat
                    ),
                    // Divider
                    Container(height: 30, width: 1, color: colorScheme.outlineVariant.withOpacity(0.5)),
                    _buildStatColumn(
                      context, 
                      '支出', 
                      expense,
                      Theme.of(context).brightness == Brightness.dark ? const Color(0xFFE57373) : colorScheme.error, 
                      isPrivacyMode, 
                      currencyFormat
                    ),
                    // Divider
                    Container(height: 30, width: 1, color: colorScheme.outlineVariant.withOpacity(0.5)),
                    _buildStatColumn(
                      context, 
                      '结余', 
                      balance, 
                      colorScheme.onSurface, 
                      isPrivacyMode, 
                      currencyFormat,
                      isBold: true
                    ),
                  ],
                ),
                
                const SizedBox(height: 16),

                // Segmented Progress Bar
                SizedBox(
                  height: 6,
                  child: Row(
                    children: [
                      // Income Segment
                      Expanded(
                        flex: (incomeRatio * 100).toInt(),
                        child: Container(
                          decoration: BoxDecoration(
                            color: Theme.of(context).brightness == Brightness.dark ? const Color(0xFF81C784) : const Color(0xFF4CAF50), // Green 300 : Green 500
                            borderRadius: const BorderRadius.horizontal(left: Radius.circular(4)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 2), // Gap
                      // Expense Segment (using remaining ratio concept visually, or just showing expense proportion)
                      // Actually for a "Balance" view, usually it's Income vs Expense bars. 
                      // Here we visualy split the bar based on volume. 
                      Expanded(
                        flex: 100 - (incomeRatio * 100).toInt(),
                        child: Container(
                          decoration: BoxDecoration(
                            color: Theme.of(context).brightness == Brightness.dark ? const Color(0xFFE57373) : colorScheme.error,
                            borderRadius: const BorderRadius.horizontal(right: Radius.circular(4)),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStatColumn(
    BuildContext context, 
    String label, 
    double value, 
    Color color, 
    bool isPrivacyMode, 
    NumberFormat fmt,
    {bool isBold = false}
  ) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 4),
        MoneyText(
           isPrivacyMode ? '****' : fmt.format(value),
           style: Theme.of(context).textTheme.titleMedium?.copyWith(
             color: color,
             fontWeight: isBold ? FontWeight.w800 : FontWeight.w600,
             fontFamily: 'Inter', // Explicitly ensure Inter
           ),
        ),
      ],
    );
  }
}
