import 'package:flutter/material.dart';

class AssetCard extends StatelessWidget {
  final String name;
  final double value;
  final String assetType;
  final String? riskLevel;
  final List<String> tags;
  final bool privacyMode;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;

  const AssetCard({
    super.key,
    required this.name,
    required this.value,
    required this.assetType,
    this.riskLevel,
    this.tags = const [],
    this.privacyMode = false,
    this.onTap,
    this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header with asset icon and name
              Row(
                children: [
                  Icon(
                    _getAssetIcon(),
                    color: _getAssetColor(),
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (onEdit != null)
                    IconButton(
                      icon: const Icon(Icons.edit, size: 20),
                      onPressed: onEdit,
                    ),
                ],
              ),
              const SizedBox(height: 12),
              
              // Value display (with privacy mode support)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '资产价值',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      Text(
                        _formatValue(),
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: Colors.green[700],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  if (riskLevel != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: _getRiskColor().withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: _getRiskColor().withOpacity(0.3)),
                      ),
                      child: Text(
                        _getRiskLabel(),
                        style: TextStyle(
                          color: _getRiskColor(),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                ],
              ),
              
              // Tags
              if (tags.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: tags.map((tag) => Chip(
                    label: Text(
                      tag,
                      style: const TextStyle(fontSize: 11),
                    ),
                    backgroundColor: Colors.grey[100],
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  )).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  IconData _getAssetIcon() {
    switch (assetType.toLowerCase()) {
      case 'real_estate':
        return Icons.home;
      case 'cash':
        return Icons.account_balance_wallet;
      case 'investment':
        return Icons.trending_up;
      case 'insurance':
        return Icons.security;
      case 'liability':
        return Icons.credit_card;
      default:
        return Icons.account_balance;
    }
  }

  Color _getAssetColor() {
    switch (assetType.toLowerCase()) {
      case 'real_estate':
        return Colors.blue;
      case 'cash':
        return Colors.green;
      case 'investment':
        return Colors.orange;
      case 'insurance':
        return Colors.purple;
      case 'liability':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _formatValue() {
    if (privacyMode) {
      if (value >= 10000000) return '1000万+';
      if (value >= 1000000) return '100万+';
      if (value >= 100000) return '10万+';
      return '***';
    }
    
    if (value >= 10000) {
      return '¥${(value / 10000).toStringAsFixed(1)}万';
    }
    return '¥${value.toStringAsFixed(0)}';
  }

  Color _getRiskColor() {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      case 'high':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _getRiskLabel() {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return '低风险';
      case 'medium':
        return '中风险';
      case 'high':
        return '高风险';
      default:
        return '未知';
    }
  }
}