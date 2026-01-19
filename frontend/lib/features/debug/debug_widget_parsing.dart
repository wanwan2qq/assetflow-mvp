import 'dart:convert';
import 'package:flutter/material.dart';
import '../../core/models/chat_history.dart';
import '../../shared/widgets/asset_card.dart';
import '../../shared/widgets/product_card.dart';
import '../../shared/widgets/action_card.dart';

class DebugWidgetParsing extends StatelessWidget {
  const DebugWidgetParsing({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Widget解析调试'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSection(context, '测试ASSET_CARD解析'),
            _testAssetCardParsing(),
            
            const SizedBox(height: 24),
            
            _buildSection(context, '测试PRODUCT_CARD解析'),
            _testProductCardParsing(),
            
            const SizedBox(height: 24),
            
            _buildSection(context, '测试WebSocket消息解析'),
            _testWebSocketMessageParsing(context),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(BuildContext context, String title) {
    return Text(
      title,
      style: Theme.of(context).textTheme.headlineSmall?.copyWith(
        fontWeight: FontWeight.bold,
        color: Theme.of(context).colorScheme.primary,
      ),
    );
  }

  Widget _testAssetCardParsing() {
    // 模拟后端返回的ASSET_CARD数据
    final testData = {
      'name': '北京朝阳区公寓',
      'value': 5000000.0,
      'type': 'real_estate',
      'risk_level': 'low',
      'tags': ['residential', 'beijing'],
      'privacy_mode': false,
    };

    return Column(
      children: [
        const Text('原始数据:'),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            json.encode(testData),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          ),
        ),
        const SizedBox(height: 8),
        const Text('渲染结果:'),
        AssetCard(
          name: testData['name'] as String,
          value: testData['value'] as double,
          assetType: testData['type'] as String,
          riskLevel: testData['risk_level'] as String?,
          tags: (testData['tags'] as List<dynamic>).cast<String>(),
          privacyMode: testData['privacy_mode'] as bool,
          onTap: () => print('AssetCard tapped'),
        ),
      ],
    );
  }

  Widget _testProductCardParsing() {
    // 模拟后端返回的PRODUCT_CARD数据
    final testData = {
      'name': '余额宝',
      'provider': '天弘基金',
      'category': 'investment',
      'description': '低风险货币基金，随存随取',
      'price': '1元起投',
      'roi': '年化收益约2.5%',
      'buy_now_link': 'https://www.alipay.com',
      'contact_info': {
        'phone': '95188',
        'website': 'https://www.alipay.com'
      },
      'priority': 'high',
      'reason': '基于您的流动性需求分析',
    };

    return Column(
      children: [
        const Text('原始数据:'),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            json.encode(testData),
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          ),
        ),
        const SizedBox(height: 8),
        const Text('渲染结果:'),
        ProductCard(
          name: testData['name'] as String,
          provider: testData['provider'] as String,
          category: testData['category'] as String,
          description: testData['description'] as String,
          price: testData['price'] as String?,
          roi: testData['roi'] as String?,
          buyNowLink: testData['buy_now_link'] as String?,
          contactInfo: testData['contact_info'] as Map<String, dynamic>?,
          priority: testData['priority'] as String,
          reason: testData['reason'] as String?,
          onTap: () => print('ProductCard tapped'),
        ),
      ],
    );
  }

  Widget _testWebSocketMessageParsing(BuildContext context) {
    // 模拟从WebSocket接收到的消息格式
    final testMessage = '''
基于您的投资组合分析，我发现了一些需要关注的风险点。

<WIDGET:ASSET_CARD data="{\\"name\\": \\"新增保险\\", \\"value\\": 100000.0, \\"type\\": \\"insurance\\", \\"risk_level\\": \\"low\\", \\"tags\\": [\\"life_insurance\\", \\"protection\\"], \\"privacy_mode\\": false}">

<WIDGET:PRODUCT_CARD data="{\\"name\\": \\"余额宝\\", \\"provider\\": \\"天弘基金\\", \\"category\\": \\"investment\\", \\"description\\": \\"低风险货币基金\\", \\"price\\": \\"1元起投\\", \\"roi\\": \\"年化收益约2.5%\\", \\"priority\\": \\"high\\"}">
''';

    final parsedWidgets = _parseEmbeddedWidgets(testMessage);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('WebSocket消息:'),
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.grey[100],
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(
            testMessage,
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          ),
        ),
        const SizedBox(height: 8),
        Text('解析到 ${parsedWidgets?.length ?? 0} 个组件:'),
        if (parsedWidgets != null) ...parsedWidgets,
        if (parsedWidgets == null || parsedWidgets.isEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.red[50],
              border: Border.all(color: Colors.red[200]!),
              borderRadius: BorderRadius.circular(4),
            ),
            child: const Text(
              '❌ 没有解析到任何组件！这可能是问题所在。',
              style: TextStyle(color: Colors.red),
            ),
          ),
      ],
    );
  }

  List<Widget>? _parseEmbeddedWidgets(String text) {
    final widgets = <Widget>[];
    
    // Parse ASSET_CARD with JSON data
    if (text.contains('<WIDGET:ASSET_CARD')) {
      final match = RegExp(r'<WIDGET:ASSET_CARD data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)?.replaceAll('\\"', '"') ?? '{}';
          print('Parsing ASSET_CARD JSON: $jsonStr');
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          widgets.add(
            AssetCard(
              name: data['name'] as String? ?? '未知资产',
              value: (data['value'] as num?)?.toDouble() ?? 0,
              assetType: data['type'] as String? ?? 'unknown',
              riskLevel: data['risk_level'] as String?,
              tags: (data['tags'] as List<dynamic>?)?.cast<String>() ?? [],
              privacyMode: data['privacy_mode'] as bool? ?? false,
              onTap: () => print('Debug AssetCard tapped'),
            ),
          );
        } catch (e) {
          print('Error parsing ASSET_CARD data: $e');
          widgets.add(
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.red[100],
              child: Text('ASSET_CARD解析错误: $e'),
            ),
          );
        }
      }
    }

    // Parse PRODUCT_CARD with JSON data
    if (text.contains('<WIDGET:PRODUCT_CARD')) {
      final match = RegExp(r'<WIDGET:PRODUCT_CARD data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)?.replaceAll('\\"', '"') ?? '{}';
          print('Parsing PRODUCT_CARD JSON: $jsonStr');
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          widgets.add(
            ProductCard(
              name: data['name'] as String? ?? '推荐产品',
              provider: data['provider'] as String? ?? '未知服务商',
              category: data['category'] as String? ?? 'general',
              description: data['description'] as String? ?? '',
              price: data['price'] as String?,
              roi: data['roi'] as String?,
              buyNowLink: data['buy_now_link'] as String?,
              contactInfo: data['contact_info'] as Map<String, dynamic>?,
              priority: data['priority'] as String? ?? 'medium',
              reason: data['reason'] as String?,
              onTap: () => print('Debug ProductCard tapped'),
            ),
          );
        } catch (e) {
          print('Error parsing PRODUCT_CARD data: $e');
          widgets.add(
            Container(
              padding: const EdgeInsets.all(8),
              color: Colors.red[100],
              child: Text('PRODUCT_CARD解析错误: $e'),
            ),
          );
        }
      }
    }
    
    return widgets.isNotEmpty ? widgets : null;
  }
}