import 'package:flutter/material.dart';

enum ActionCardType {
  insurance,
  broker,
  investment,
  warning,
}

class ActionCard extends StatelessWidget {
  final ActionCardType type;
  final String title;
  final String description;
  final String? provider;
  final String? contactInfo;
  final VoidCallback? onTap;

  const ActionCard({
    super.key,
    required this.type,
    required this.title,
    required this.description,
    this.provider,
    this.contactInfo,
    this.onTap,
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
              Row(
                children: [
                  Icon(
                    _getIcon(),
                    color: _getColor(),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: _getColor(),
                      ),
                    ),
                  ),
                  if (onTap != null)
                    Icon(
                      Icons.chevron_right,
                      color: Colors.grey[400],
                    ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                description,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              if (provider != null) ...[
                const SizedBox(height: 8),
                Row(
                  children: [
                    Icon(
                      Icons.business,
                      size: 16,
                      color: Colors.grey[600],
                    ),
                    const SizedBox(width: 4),
                    Text(
                      provider!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
              if (contactInfo != null) ...[
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(
                      Icons.contact_phone,
                      size: 16,
                      color: Colors.grey[600],
                    ),
                    const SizedBox(width: 4),
                    Text(
                      contactInfo!,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  IconData _getIcon() {
    switch (type) {
      case ActionCardType.insurance:
        return Icons.security;
      case ActionCardType.broker:
        return Icons.person_outline;
      case ActionCardType.investment:
        return Icons.trending_up;
      case ActionCardType.warning:
        return Icons.warning;
    }
  }

  Color _getColor() {
    switch (type) {
      case ActionCardType.insurance:
        return Colors.blue;
      case ActionCardType.broker:
        return Colors.green;
      case ActionCardType.investment:
        return Colors.orange;
      case ActionCardType.warning:
        return Colors.red;
    }
  }
}