import 'package:flutter/material.dart';
import '../../core/models/asset.dart';

class SPQuadrantChart extends StatelessWidget {
  final PortfolioHealth portfolioHealth;
  final VoidCallback? onTap;

  const SPQuadrantChart({
    super.key,
    required this.portfolioHealth,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final quadrantData = _calculateQuadrantData();
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '标准普尔四象限分析',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            // Use AspectRatio to ensure square layout with proper spacing
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 20),
              child: AspectRatio(
                aspectRatio: 1.0,
                child: _buildQuadrantGrid(context, quadrantData),
              ),
            ),
            const SizedBox(height: 16),
            _buildDynamicContextText(context, quadrantData),
            const SizedBox(height: 12),
            _buildQuadrantLegend(context, quadrantData),
          ],
        ),
      ),
    );
  }

  Widget _buildDynamicContextText(BuildContext context, SPQuadrantData data) {
    // Check if spending allocation is below 10%
    final spendingIdeal = data.idealRatios['spending'] ?? 0.10;
    
    if (spendingIdeal < 0.10) {
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.blue.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.blue.withOpacity(0.3)),
        ),
        child: Row(
          children: [
            Icon(Icons.lightbulb_outline, color: Colors.blue[700], size: 20),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '💡 基于您的支出分析，AI建议预留更精准的流动资金，而非固定的10%。',
                style: TextStyle(
                  color: Colors.blue[900],
                  fontSize: 13,
                ),
              ),
            ),
          ],
        ),
      );
    }
    
    return const SizedBox.shrink();
  }

  SPQuadrantData _calculateQuadrantData() {
    // Use dynamic ideal allocations from backend if available (these are ratios 0-1)
    final idealRatios = portfolioHealth.idealAllocations ?? {
      'spending': 0.10,    // 要花的钱 (10%)
      'life': 0.20,        // 保命的钱 (20%)
      'growth': 0.30,      // 生钱的钱 (30%)
      'preservation': 0.40, // 保本升值的钱 (40%)
    };
    
    // Backend returns absolute amounts, need to convert to ratios
    Map<String, double> currentRatios;
    if (portfolioHealth.quadrantAllocations != null && portfolioHealth.netWorth > 0) {
      // Convert absolute amounts to ratios
      currentRatios = portfolioHealth.quadrantAllocations!.map(
        (key, value) => MapEntry(key, value / portfolioHealth.netWorth),
      );
    } else {
      // Fallback to calculated ratios
      currentRatios = {
        'spending': _calculateEmergencyRatio(),
        'life': _calculateProtectionRatio(),
        'growth': _calculateInvestmentRatio(),
        'preservation': _calculatePreservationRatio(),
      };
    }
    
    return SPQuadrantData(
      idealRatios: idealRatios,
      currentRatios: currentRatios,
      netWorth: portfolioHealth.netWorth,
      recommendations: _generateRecommendations(idealRatios, currentRatios),
    );
  }

  double _calculateEmergencyRatio() {
    // 简化：假设现金类资产为应急资金
    return 0.05; // 示例值
  }

  double _calculateProtectionRatio() {
    // 简化：假设保险类资产为保障资金
    return 0.15; // 示例值
  }

  double _calculateInvestmentRatio() {
    // 简化：假设投资类资产为投资资金
    return 0.25; // 示例值
  }

  double _calculatePreservationRatio() {
    // 简化：假设房产为保本升值资金
    return portfolioHealth.realEstateRatio;
  }

  List<String> _generateRecommendations(
    Map<String, double> ideal,
    Map<String, double> current,
  ) {
    final recommendations = <String>[];
    
    ideal.forEach((quadrant, idealRatio) {
      final currentRatio = current[quadrant] ?? 0;
      final difference = idealRatio - currentRatio;
      
      if (difference.abs() > 0.05) { // 5%以上差异才提醒
        final quadrantName = _getQuadrantName(quadrant);
        if (difference > 0) {
          recommendations.add('建议增加${quadrantName}配置 ${(difference * 100).toStringAsFixed(1)}%');
        } else {
          recommendations.add('建议减少${quadrantName}配置 ${(difference.abs() * 100).toStringAsFixed(1)}%');
        }
      }
    });
    
    return recommendations;
  }

  String _getQuadrantName(String quadrant) {
    switch (quadrant) {
      case 'spending':
        return '要花的钱';
      case 'life':
        return '保命的钱';
      case 'growth':
        return '生钱的钱';
      case 'preservation':
        return '保本升值的钱';
      // Legacy key support
      case 'emergency':
        return '要花的钱';
      case 'protection':
        return '保命的钱';
      case 'investment':
        return '生钱的钱';
      default:
        return quadrant;
    }
  }

  Widget _buildQuadrantGrid(BuildContext context, SPQuadrantData data) {
    return GridView.count(
      crossAxisCount: 2,
      crossAxisSpacing: 8,
      mainAxisSpacing: 8,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        _buildQuadrantTile(
          context,
          '要花的钱',
          '日常开销',
          '${((data.idealRatios['spending'] ?? 0.10) * 100).toStringAsFixed(0)}%',
          '${((data.currentRatios['spending'] ?? 0.0) * 100).toStringAsFixed(1)}%',
          Colors.red,
          Icons.shopping_cart,
          'spending',
          data,
        ),
        _buildQuadrantTile(
          context,
          '保命的钱',
          '保险保障',
          '${((data.idealRatios['life'] ?? 0.20) * 100).toStringAsFixed(0)}%',
          '${((data.currentRatios['life'] ?? 0.0) * 100).toStringAsFixed(1)}%',
          Colors.blue,
          Icons.security,
          'life',
          data,
        ),
        _buildQuadrantTile(
          context,
          '生钱的钱',
          '投资理财',
          '${((data.idealRatios['growth'] ?? 0.30) * 100).toStringAsFixed(0)}%',
          '${((data.currentRatios['growth'] ?? 0.0) * 100).toStringAsFixed(1)}%',
          Colors.green,
          Icons.trending_up,
          'growth',
          data,
        ),
        _buildQuadrantTile(
          context,
          '保本升值的钱',
          '稳健增值',
          '${((data.idealRatios['preservation'] ?? 0.40) * 100).toStringAsFixed(0)}%',
          '${((data.currentRatios['preservation'] ?? 0.0) * 100).toStringAsFixed(1)}%',
          Colors.orange,
          Icons.home,
          'preservation',
          data,
        ),
      ],
    );
  }

  Widget _buildQuadrantTile(
    BuildContext context,
    String title,
    String subtitle,
    String idealRatio,
    String currentRatio,
    Color color,
    IconData icon,
    String quadrantKey,
    SPQuadrantData data,
  ) {
    final isBalanced = _isRatioBalanced(idealRatio, currentRatio);
    
    return InkWell(
      onTap: () => _showQuadrantTooltip(context, title, quadrantKey, data),
      borderRadius: BorderRadius.circular(8),
      child: Container(
        decoration: BoxDecoration(
          color: color.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isBalanced ? Colors.green : Colors.orange,
            width: 2,
          ),
        ),
        padding: const EdgeInsets.all(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 4),
            Text(
              title,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: color,
              ),
              textAlign: TextAlign.center,
            ),
            Text(
              subtitle,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '理想: $idealRatio',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '当前: $currentRatio',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: isBalanced ? Colors.green : Colors.orange,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  void _showQuadrantTooltip(BuildContext context, String title, String quadrantKey, SPQuadrantData data) {
    final gap = portfolioHealth.allocationGaps?[quadrantKey];
    final ideal = data.idealRatios[quadrantKey];
    
    String explanation = '';
    switch (quadrantKey) {
      case 'spending':
        explanation = '建议预留3-6个月的生活开支作为应急资金';
        break;
      case 'protection':
        explanation = '用于保险保障，抵御意外风险';
        break;
      case 'growth':
        explanation = '用于投资理财，追求资产增值';
        break;
      case 'preservation':
        explanation = '用于稳健保值，如房产、债券等';
        break;
    }
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(explanation),
            const SizedBox(height: 12),
            if (ideal != null)
              Text('目标配置: ${(ideal * 100).toStringAsFixed(0)}%'),
            if (gap != null)
              Text(
                '差距: ${gap > 0 ? "+" : ""}${(gap * 100).toStringAsFixed(1)}%',
                style: TextStyle(
                  color: gap > 0 ? Colors.red : Colors.green,
                  fontWeight: FontWeight.bold,
                ),
              ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('关闭'),
          ),
        ],
      ),
    );
  }

  bool _isRatioBalanced(String idealStr, String currentStr) {
    final ideal = double.tryParse(idealStr.replaceAll('%', '')) ?? 0;
    final current = double.tryParse(currentStr.replaceAll('%', '')) ?? 0;
    return (ideal - current).abs() <= 5; // 5%以内认为平衡
  }

  Widget _buildQuadrantLegend(BuildContext context, SPQuadrantData data) {
    if (data.recommendations.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.green.withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            Icon(Icons.check_circle, color: Colors.green),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '您的资产配置相对均衡',
                style: TextStyle(color: Colors.green[700]),
              ),
            ),
          ],
        ),
      );
    }
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '配置建议',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 8),
        ...data.recommendations.map((recommendation) => Padding(
          padding: const EdgeInsets.only(bottom: 4),
          child: Row(
            children: [
              Icon(Icons.lightbulb, color: Colors.amber, size: 16),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  recommendation,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ],
          ),
        )),
      ],
    );
  }
}

class SPQuadrantData {
  final Map<String, double> idealRatios;
  final Map<String, double> currentRatios;
  final double netWorth;
  final List<String> recommendations;

  SPQuadrantData({
    required this.idealRatios,
    required this.currentRatios,
    required this.netWorth,
    required this.recommendations,
  });
}