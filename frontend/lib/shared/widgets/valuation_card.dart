import 'package:flutter/material.dart';

class ValuationCard extends StatelessWidget {
  final String propertyName;
  final double estimatedValue;
  final String pricePerSqm;
  final VoidCallback? onConfirm;
  final VoidCallback? onEdit;

  const ValuationCard({
    super.key,
    required this.propertyName,
    required this.estimatedValue,
    required this.pricePerSqm,
    this.onConfirm,
    this.onEdit,
  });

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
              propertyName,
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
                      '¥${(estimatedValue / 10000).toStringAsFixed(0)}万',
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
                      pricePerSqm,
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
                    onPressed: onEdit,
                    child: const Text('修改'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    key: const Key('confirm_valuation_button'),
                    onPressed: onConfirm,
                    child: const Text('确认'),
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