import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../../../shared/widgets/money_text.dart';

class NetCashFlowCard extends ConsumerWidget {
  final double income;
  final double expense;
  final bool isPrivacyMode;

  const NetCashFlowCard({
    super.key,
    required this.income,
    required this.expense,
    required this.isPrivacyMode,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final netCashFlow = income - expense;
    final currencyFormat = NumberFormat.simpleCurrency(locale: 'zh_CN', decimalDigits: 0);
    
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
      child: Container(
        height: 180,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(24),
          // Gradient Background for Premium Look (Deep Teal)
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: isDark
                ? [const Color(0xFF004D40), const Color(0xFF00695C)] // Darker Teal for Dark Mode
                : [const Color(0xFF00695C), const Color(0xFF4DB6AC)], // Standard Teal for Light Mode
          ),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF00695C).withOpacity(0.3),
              blurRadius: 20,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          children: [
            // Decorative background elements (Geometric shapes)
            Positioned(
              right: -20,
              top: -20,
              child: Container(
                width: 150,
                height: 150,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white.withOpacity(0.05),
                ),
              ),
            ),
            Positioned(
              right: 40,
              bottom: -40,
              child: Container(
                width: 100,
                height: 100,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: Colors.white.withOpacity(0.05),
                ),
              ),
            ),
            
            // Content
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                   Text(
                    '本月净现金流 (Net Cash Flow)',
                    style: theme.textTheme.labelMedium?.copyWith(
                      color: Colors.white.withOpacity(0.8),
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Net Cash Flow Value
                  MoneyText(
                    isPrivacyMode ? '****' : '${netCashFlow >= 0 ? "+" : ""}${currencyFormat.format(netCashFlow)}',
                    style: theme.textTheme.displaySmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      letterSpacing: -1,
                      fontSize: 40,
                    ),
                  ),
                  
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      // Income
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: const Color(0xFF00C853).withOpacity(0.2), // Green accent bg
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.arrow_downward_rounded, size: 14, color: Color(0xFF69F0AE)), // Light Green
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '收入',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.white.withOpacity(0.7),
                        ),
                      ),
                      const SizedBox(width: 4),
                      MoneyText(
                        currencyFormat.format(income),
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      
                      const SizedBox(width: 24), // Spacer
                      
                      // Expense
                      Container(
                        padding: const EdgeInsets.all(4),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFF5252).withOpacity(0.2), // Red accent bg
                          shape: BoxShape.circle,
                        ),
                        child: const Icon(Icons.arrow_upward_rounded, size: 14, color: Color(0xFFFF8A80)), // Light Red
                      ),
                      const SizedBox(width: 6),
                      Text(
                        '支出',
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: Colors.white.withOpacity(0.7),
                        ),
                      ),
                      const SizedBox(width: 4),
                      MoneyText(
                        currencyFormat.format(expense),
                        style: theme.textTheme.titleMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  // Mini bar visualization or simple summary could go here, 
                  // but keeping it clean as per "Unique Hero" request.
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
