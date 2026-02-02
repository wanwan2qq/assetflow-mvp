import 'package:flutter/material.dart';

class AssetCard extends StatefulWidget {
  final String name;
  final double value;
  final String assetType;
  final String? riskLevel;
  final List<String> tags;
  final bool privacyMode;
  final Future<void> Function()? onTap;
  final Future<void> Function()? onEdit;
  final String status;

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
    this.status = 'active',
  });


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

  @override
  State<AssetCard> createState() => _AssetCardState();
}

class _AssetCardState extends State<AssetCard> {
  bool _isLoading = false;
  late String _currentStatus;

  @override
  void initState() {
    super.initState();
    _currentStatus = widget.status;
  }

  @override
  void didUpdateWidget(AssetCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.status != oldWidget.status) {
      _currentStatus = widget.status;
    }
  }

  Future<void> _handleAction(Future<void> Function()? action, {bool complete = false}) async {
    if (action == null || _isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      await action();
      if (mounted && complete) {
        setState(() {
          _currentStatus = 'completed';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      child: InkWell(
        onTap: _isLoading ? null : () => _handleAction(widget.onTap),
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
                    widget._getAssetIcon(),
                    color: widget._getAssetColor(),
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      widget.name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (_isLoading)
                     const SizedBox(
                       width: 16,
                       height: 16,
                       child: CircularProgressIndicator(strokeWidth: 2),
                     )
                  else if (widget.onEdit != null && _currentStatus == 'active')
                    IconButton(
                      icon: const Icon(Icons.edit, size: 20),
                      onPressed: () => _handleAction(widget.onEdit, complete: true),
                    )
                  else if (_currentStatus != 'active')
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: Colors.grey[200],
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        _currentStatus == 'completed' ? '已更新' : '已失效',
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.grey[600],
                        ),
                      ),
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
                        widget._formatValue(),
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: Colors.green[700],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  if (widget.riskLevel != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: widget._getRiskColor().withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: widget._getRiskColor().withOpacity(0.3)),
                      ),
                      child: Text(
                        widget._getRiskLabel(),
                        style: TextStyle(
                          color: widget._getRiskColor(),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                ],
              ),
              
              // Tags
              if (widget.tags.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: widget.tags.map((tag) => Chip(
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
}