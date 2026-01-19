import 'package:flutter/material.dart';
import '../../../../shared/widgets/asset_card.dart';
import '../../../../shared/widgets/product_card.dart';
import '../../../../shared/widgets/action_card.dart';
import '../../../../shared/widgets/valuation_card.dart';

class WidgetDemoPage extends StatelessWidget {
  const WidgetDemoPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('UI组件演示'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Section: Asset Cards
            _buildSectionTitle(context, 'ASSET_CARD - 资产卡片'),
            AssetCard(
              name: '北京朝阳区公寓',
              value: 5000000,
              assetType: 'real_estate',
              riskLevel: 'low',
              tags: const ['residential', 'beijing', 'prime_location'],
              privacyMode: false,
              onTap: () => _showSnackBar(context, '点击了资产卡片'),
              onEdit: () => _showSnackBar(context, '点击了编辑按钮'),
            ),
            
            AssetCard(
              name: '股票投资组合',
              value: 1200000,
              assetType: 'investment',
              riskLevel: 'high',
              tags: const ['stocks', 'equity', 'growth'],
              privacyMode: false,
              onTap: () => _showSnackBar(context, '点击了投资资产'),
            ),
            
            AssetCard(
              name: '私密资产',
              value: 15000000,
              assetType: 'cash',
              riskLevel: 'low',
              tags: const ['savings', 'emergency_fund'],
              privacyMode: true, // 隐私模式
              onTap: () => _showSnackBar(context, '点击了隐私模式资产'),
            ),
            
            const SizedBox(height: 24),
            
            // Section: Product Cards
            _buildSectionTitle(context, 'PRODUCT_CARD - 产品推荐卡片'),
            ProductCard(
              name: '余额宝',
              provider: '天弘基金',
              category: 'investment',
              description: '低风险货币基金，随存随取，适合作为现金管理工具',
              price: '1元起投',
              roi: '年化收益约2.5%',
              buyNowLink: 'https://www.alipay.com',
              contactInfo: const {
                'phone': '95188',
                'website': 'https://www.alipay.com'
              },
              priority: 'high',
              reason: '基于您的流动性需求分析，推荐此产品提高资金利用效率',
              onTap: () => _showSnackBar(context, '点击了余额宝产品卡片'),
              onContact: () => _showSnackBar(context, '点击了联系咨询'),
            ),
            
            ProductCard(
              name: '平安人寿保险',
              provider: '中国平安',
              category: 'insurance',
              description: '全面的人寿保险保障，覆盖意外、疾病、身故等风险',
              price: '年缴费5000元起',
              roi: '风险保障覆盖',
              contactInfo: const {
                'phone': '95511',
                'website': 'https://www.pingan.com'
              },
              priority: 'medium',
              reason: '基于您的保险缺口分析，建议增加人寿保险保障',
              onTap: () => _showSnackBar(context, '点击了保险产品卡片'),
            ),
            
            ProductCard(
              name: '招商证券投资咨询',
              provider: '招商证券',
              category: 'broker',
              description: '专业的投资顾问服务，提供个性化资产配置建议',
              contactInfo: const {
                'phone': '400-888-8111',
                'website': 'https://www.cmschina.com'
              },
              priority: 'low',
              onTap: () => _showSnackBar(context, '点击了经纪服务卡片'),
            ),
            
            const SizedBox(height: 24),
            
            // Section: Comparison with existing cards
            _buildSectionTitle(context, '现有卡片对比'),
            ActionCard(
              type: ActionCardType.warning,
              title: '流动性风险警告',
              description: '您的现金储备相对较低，建议增加应急资金至6个月支出',
              provider: '系统分析',
              onTap: () => _showSnackBar(context, '点击了ACTION_CARD'),
            ),
            
            ValuationCard(
              propertyName: '北京天通苑',
              estimatedValue: 4500000,
              pricePerSqm: '3.8万/平',
              onConfirm: () => _showSnackBar(context, '确认了房产估值'),
              onEdit: () => _showSnackBar(context, '编辑房产估值'),
            ),
            
            const SizedBox(height: 24),
            
            // Usage instructions
            _buildSectionTitle(context, '使用说明'),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '新增组件特性：',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text('• ASSET_CARD: 支持隐私模式、风险等级标签、资产标签'),
                    const Text('• PRODUCT_CARD: 商业产品推荐、价格ROI信息、购买链接'),
                    const Text('• 优先级显示: 高优先级产品有特殊标识和边框'),
                    const Text('• 交互功能: 点击卡片、联系咨询、立即购买'),
                    const Text('• 推荐原因: 显示AI分析的推荐理由'),
                    const SizedBox(height: 12),
                    Text(
                      '后端集成：',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    const Text('• 支持从WebSocket消息的JSON数据解析'),
                    const Text('• 兼容现有的<WIDGET:TYPE>标签格式'),
                    const Text('• 自动处理数据解析错误，提供降级显示'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12, top: 8),
      child: Text(
        title,
        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  void _showSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        duration: const Duration(seconds: 2),
      ),
    );
  }
}