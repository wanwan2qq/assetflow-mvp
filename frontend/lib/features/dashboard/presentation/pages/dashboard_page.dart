import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import '../../../../core/models/asset.dart';
import '../../../../core/providers/asset_provider.dart';
import '../../../../shared/widgets/portfolio_chart.dart';
import '../../../../shared/widgets/sp_quadrant_chart.dart';
import '../../../chat/presentation/pages/chat_page.dart';

class DashboardPage extends ConsumerWidget {
  const DashboardPage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assetsAsync = ref.watch(assetListProvider);
    final portfolioHealthAsync = ref.watch(portfolioHealthDataProvider);
    
    return Scaffold(
      appBar: AppBar(
        title: const Text('资产仪表板'),
      ),
      body: RefreshIndicator(
        onRefresh: () async {
          ref.invalidate(assetListProvider);
          ref.invalidate(portfolioHealthDataProvider);
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSummaryCard(context, ref, portfolioHealthAsync),
              const SizedBox(height: 16),
              _buildFinancialWellnessScore(context, ref, portfolioHealthAsync),
              const SizedBox(height: 16),
              _buildAssetDistributionChart(context, ref, assetsAsync, portfolioHealthAsync),
              const SizedBox(height: 16),
              _buildSPQuadrantAnalysis(context, ref, portfolioHealthAsync),
              const SizedBox(height: 16),
              _buildRiskWarnings(context, ref, portfolioHealthAsync),
              const SizedBox(height: 16),
              _buildAssetList(context, ref, assetsAsync),
              // 添加底部安全区域，避免被导航栏遮挡
              SizedBox(height: MediaQuery.of(context).padding.bottom + 80),
            ],
          ),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddAssetDialog(context, ref),
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildSummaryCard(BuildContext context, WidgetRef ref, AsyncValue<PortfolioHealth> portfolioHealthAsync) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '总资产概览',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            portfolioHealthAsync.when(
              data: (portfolioHealth) => Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _buildSummaryItem(
                    context, 
                    '净资产', 
                    '¥${_formatCurrency(portfolioHealth.netWorth)}', 
                    Colors.green
                  ),
                  _buildSummaryItem(
                    context, 
                    '房产占比', 
                    '${((portfolioHealth.realEstateRatio ?? 0.0) * 100).toStringAsFixed(1)}%', 
                    (portfolioHealth.realEstateRatio ?? 0.0) > 0.75 ? Colors.red : Colors.orange
                  ),
                  _buildSummaryItem(
                    context, 
                    '流动性比率', 
                    (portfolioHealth.liquidityRatio ?? 0.0).toStringAsFixed(1), 
                    (portfolioHealth.liquidityRatio ?? 0.0) < 3 ? Colors.red : Colors.green
                  ),
                ],
              ),
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Text('加载失败: $error'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryItem(BuildContext context, String label, String value, Color color) {
    return Column(
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }

  Widget _buildFinancialWellnessScore(BuildContext context, WidgetRef ref, AsyncValue<PortfolioHealth> portfolioHealthAsync) {
    return portfolioHealthAsync.when(
      data: (portfolioHealth) {
        // Calculate wellness score (0-100)
        final score = _calculateWellnessScore(portfolioHealth);
        final hasLiquidityAnxiety = _detectLiquidityAnxiety(portfolioHealth);
        
        return Card(
          elevation: hasLiquidityAnxiety ? 4 : 2,
          child: Container(
            decoration: hasLiquidityAnxiety ? BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: Colors.amber, width: 2),
              boxShadow: [
                BoxShadow(
                  color: Colors.amber.withOpacity(0.3),
                  blurRadius: 8,
                  spreadRadius: 2,
                ),
              ],
            ) : null,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.favorite, color: _getScoreColor(score)),
                      const SizedBox(width: 8),
                      Text(
                        '财务健康度',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      const Spacer(),
                      Text(
                        '${score.toStringAsFixed(0)}分',
                        style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                          color: _getScoreColor(score),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  LinearProgressIndicator(
                    value: score / 100,
                    backgroundColor: Colors.grey[200],
                    valueColor: AlwaysStoppedAnimation<Color>(_getScoreColor(score)),
                    minHeight: 8,
                  ),
                  if (hasLiquidityAnxiety) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.warning_amber, color: Colors.amber[700]),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '检测到流动性压力，建议关注现金流管理',
                              style: TextStyle(
                                color: Colors.amber[900],
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }

  double _calculateWellnessScore(PortfolioHealth health) {
    double score = 100.0;
    
    // Deduct points for high real estate ratio
    if (health.realEstateRatio > 0.75) {
      score -= 20;
    } else if (health.realEstateRatio > 0.6) {
      score -= 10;
    }
    
    // Deduct points for low liquidity
    if (health.liquidityRatio < 3) {
      score -= 20;
    } else if (health.liquidityRatio < 6) {
      score -= 10;
    }
    
    // Deduct points for risk warnings
    score -= health.riskWarnings.length * 5;
    
    return score.clamp(0, 100);
  }

  bool _detectLiquidityAnxiety(PortfolioHealth health) {
    // High net worth but low liquidity ratio
    return health.netWorth > 1000000 && health.liquidityRatio < 3;
  }

  Color _getScoreColor(double score) {
    if (score >= 80) return Colors.green;
    if (score >= 60) return Colors.orange;
    return Colors.red;
  }

  Widget _buildAssetDistributionChart(BuildContext context, WidgetRef ref, AsyncValue<List<UserAsset>> assetsAsync, AsyncValue<PortfolioHealth> portfolioHealthAsync) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '资产分布',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            assetsAsync.when(
              data: (assets) {
                final hasLiquidityAnxiety = portfolioHealthAsync.maybeWhen(
                  data: (health) => _detectLiquidityAnxiety(health),
                  orElse: () => false,
                );
                
                // Empty state handled by PortfolioChart widget
                return SizedBox(
                  height: 300,
                  child: PortfolioChart(
                    assets: assets,
                    highlightCash: hasLiquidityAnxiety,
                  ),
                );
              },
              loading: () => const SizedBox(
                height: 300,
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, _) => SizedBox(
                height: 300,
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 48, color: Colors.red[300]),
                      const SizedBox(height: 16),
                      Text('加载失败: $error'),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSPQuadrantAnalysis(BuildContext context, WidgetRef ref, AsyncValue<PortfolioHealth> portfolioHealthAsync) {
    return portfolioHealthAsync.when(
      data: (portfolioHealth) {
        if (portfolioHealth.netWorth == 0) {
          return const SizedBox.shrink();
        }
        
        return SPQuadrantChart(
          portfolioHealth: portfolioHealth,
          onTap: () {
            // 可以添加点击事件，跳转到详细分析页面
          },
        );
      },
      loading: () => Card(
        child: Container(
          height: 300,
          child: const Center(child: CircularProgressIndicator()),
        ),
      ),
      error: (error, _) => const SizedBox.shrink(),
    );
  }

  Widget _buildRiskWarnings(BuildContext context, WidgetRef ref, AsyncValue<PortfolioHealth> portfolioHealthAsync) {
    return portfolioHealthAsync.when(
      data: (portfolioHealth) {
        if (portfolioHealth.riskWarnings.isEmpty) {
          return const SizedBox.shrink();
        }
        
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.warning, color: Colors.orange),
                    const SizedBox(width: 8),
                    Text(
                      '风险提醒',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                ...portfolioHealth.riskWarnings.map((warning) => _buildActionableWarningCard(
                  context,
                  ref,
                  warning,
                )),
              ],
            ),
          ),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }

  Widget _buildActionableWarningCard(BuildContext context, WidgetRef ref, RiskWarning warning) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: _getWarningColor(warning.severity).withOpacity(0.1),
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: _getWarningColor(warning.severity).withOpacity(0.3),
            width: 1.5,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _getWarningIcon(warning.severity),
                  color: _getWarningColor(warning.severity),
                  size: 24,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    warning.message,
                    style: TextStyle(
                      color: _getWarningColor(warning.severity),
                      fontWeight: FontWeight.w600,
                      fontSize: 14,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: () => _navigateToChatWithQuery(context, warning),
                icon: const Icon(Icons.chat_bubble_outline, size: 16),
                label: const Text('咨询AI'),
                style: TextButton.styleFrom(
                  foregroundColor: _getWarningColor(warning.severity),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _navigateToChatWithQuery(BuildContext context, RiskWarning warning) {
    // Generate query based on warning type
    String query = _generateQueryFromWarning(warning);
    
    // Navigate to chat page
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => const ChatPage(),
      ),
    );
    
    // Note: To pre-fill the query, you would need to modify ChatPage to accept an initial message
    // For now, this just navigates to the chat page
  }

  String _generateQueryFromWarning(RiskWarning warning) {
    // Map warning types to helpful queries
    if (warning.type.contains('liquidity') || warning.type.contains('spending')) {
      return '我的流动性不足，应该如何改善现金流？';
    } else if (warning.type.contains('real_estate')) {
      return '我的房产占比过高，应该如何优化资产配置？';
    } else if (warning.type.contains('protection') || warning.type.contains('insurance')) {
      return '我的保障资金不足，应该如何配置保险？';
    } else if (warning.type.contains('investment') || warning.type.contains('growth')) {
      return '我的投资配置有什么问题？应该如何调整？';
    }
    return '如何改善我的资产配置？';
  }

  Color _getWarningColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'high':
        return Colors.red;
      case 'medium':
        return Colors.orange;
      case 'low':
        return Colors.yellow.shade700;
      default:
        return Colors.orange;
    }
  }

  IconData _getWarningIcon(String severity) {
    switch (severity.toLowerCase()) {
      case 'high':
        return Icons.error;
      case 'medium':
        return Icons.warning;
      case 'low':
        return Icons.info;
      default:
        return Icons.warning;
    }
  }
  Widget _buildAssetList(BuildContext context, WidgetRef ref, AsyncValue<List<UserAsset>> assetsAsync) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '资产明细',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            assetsAsync.when(
              data: (assets) {
                if (assets.isEmpty) {
                  return const Center(
                    child: Padding(
                      padding: EdgeInsets.all(32),
                      child: Column(
                        children: [
                          Icon(Icons.account_balance_wallet_outlined, size: 64, color: Colors.grey),
                          SizedBox(height: 16),
                          Text('暂无资产数据', style: TextStyle(color: Colors.grey)),
                          SizedBox(height: 8),
                          Text('点击右下角的 + 按钮添加资产', style: TextStyle(color: Colors.grey, fontSize: 12)),
                        ],
                      ),
                    ),
                  );
                }
                
                return Column(
                  children: assets.map((asset) => _buildAssetTile(context, ref, asset)).toList(),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (error, _) => Center(child: Text('加载失败: $error')),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAssetTile(BuildContext context, WidgetRef ref, UserAsset asset) {
    return ListTile(
      leading: CircleAvatar(
        backgroundColor: _getAssetTypeColor(asset.assetType).withOpacity(0.2),
        child: Icon(
          _getAssetTypeIcon(asset.assetType),
          color: _getAssetTypeColor(asset.assetType),
        ),
      ),
      title: Text(asset.name),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(_getAssetTypeLabel(asset.assetType)),
          if (!asset.isConfirmed)
            Text(
              '未确认',
              style: TextStyle(
                color: Colors.orange,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
        ],
      ),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(
            '¥${_formatCurrency(asset.value)}',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: asset.assetType == AssetType.liability ? Colors.red : Colors.green,
            ),
          ),
          if (asset.metadata != null && asset.metadata!.isNotEmpty)
            Text(
              _getAssetMetadataText(asset),
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Colors.grey,
              ),
            ),
        ],
      ),
      onTap: () => _showAssetDetailsDialog(context, ref, asset),
    );
  }

  // Helper methods
  String _formatCurrency(double? value) {
    if (value == null) return '0';
    if (value >= 10000) {
      return '${(value / 10000).toStringAsFixed(1)}万';
    } else if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}千';
    } else {
      return value.toStringAsFixed(0);
    }
  }

