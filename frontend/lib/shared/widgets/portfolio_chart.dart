import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../core/models/asset.dart';

// Color palette for asset types - ensures consistency across pie chart and legend
const Map<AssetType, Color> assetTypeColors = {
  AssetType.realEstate: Colors.blue,
  AssetType.cash: Colors.green,
  AssetType.investment: Colors.orange,
  AssetType.insurance: Colors.purple,
  AssetType.liability: Colors.red,
};

// Data class for enhanced asset grouping
class AssetGroupData {
  final String label;
  final Color color;
  final double value;
  final AssetType assetType;

  AssetGroupData({
    required this.label,
    required this.color,
    required this.value,
    required this.assetType,
  });
}

class PortfolioChart extends StatefulWidget {
  final List<UserAsset> assets;
  final String? title;
  final VoidCallback? onTap;
  final bool highlightCash;

  const PortfolioChart({
    super.key,
    required this.assets,
    this.title,
    this.onTap,
    this.highlightCash = false,
  });

  @override
  State<PortfolioChart> createState() => _PortfolioChartState();
}

class _PortfolioChartState extends State<PortfolioChart> {
  int touchedIndex = -1;

  @override
  Widget build(BuildContext context) {
    final assetDistribution = _calculateEnhancedAssetDistribution();
    final totalValue = _getTotalAssetValue();
    
    // Empty state - no assets
    if (assetDistribution.isEmpty || totalValue <= 0) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.pie_chart_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              '暂无资产数据',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '请先添加资产',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey[500],
              ),
            ),
          ],
        ),
      );
    }

    // Pie chart with legend badges - fixed size at 70% scale (210x210)
    return Center(
      child: SizedBox(
        width: 210,
        height: 210,
        child: Stack(
          alignment: Alignment.center,
          children: [
            PieChart(
              PieChartData(
                pieTouchData: PieTouchData(
                  touchCallback: (FlTouchEvent event, pieTouchResponse) {
                    setState(() {
                      if (!event.isInterestedForInteractions ||
                          pieTouchResponse == null ||
                          pieTouchResponse.touchedSection == null) {
                        touchedIndex = -1;
                        return;
                      }
                      touchedIndex = pieTouchResponse
                          .touchedSection!.touchedSectionIndex;
                    });
                  },
                ),
                borderData: FlBorderData(show: false),
                sectionsSpace: 2,
                centerSpaceRadius: 42,
                sections: _buildEnhancedPieChartSections(assetDistribution, totalValue),
              ),
            ),
            // Glowing effect for cash when liquidity anxiety is detected
            if (widget.highlightCash && _hasCashAssets())
              IgnorePointer(
                child: Container(
                  width: 210,
                  height: 210,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.amber.withOpacity(0.4),
                        blurRadius: 20,
                        spreadRadius: 5,
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }

  bool _hasCashAssets() {
    return widget.assets.any((asset) => asset.assetType == AssetType.cash);
  }

  /// Enhanced asset distribution with risk-level sub-grouping for investments
  /// Groups investment assets into "Investment (Safe)" and "Investment (Risk)"
  Map<String, AssetGroupData> _calculateEnhancedAssetDistribution() {
    final distribution = <String, AssetGroupData>{};
    
    for (final asset in widget.assets) {
      if (asset.assetType == AssetType.liability || asset.value <= 0) continue;
      
      // Special handling for investment assets - split by risk level
      if (asset.assetType == AssetType.investment) {
        final riskLevel = asset.metadata?['risk_level'] as String?;
        
        if (riskLevel == 'low') {
          final key = 'investment_safe';
          distribution[key] = AssetGroupData(
            label: '投资(稳健)',
            color: Colors.teal,
            value: (distribution[key]?.value ?? 0.0) + asset.value,
            assetType: AssetType.investment,
          );
        } else {
          // medium or high risk
          final key = 'investment_risk';
          distribution[key] = AssetGroupData(
            label: '投资(进取)',
            color: Colors.deepOrange,
            value: (distribution[key]?.value ?? 0.0) + asset.value,
            assetType: AssetType.investment,
          );
        }
      } else {
        // Regular asset types
        final key = asset.assetType.toString();
        distribution[key] = AssetGroupData(
          label: _getAssetTypeLabel(asset.assetType),
          color: assetTypeColors[asset.assetType] ?? Colors.grey,
          value: (distribution[key]?.value ?? 0.0) + asset.value,
          assetType: asset.assetType,
        );
      }
    }
    
    return distribution;
  }

  /// Dynamically aggregate asset values by type (legacy method)
  /// Only includes positive value assets (excluding liabilities from pie chart)
  Map<AssetType, double> _calculateAssetDistribution() {
    final distribution = <AssetType, double>{};
    
    // Aggregate values by asset type (excluding liabilities from pie chart)
    for (final asset in widget.assets) {
      if (asset.assetType != AssetType.liability && asset.value > 0) {
        distribution[asset.assetType] = 
            (distribution[asset.assetType] ?? 0.0) + asset.value;
      }
    }
    
    return distribution;
  }

  /// Calculate total asset value (assets - liabilities)
  double _getTotalAssetValue() {
    double totalAssets = 0;
    
    // Only sum positive value assets (excluding liabilities)
    for (final asset in widget.assets) {
      if (asset.assetType != AssetType.liability && asset.value > 0) {
        totalAssets += asset.value;
      }
    }
    
    return totalAssets;
  }

  List<PieChartSectionData> _buildEnhancedPieChartSections(
    Map<String, AssetGroupData> distribution,
    double totalValue,
  ) {
    // Division by zero protection
    if (totalValue <= 0) return [];
    
    return distribution.entries.toList().asMap().entries.map((entry) {
      final index = entry.key;
      final groupKey = entry.value.key;
      final groupData = entry.value.value;
      final percentage = (groupData.value / totalValue) * 100;
      
      final isTouched = index == touchedIndex;
      final isCash = groupData.assetType == AssetType.cash;
      
      // Highlight cash with glow if liquidity anxiety detected
      final radius = isTouched ? 77.0 : (isCash && widget.highlightCash ? 73.0 : 70.0);

      return PieChartSectionData(
        color: groupData.color,
        value: groupData.value,
        title: '${percentage.toStringAsFixed(1)}%',
        radius: radius,
        titleStyle: TextStyle(
          fontSize: isTouched ? 14.0 : 12.0,
          fontWeight: FontWeight.bold,
          color: Colors.white,
          shadows: [
            Shadow(
              color: Colors.black.withOpacity(0.3),
              offset: const Offset(1, 1),
              blurRadius: 2,
            ),
          ],
        ),
        badgeWidget: _buildEnhancedBadge(groupData, percentage, isTouched),
        badgePositionPercentageOffset: 1.3,
      );
    }).toList();
  }

  Widget _buildEnhancedBadge(AssetGroupData groupData, double percentage, bool isTouched) {
    // Only show badge for sections > 5%
    if (percentage <= 5) return const SizedBox.shrink();
    
    final isCash = groupData.assetType == AssetType.cash;
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
      decoration: BoxDecoration(
        color: groupData.color.withOpacity(0.9),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: (isCash && widget.highlightCash) ? Colors.amber : Colors.white,
          width: (isCash && widget.highlightCash) ? 2.0 : 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: (isCash && widget.highlightCash) 
                ? Colors.amber.withOpacity(0.5)
                : Colors.black.withOpacity(0.2),
            blurRadius: (isCash && widget.highlightCash) ? 6 : 3,
            offset: const Offset(0, 1.5),
          ),
        ],
      ),
      child: Text(
        groupData.label,
        style: TextStyle(
          color: Colors.white,
          fontSize: isTouched ? 11.0 : 10.0,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  List<PieChartSectionData> _buildPieChartSections(
    Map<AssetType, double> distribution,
    double totalValue,
  ) {
    // Division by zero protection
    if (totalValue <= 0) return [];
    
    return distribution.entries.toList().asMap().entries.map((entry) {
      final index = entry.key;
      final assetType = entry.value.key;
      final value = entry.value.value;
      final percentage = (value / totalValue) * 100;
      
      final isTouched = index == touchedIndex;
      final radius = isTouched ? 77.0 : 70.0; // Scaled down from 110/100

      return PieChartSectionData(
        color: assetTypeColors[assetType] ?? Colors.grey,
        value: value,
        title: '${percentage.toStringAsFixed(1)}%',
        radius: radius,
        titleStyle: TextStyle(
          fontSize: isTouched ? 14.0 : 12.0, // Slightly smaller text
          fontWeight: FontWeight.bold,
          color: Colors.white,
          shadows: [
            Shadow(
              color: Colors.black.withOpacity(0.3),
              offset: const Offset(1, 1),
              blurRadius: 2,
            ),
          ],
        ),
        badgeWidget: _buildBadge(assetType, percentage, isTouched),
        badgePositionPercentageOffset: 1.3,
      );
    }).toList();
  }

  Widget _buildBadge(AssetType assetType, double percentage, bool isTouched) {
    // Only show badge for sections > 5%
    if (percentage <= 5) return const SizedBox.shrink();
    
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3), // Smaller padding
      decoration: BoxDecoration(
        color: (assetTypeColors[assetType] ?? Colors.grey).withOpacity(0.9),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: Colors.white,
          width: 1.5, // Thinner border
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 3,
            offset: const Offset(0, 1.5),
          ),
        ],
      ),
      child: Text(
        _getAssetTypeLabel(assetType),
        style: TextStyle(
          color: Colors.white,
          fontSize: isTouched ? 11.0 : 10.0, // Smaller font
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  String _getAssetTypeLabel(AssetType type) {
    switch (type) {
      case AssetType.realEstate:
        return '房产';
      case AssetType.cash:
        return '现金';
      case AssetType.investment:
        return '投资';
      case AssetType.insurance:
        return '保险';
      case AssetType.liability:
        return '负债';
    }
  }

  String _formatCurrency(double value) {
    if (value >= 10000) {
      return '${(value / 10000).toStringAsFixed(1)}万';
    } else if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}千';
    } else {
      return value.toStringAsFixed(0);
    }
  }
}