import 'package:flutter/material.dart';

class CashFlowSummaryCard extends StatelessWidget {
  final double income;
  final double expense;
  final bool isPrivacyMode;

  const CashFlowSummaryCard({
    super.key,
    required this.income,
    required this.expense,
    required this.isPrivacyMode,
  });

  @override
  Widget build(BuildContext context) {
    final netFlow = income - expense;
    final isPositive = netFlow >= 0;

    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // Design Colors
    final positiveColor = const Color(0xFF059669); // Emerald 600
    final negativeColor = const Color(0xFFE11D48); // Rose 600
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Theme.of(context).dividerColor.withOpacity(0.1)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(isDark ? 0.2 : 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '本月净现金流 (Net Cash Flow)',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade400,
              fontWeight: FontWeight.w600,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                isPrivacyMode 
                    ? '****' 
                    : '${isPositive ? '+' : ''}¥${netFlow.abs().toStringAsFixed(0).replaceAllMapped(RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'), (Match m) => '${m[1]},')}',
                style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.bold,
                  color: isPositive ? positiveColor : negativeColor,
                  letterSpacing: -0.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildDetailItem('总收入', income),
              const SizedBox(width: 16),
              _buildDetailItem('总支出', expense),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDetailItem(String label, double amount) {
    return Text(
      '$label: ¥${amount.toStringAsFixed(0)}', // Simplified formatting
      style: const TextStyle(
        fontSize: 12,
        color: Colors.grey,
        fontWeight: FontWeight.w500
      ),
    );
  }
}