  IconData _getAssetTypeIcon(AssetType type) {
    switch (type) {
      case AssetType.realEstate:
        return Icons.home;
      case AssetType.cash:
        return Icons.account_balance;
      case AssetType.investment:
        return Icons.trending_up;
      case AssetType.insurance:
        return Icons.security;
      case AssetType.liability:
        return Icons.credit_card;
    }
  }

  Color _getAssetTypeColor(AssetType type) {
    switch (type) {
      case AssetType.realEstate:
        return Colors.blue;
      case AssetType.cash:
        return Colors.green;
      case AssetType.investment:
        return Colors.orange;
      case AssetType.insurance:
        return Colors.purple;
      case AssetType.liability:
        return Colors.red;
    }
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

  String _getAssetMetadataText(UserAsset asset) {
    if (asset.metadata == null) return '';
    
    final metadata = asset.metadata!;
    final parts = <String>[];
    
    if (metadata['area'] != null) {
      parts.add('${metadata['area']}平米');
    }
    if (metadata['location'] != null) {
      parts.add(metadata['location']);
    }
    if (metadata['rate'] != null) {
      parts.add('${metadata['rate']}%');
    }
    
    return parts.join(' • ');
  }

  // Dialog functions
  void _showAddAssetDialog(BuildContext context, WidgetRef ref) {
    showDialog(
      context: context,
      builder: (context) => _AddAssetDialog(ref: ref),
    );
  }

  void _showAssetDetailsDialog(BuildContext context, WidgetRef ref, UserAsset asset) {
    showDialog(
      context: context,
      builder: (context) => _AssetDetailsDialog(asset: asset, ref: ref),
    );
  }
}

// Add Asset Dialog
class _AddAssetDialog extends StatefulWidget {
  final WidgetRef ref;

