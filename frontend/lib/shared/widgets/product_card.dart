import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class ProductCard extends StatelessWidget {
  final String name;
  final String provider;
  final String category;
  final String description;
  final String? price;
  final String? roi;
  final String? buyNowLink;
  final Map<String, dynamic>? contactInfo;
  final String priority;
  final String? reason;
  final VoidCallback? onTap;
  final VoidCallback? onContact;

  const ProductCard({
    super.key,
    required this.name,
    required this.provider,
    required this.category,
    required this.description,
    this.price,
    this.roi,
    this.buyNowLink,
    this.contactInfo,
    this.priority = 'medium',
    this.reason,
    this.onTap,
    this.onContact,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8),
      elevation: _getPriorityElevation(),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: _getPriorityBorder(),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header with product info
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: _getCategoryColor().withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Icon(
                        _getCategoryIcon(),
                        color: _getCategoryColor(),
                        size: 20,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            name,
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            provider,
                            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                    ),
                    if (priority == 'high')
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.red[100],
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '推荐',
                          style: TextStyle(
                            color: Colors.red[700],
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                  ],
                ),
                
                const SizedBox(height: 12),
                
                // Description
                Text(
                  description,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                
                // Price and ROI
                if (price != null || roi != null) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      if (price != null) ...[
                        Icon(Icons.attach_money, size: 16, color: Colors.grey[600]),
                        const SizedBox(width: 4),
                        Text(
                          price!,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.grey[700],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                      if (price != null && roi != null)
                        Container(
                          margin: const EdgeInsets.symmetric(horizontal: 8),
                          width: 1,
                          height: 12,
                          color: Colors.grey[300],
                        ),
                      if (roi != null) ...[
                        Icon(Icons.trending_up, size: 16, color: Colors.green[600]),
                        const SizedBox(width: 4),
                        Text(
                          roi!,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                            color: Colors.green[700],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
                
                // Reason
                if (reason != null) ...[
                  const SizedBox(height: 8),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.blue[50],
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.lightbulb_outline, size: 16, color: Colors.blue[600]),
                        const SizedBox(width: 6),
                        Expanded(
                          child: Text(
                            reason!,
                            style: TextStyle(
                              color: Colors.blue[700],
                              fontSize: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                
                const SizedBox(height: 16),
                
                // Action buttons
                Row(
                  children: [
                    if (contactInfo != null)
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: onContact ?? _handleContact,
                          icon: const Icon(Icons.phone, size: 16),
                          label: const Text('联系咨询'),
                          style: OutlinedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                        ),
                      ),
                    if (contactInfo != null && buyNowLink != null)
                      const SizedBox(width: 12),
                    if (buyNowLink != null)
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: _handleBuyNow,
                          icon: const Icon(Icons.shopping_cart, size: 16),
                          label: const Text('立即购买'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: _getCategoryColor(),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(vertical: 8),
                          ),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  double _getPriorityElevation() {
    switch (priority) {
      case 'high':
        return 4.0;
      case 'medium':
        return 2.0;
      default:
        return 1.0;
    }
  }

  Border? _getPriorityBorder() {
    if (priority == 'high') {
      return Border.all(color: Colors.orange.withOpacity(0.3), width: 1);
    }
    return null;
  }

  IconData _getCategoryIcon() {
    switch (category.toLowerCase()) {
      case 'insurance':
        return Icons.security;
      case 'investment':
        return Icons.trending_up;
      case 'broker':
        return Icons.person_outline;
      case 'loan':
        return Icons.account_balance;
      default:
        return Icons.business;
    }
  }

  Color _getCategoryColor() {
    switch (category.toLowerCase()) {
      case 'insurance':
        return Colors.blue;
      case 'investment':
        return Colors.green;
      case 'broker':
        return Colors.orange;
      case 'loan':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  void _handleContact() {
    if (contactInfo != null) {
      final phone = contactInfo!['phone'] as String?;
      if (phone != null) {
        launchUrl(Uri.parse('tel:$phone'));
      }
    }
  }

  void _handleBuyNow() {
    if (buyNowLink != null) {
      launchUrl(Uri.parse(buyNowLink!));
    }
  }
}