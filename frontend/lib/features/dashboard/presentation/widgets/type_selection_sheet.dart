import 'package:flutter/material.dart';
import '../../../../core/models/asset.dart';

class TypeSelectionSheet extends StatelessWidget {
  final VoidCallback onRecordTransaction;
  final ValueChanged<AssetType> onSelectAssetType;

  const TypeSelectionSheet({
    super.key,
    required this.onRecordTransaction,
    required this.onSelectAssetType,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: colorScheme.surfaceContainer,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: SafeArea( // Ensure content safe area
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // M3 Drag Handle
            const SizedBox(height: 16),
            Container(
              width: 32,
              height: 4,
              decoration: BoxDecoration(
                color: colorScheme.outlineVariant,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 16),
            
            // Header
            Text(
              '添加内容',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 24),

            // 1. Transaction Button (Priority Action)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: SizedBox(
                width: double.infinity,
                height: 56,
                child: FilledButton.tonalIcon(
                  onPressed: onRecordTransaction,
                  icon: const Icon(Icons.edit_note_rounded),
                  label: const Text('记一笔'),
                  style: FilledButton.styleFrom(
                    backgroundColor: colorScheme.primaryContainer,
                    foregroundColor: colorScheme.onPrimaryContainer,
                    textStyle: theme.textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ),

            const SizedBox(height: 24),
            
            // Divider with Label
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Row(
                children: [
                  Expanded(child: Divider(color: colorScheme.outlineVariant)),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: Text(
                      '或添加新资产',
                      style: theme.textTheme.labelMedium?.copyWith(
                        color: colorScheme.onSurfaceVariant,
                      ),
                    ),
                  ),
                  Expanded(child: Divider(color: colorScheme.outlineVariant)),
                ],
              ),
            ),
            
            const SizedBox(height: 24),

            // 2. Asset Grid (3 + 2 Layout)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                children: [
                  // First Row: 3 items
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      _buildAssetItem(context, AssetType.realEstate, '房产', Icons.house_rounded, Colors.orange),
                      _buildAssetItem(context, AssetType.liability, '负债', Icons.credit_card_rounded, Colors.redAccent),
                      _buildAssetItem(context, AssetType.investment, '投资', Icons.show_chart_rounded, Colors.purpleAccent),
                    ],
                  ),
                  const SizedBox(height: 24),
                  // Second Row: 2 items (Centered)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _buildAssetItem(context, AssetType.insurance, '保险', Icons.security_rounded, Colors.green),
                      const SizedBox(width: 48), // Spacing between the two items
                      _buildAssetItem(context, AssetType.cash, '现金账户', Icons.account_balance_wallet_rounded, Colors.teal),
                    ],
                  ),
                ],
              ),
            ),

            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }

  Widget _buildAssetItem(
    BuildContext context,
    AssetType type,
    String label,
    IconData icon,
    Color color,
  ) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;
    
    // Check for dark mode to adjust opacity if needed for contrast
    final isDark = theme.brightness == Brightness.dark;
    final bgOpacity = isDark ? 0.2 : 0.15; // Slightly higher opacity for better visibility

    return GestureDetector(
      onTap: () => onSelectAssetType(type),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 64, // Fixed larger size
            height: 64,
            decoration: BoxDecoration(
              color: color.withOpacity(bgOpacity), // Semantic background
              shape: BoxShape.circle,
            ),
            child: Icon(icon, color: color, size: 32), // Larger icon
          ),
          const SizedBox(height: 12),
          Text(
            label,
            style: theme.textTheme.labelMedium?.copyWith(
              color: colorScheme.onSurface,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