  const _AddAssetDialog({required this.ref});

  @override
  State<_AddAssetDialog> createState() => _AddAssetDialogState();
}

class _AddAssetDialogState extends State<_AddAssetDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _valueController = TextEditingController();
  AssetType _selectedType = AssetType.cash;
  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _valueController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('添加资产'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<AssetType>(
              value: _selectedType,
              decoration: const InputDecoration(
                labelText: '资产类型',
                border: OutlineInputBorder(),
              ),
              items: AssetType.values.map((type) => DropdownMenuItem(
                value: type,
                child: Text(_getAssetTypeLabel(type)),
              )).toList(),
              onChanged: (value) {
                if (value != null) {
                  setState(() {
                    _selectedType = value;
                  });
                }
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: '资产名称',
                border: OutlineInputBorder(),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return '请输入资产名称';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _valueController,
              decoration: const InputDecoration(
                labelText: '资产价值 (元)',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return '请输入资产价值';
                }
                final doubleValue = double.tryParse(value);
                if (doubleValue == null || doubleValue <= 0) {
                  return '请输入有效的数值';
                }
                return null;
              },
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _handleSubmit,
          child: _isLoading 
            ? const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Text('添加'),
        ),
      ],
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

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      await widget.ref.read(assetListProvider.notifier).createAsset(
        assetType: _selectedType,
        name: _nameController.text.trim(),
        value: double.parse(_valueController.text),
        isConfirmed: true,
      );

