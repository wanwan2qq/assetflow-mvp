import 'package:flutter/material.dart';

class ValuationCard extends StatefulWidget {
  final String propertyName;
  final double estimatedValue;
  final String pricePerSqm;
  final Future<void> Function()? onConfirm;
  final Future<void> Function()? onEdit;
  final String status;

  const ValuationCard({
    super.key,
    required this.propertyName,
    required this.estimatedValue,
    required this.pricePerSqm,
    this.onConfirm,
    this.onEdit,
    this.status = 'active',
  });

  @override
  State<ValuationCard> createState() => _ValuationCardState();
}

class _ValuationCardState extends State<ValuationCard> {
  bool _isLoading = false;
  late String _currentStatus;

  @override
  void initState() {
    super.initState();
    _currentStatus = widget.status;
  }

  @override
  void didUpdateWidget(ValuationCard oldWidget) {
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
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.home, color: Colors.blue),
                const SizedBox(width: 8),
                Text(
                  '房产估值',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              widget.propertyName,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '估值',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                    Text(
                      '¥${(widget.estimatedValue / 10000).toStringAsFixed(0)}万',
                      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        color: Colors.green,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '单价',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey,
                      ),
                    ),
                    Text(
                      widget.pricePerSqm,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      // Always allow modification, regardless of status
                      onPressed: _isLoading ? null : () => _handleAction(widget.onEdit, complete: true),
                      child: const Text('修改'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: _currentStatus == 'active'
                        ? ElevatedButton(
                            key: const Key('confirm_valuation_button'),
                            onPressed: _isLoading ? null : () => _handleAction(widget.onConfirm, complete: true),
                            child: _isLoading 
                                ? const SizedBox(
                                    width: 20, 
                                    height: 20, 
                                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)
                                  )
                                : const Text('确认'),
                          )
                        : ElevatedButton(
                            onPressed: null, // Disabled
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.grey[100],
                              disabledBackgroundColor: Colors.grey[100],
                              elevation: 0,
                            ),
                            child: Text(
                              '已确认',
                              style: TextStyle(
                                color: Colors.grey[600],
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                  ),
                ],
              ),
            const SizedBox(height: 8),
            Text(
              '* 估值基于市场数据的保守估算',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      ),
    );
  }
}