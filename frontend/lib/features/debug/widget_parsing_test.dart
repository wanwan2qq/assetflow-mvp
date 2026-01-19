import 'dart:convert';
import 'package:flutter/material.dart';

class WidgetParsingTest extends StatefulWidget {
  const WidgetParsingTest({super.key});

  @override
  State<WidgetParsingTest> createState() => _WidgetParsingTestState();
}

class _WidgetParsingTestState extends State<WidgetParsingTest> {
  String testMessage = '';
  List<Widget> parsedWidgets = [];
  String debugLog = '';

  @override
  void initState() {
    super.initState();
    // 使用从控制台看到的实际消息格式
    testMessage = '''
我先帮您做新一下资产分析。刚才我查了一下武汉黄鹤花园的市场价，153平米的参考价大约是654万左右，比您之前提到的140万要高不少，这个差异会影响整体资产配置，我们先以市场价为准进行分析。

<WIDGET:VALUATION_CARD data="{&quot;price&quot;:6000000.0, &quot;area&quot;:153.0, &quot;location&quot;:&quot;武汉黄鹤花园&quot;, &quot;price_per_sqm&quot;:39215.686274509804, &quot;confidence&quot;:0.8}">
''';
    _parseMessage();
  }

  void _parseMessage() {
    setState(() {
      debugLog = '';
      parsedWidgets.clear();
      
      debugLog += '🔍 开始解析消息...\n';
      debugLog += '消息内容: ${testMessage.substring(0, 100)}...\n\n';
      
      // 检查是否包含WIDGET标签
      if (testMessage.contains('<WIDGET:')) {
        debugLog += '✅ 发现WIDGET标签\n';
        
        // 查找VALUATION_CARD
        if (testMessage.contains('<WIDGET:VALUATION_CARD')) {
          debugLog += '✅ 发现VALUATION_CARD\n';
          
          final match = RegExp(r'<WIDGET:VALUATION_CARD data="([^"]*)"').firstMatch(testMessage);
          if (match != null) {
            debugLog += '✅ 正则匹配成功\n';
            
            try {
              final rawJson = match.group(1) ?? '{}';
              debugLog += '原始JSON: $rawJson\n';
              
              final jsonStr = rawJson
                .replaceAll('&quot;', '"')
                .replaceAll('\\&quot;', '"')
                .replaceAll('\\"', '"');
              debugLog += '处理后JSON: $jsonStr\n';
              
              final data = json.decode(jsonStr) as Map<String, dynamic>;
              debugLog += '✅ JSON解析成功: $data\n';
              
              // 创建卡片
              final card = Card(
                margin: const EdgeInsets.all(8),
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('房产估值卡片', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
                      SizedBox(height: 8),
                      Text('位置: ${data['location'] ?? '未知'}'),
                      Text('面积: ${data['area'] ?? 0} 平米'),
                      Text('估值: ¥${((data['price'] as num?) ?? 0) / 10000}万'),
                      Text('单价: ¥${((data['price_per_sqm'] as num?) ?? 0).toStringAsFixed(0)}/平米'),
                      Text('置信度: ${((data['confidence'] as num?) ?? 0) * 100}%'),
                    ],
                  ),
                ),
              );
              
              parsedWidgets.add(card);
              debugLog += '✅ 卡片创建成功\n';
              
            } catch (e) {
              debugLog += '❌ JSON解析失败: $e\n';
            }
          } else {
            debugLog += '❌ 正则匹配失败\n';
          }
        } else {
          debugLog += '❌ 未发现VALUATION_CARD\n';
        }
        
        // 检查其他WIDGET类型
        if (testMessage.contains('<WIDGET:ASSET_CARD')) {
          debugLog += '✅ 发现ASSET_CARD\n';
        }
        if (testMessage.contains('<WIDGET:PRODUCT_CARD')) {
          debugLog += '✅ 发现PRODUCT_CARD\n';
        }
        
      } else {
        debugLog += '❌ 未发现任何WIDGET标签\n';
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Widget解析测试'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _parseMessage,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '调试日志:',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Text(
                debugLog,
                style: const TextStyle(
                  fontFamily: 'monospace',
                  fontSize: 12,
                ),
              ),
            ),
            
            const SizedBox(height: 24),
            
            Text(
              '解析结果 (${parsedWidgets.length} 个组件):',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            
            if (parsedWidgets.isEmpty)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.red[50],
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.red[200]!),
                ),
                child: const Text(
                  '❌ 没有解析到任何组件',
                  style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
                ),
              )
            else
              ...parsedWidgets,
              
            const SizedBox(height: 24),
            
            Text(
              '原始消息:',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.blue[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.blue[200]!),
              ),
              child: Text(
                testMessage,
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}