      if (mounted) {
        Navigator.of(context).pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('资产添加成功')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('添加失败: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
}

// Asset Details Dialog
class _AssetDetailsDialog extends StatelessWidget {
  final UserAsset asset;
  final WidgetRef ref;

  const _AssetDetailsDialog({required this.asset, required this.ref});

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(asset.name),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildDetailRow('类型', _getAssetTypeLabel(asset.assetType)),
          _buildDetailRow('价值', '¥${_formatCurrency(asset.value)}'),
          _buildDetailRow('状态', asset.isConfirmed ? '已确认' : '未确认'),
          _buildDetailRow('创建时间', _formatDate(asset.createdAt)),
          if (asset.updatedAt != asset.createdAt)
            _buildDetailRow('更新时间', _formatDate(asset.updatedAt)),
          if (asset.metadata != null && asset.metadata!.isNotEmpty)
            ..._buildMetadataRows(asset.metadata!),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('关闭'),
        ),
        TextButton(
          onPressed: () => _showDeleteConfirmation(context),
          style: TextButton.styleFrom(foregroundColor: Colors.red),
          child: const Text('删除'),
        ),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              '$label:',
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }

  List<Widget> _buildMetadataRows(Map<String, dynamic> metadata) {
    return metadata.entries.map((entry) {
      return _buildDetailRow(entry.key, entry.value.toString());
    }).toList();
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

  String _formatCurrency(double? value) {
    if (value == null) return '0';
    if (value >= 10000) {
      return '${(value / 10000).toStringAsFixed(1)}万';
    } else if (value >= 1000) {
      return '${(value / 1000).toStringAsFixed(1)}千';
    } else {
      return value.toStringAsFixed(0);
    }
  }

  String _formatDate(DateTime date) {
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  void _showDeleteConfirmation(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('确定要删除资产 "${asset.name}" 吗？此操作不可撤销。'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () async {
              try {
                await ref.read(assetListProvider.notifier).deleteAsset(asset.id);
                if (context.mounted) {
                  Navigator.of(context).pop(); // Close confirmation dialog
                  Navigator.of(context).pop(); // Close details dialog
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('资产删除成功')),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('删除失败: $e')),
                  );
                }
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: const Text('删除', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
    );
  }
}