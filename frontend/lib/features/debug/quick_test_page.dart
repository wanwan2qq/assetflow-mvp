import 'dart:convert';
import 'package:flutter/material.dart';
import '../../shared/widgets/valuation_card.dart';
import '../../shared/widgets/asset_card.dart';
import '../../shared/widgets/product_card.dart';

class QuickTestPage extends StatelessWidget {
  const QuickTestPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('快速测试页面'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '测试新组件是否正常工作:',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 16),
            
            // 测试 VALUATION_CARD
            const Text('1. VALUATION_CARD 测试:'),
            ValuationCard(
              propertyName: '武汉黄鹤花园',
              estimatedValue: 6000000,
              pricePerSqm: '39216元/平',
              onConfirm: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('确认估值按钮点击')),
                );
              },
              onEdit: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('编辑估值按钮点击')),
                );
              },
            ),
            
            const SizedBox(height: 16),
            
            // 测试 ASSET_CARD
            const Text('2. ASSET_CARD 测试:'),
            AssetCard(
              name: '北京朝阳区公寓',
              value: 5000000,
              assetType: 'real_estate',
              riskLevel: 'low',
              tags: const ['residential', 'beijing'],
              privacyMode: false,
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('资产卡片点击')),
                );
              },
            ),
            
            const SizedBox(height: 16),
            
            // 测试 PRODUCT_CARD
            const Text('3. PRODUCT_CARD 测试:'),
            ProductCard(
              name: '余额宝',
              provider: '天弘基金',
              category: 'investment',
              description: '低风险货币基金，随存随取',
              price: '1元起投',
              roi: '年化收益约2.5%',
              priority: 'high',
              reason: '基于您的流动性需求分析',
              onTap: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('产品卡片点击')),
                );
              },
            ),
            
            const SizedBox(height: 24),
            
            // 测试解析逻辑
            const Text('4. 解析逻辑测试:'),
            ElevatedButton(
              onPressed: () => _testParsing(context),
              child: const Text('测试消息解析'),
            ),
          ],
        ),
      ),
    );
  }

  void _testParsing(BuildContext context) {
    // 模拟从控制台看到的实际消息
    const testMessage = '''
我先帮您做新一下资产分析。刚才我查了一下武汉黄鹤花园的市场价，153平米的参考价大约是654万左右。

<WIDGET:VALUATION_CARD data="{&quot;price&quot;:6000000.0, &quot;area&quot;:153.0, &quot;location&quot;:&quot;武汉黄鹤花园&quot;, &quot;price_per_sqm&quot;:39215.686274509804, &quot;confidence&quot;:0.8}">
''';

    print('🔍 测试消息解析...');
    print('消息内容: $testMessage');
    
    final widgets = _parseEmbeddedWidgets(testMessage);
    
    if (widgets != null && widgets.isNotEmpty) {
      print('✅ 解析成功，找到 ${widgets.length} 个组件');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('✅ 解析成功，找到 ${widgets.length} 个组件')),
      );
    } else {
      print('❌ 解析失败，没有找到组件');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('❌ 解析失败，没有找到组件'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  List<Widget>? _parseEmbeddedWidgets(String text) {
    final widgets = <Widget>[];
    
    // Parse VALUATION_CARD with JSON data
    if (text.contains('<WIDGET:VALUATION_CARD')) {
      final match = RegExp(r'<WIDGET:VALUATION_CARD data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)
            ?.replaceAll('&quot;', '"')  // HTML转义
            ?.replaceAll('\\"', '"')     // JSON转义
            ?? '{}';
          print('🔍 Parsing VALUATION_CARD JSON: $jsonStr');
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          widgets.add(
            ValuationCard(
              propertyName: data['location'] as String? ?? '房产',
              estimatedValue: (data['price'] as num?)?.toDouble() ?? 0,
              pricePerSqm: '${((data['price_per_sqm'] as num?) ?? 0).toStringAsFixed(0)}元/平',
              onConfirm: () => print('确认估值'),
              onEdit: () => print('编辑估值'),
            ),
          );
          print('✅ Successfully created VALUATION_CARD widget');
        } catch (e) {
          print('❌ Error parsing VALUATION_CARD data: $e');
        }
      }
    }
    
    return widgets.isNotEmpty ? widgets : null;
  }
}