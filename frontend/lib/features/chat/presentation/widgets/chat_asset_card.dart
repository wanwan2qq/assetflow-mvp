import 'package:flutter/material.dart';

class ChatAssetCard extends StatelessWidget {
  final Map<String, dynamic> data;
  final VoidCallback? onConfirm;
  final VoidCallback? onModify;

  const ChatAssetCard({
    super.key,
    required this.data,
    this.onConfirm,
    this.onModify,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final backgroundColor = isDark ? const Color(0xFF1E1E1E) : Colors.white;

    final String title = data['name'] ?? data['location'] ?? '未命名资产';
    final double value = (data['value'] ?? data['price'] ?? 0).toDouble();
    final String subtitle = data['unit_price'] ?? data['price_per_sqm']?.toString() ?? '';
    final String type = data['type'] ?? 'asset';

    IconData getIcon() {
      switch (type.toLowerCase()) {
        case 'real_estate': return Icons.home_work_outlined;
        case 'liability': return Icons.credit_card_outlined;
        case 'investment': return Icons.show_chart;
        case 'insurance': return Icons.security;
        case 'cash': return Icons.account_balance_wallet_outlined;
        default: return Icons.category_outlined;
      }
    }

    return Container(
      width: 280, // Constrain width for chat bubble look
      margin: const EdgeInsets.symmetric(vertical: 4),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: isDark ? Colors.grey[800] : Colors.grey[100],
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    getIcon(),
                    size: 20,
                    color: isDark ? Colors.grey[300] : Colors.grey[700],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    title,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w600,
                      color: isDark ? Colors.white : Colors.black87,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),
          
          // Divider
          Divider(height: 1, color: isDark ? Colors.grey[800] : Colors.grey[100]),
          
          // Body
          Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '¥ ${_formatMoney(value)}',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: isDark ? Colors.white : Colors.black,
                    fontFamily: 'Roboto', // Ensure tabular figures if possible, or use standard
                  ),
                ),
                if (subtitle.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    subtitle.contains('平') ? subtitle : '$subtitle/平', // Quick fix for display
                    style: TextStyle(
                      fontSize: 12,
                      color: isDark ? Colors.grey[400] : Colors.grey[600],
                    ),
                  ),
                ],
              ],
            ),
          ),
          
          // Actions
          if (onConfirm != null || onModify != null) ...[
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              child: Row(
                children: [
                  if (onConfirm != null)
                    Expanded(
                      child: ElevatedButton(
                        onPressed: onConfirm,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF00695C), // Brand Teal
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        child: const Text('确认'),
                      ),
                    ),
                  if (onConfirm != null && onModify != null)
                    const SizedBox(width: 12),
                  if (onModify != null)
                    Expanded(
                      child: OutlinedButton(
                        onPressed: onModify,
                        style: OutlinedButton.styleFrom(
                          foregroundColor: isDark ? Colors.grey[300] : Colors.grey[700],
                          side: BorderSide(
                            color: isDark ? Colors.grey[700]! : Colors.grey[300]!,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(20),
                          ),
                          padding: const EdgeInsets.symmetric(vertical: 10),
                        ),
                        child: const Text('修改'),
                      ),
                    ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  String _formatMoney(double value) {
    if (value >= 10000) {
      return '${(value / 10000).toStringAsFixed(1)}万'; // Simple formatting matching design request
    }
    return value.toStringAsFixed(0);
  }
}
