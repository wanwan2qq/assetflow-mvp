# 前端准备工作清单 - 显示推荐卡片

## 📋 概述

为了在前端聊天页面显示新的 `ASSET_CARD` 和 `PRODUCT_CARD` 推荐卡片，需要完成以下准备工作。

## 🎯 当前状态分析

### ✅ 已有功能
- **Widget解析系统**：支持从文本标签和meta_data解析UI组件
- **现有卡片**：`VALUATION_CARD`, `ACTION_CARD`, `PORTFOLIO_CHART`
- **渲染架构**：ChatMessage → embeddedWidgets → ChatBubble渲染
- **数据流**：WebSocket → 消息解析 → Widget生成 → UI显示

### ❌ 缺失功能
- **ASSET_CARD**：新的资产卡片组件
- **PRODUCT_CARD**：商业产品推荐卡片组件
- **数据解析**：新卡片类型的数据解析逻辑
- **交互回调**：商业化操作（立即购买、联系等）

## 🚀 必需的准备工作

### 1. 创建新的Widget组件

#### A. AssetCard Widget (`frontend/lib/shared/widgets/asset_card.dart`)

```dart
import 'package:flutter/material.dart';

class AssetCard extends StatelessWidget {
  final String name;
  final double value;
  final String assetType;
  final String? riskLevel;
  final List<String> tags;
  final bool privacyMode;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;

  const AssetCard({
    super.key,
    required this.name,
    required this.value,
    required this.assetType,
    this.riskLevel,
    this.tags = const [],
    this.privacyMode = false,
    this.onTap,
    this.onEdit,
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
              // Header with asset icon and name
              Row(
                children: [
                  Icon(
                    _getAssetIcon(),
                    color: _getAssetColor(),
                    size: 24,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      name,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                  if (onEdit != null)
                    IconButton(
                      icon: const Icon(Icons.edit, size: 20),
                      onPressed: onEdit,
                    ),
                ],
              ),
              const SizedBox(height: 12),
              
              // Value display (with privacy mode support)
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        '资产价值',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Colors.grey[600],
                        ),
                      ),
                      Text(
                        _formatValue(),
                        style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                          color: Colors.green[700],
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  if (riskLevel != null)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: _getRiskColor().withOpacity(0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: _getRiskColor().withOpacity(0.3)),
                      ),
                      child: Text(
                        _getRiskLabel(),
                        style: TextStyle(
                          color: _getRiskColor(),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                ],
              ),
              
              // Tags
              if (tags.isNotEmpty) ...[
                const SizedBox(height: 12),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: tags.map((tag) => Chip(
                    label: Text(
                      tag,
                      style: const TextStyle(fontSize: 11),
                    ),
                    backgroundColor: Colors.grey[100],
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                  )).toList(),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  IconData _getAssetIcon() {
    switch (assetType.toLowerCase()) {
      case 'real_estate':
        return Icons.home;
      case 'cash':
        return Icons.account_balance_wallet;
      case 'investment':
        return Icons.trending_up;
      case 'insurance':
        return Icons.security;
      case 'liability':
        return Icons.credit_card;
      default:
        return Icons.account_balance;
    }
  }

  Color _getAssetColor() {
    switch (assetType.toLowerCase()) {
      case 'real_estate':
        return Colors.blue;
      case 'cash':
        return Colors.green;
      case 'investment':
        return Colors.orange;
      case 'insurance':
        return Colors.purple;
      case 'liability':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _formatValue() {
    if (privacyMode) {
      if (value >= 10000000) return '1000万+';
      if (value >= 1000000) return '100万+';
      if (value >= 100000) return '10万+';
      return '***';
    }
    
    if (value >= 10000) {
      return '¥${(value / 10000).toStringAsFixed(1)}万';
    }
    return '¥${value.toStringAsFixed(0)}';
  }

  Color _getRiskColor() {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return Colors.green;
      case 'medium':
        return Colors.orange;
      case 'high':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _getRiskLabel() {
    switch (riskLevel?.toLowerCase()) {
      case 'low':
        return '低风险';
      case 'medium':
        return '中风险';
      case 'high':
        return '高风险';
      default:
        return '未知';
    }
  }
}
```

#### B. ProductCard Widget (`frontend/lib/shared/widgets/product_card.dart`)

```dart
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
```

### 2. 更新Widget解析逻辑

#### 修改 `chat_page.dart` 中的解析方法

在 `_parseWidgetsFromMetaData` 方法中添加新的case：

```dart
// 在现有的 switch 语句中添加
case 'ASSET_CARD':
  final data = widgetData.data;
  widgets.add(
    AssetCard(
      name: data['name'] as String? ?? '未知资产',
      value: (data['value'] as num?)?.toDouble() ?? 0,
      assetType: data['type'] as String? ?? 'unknown',
      riskLevel: data['risk_level'] as String?,
      tags: (data['tags'] as List<dynamic>?)?.cast<String>() ?? [],
      privacyMode: data['privacy_mode'] as bool? ?? false,
      onTap: () {
        _sendMessage('告诉我更多关于${data['name'] ?? '这个资产'}的信息');
      },
      onEdit: () {
        _sendMessage('我想修改${data['name'] ?? '这个资产'}的信息');
      },
    ),
  );
  break;

case 'PRODUCT_CARD':
  final data = widgetData.data;
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
      onTap: () {
        _sendMessage('我对${data['name'] ?? '这个产品'}感兴趣，请提供更多信息');
      },
      onContact: () {
        _sendMessage('我想联系${data['provider'] ?? '服务商'}咨询${data['name'] ?? '这个产品'}');
      },
    ),
  );
  break;
```

同时在 `_parseEmbeddedWidgets` 方法中添加对应的文本标签解析：

```dart
// 添加到现有的 if 语句中
if (text.contains('<WIDGET:ASSET_CARD')) {
  // 解析 data 属性中的JSON数据
  final match = RegExp(r'<WIDGET:ASSET_CARD data="([^"]*)"').firstMatch(text);
  if (match != null) {
    try {
      final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';
      final data = json.decode(jsonStr) as Map<String, dynamic>;
      
      widgets.add(
        AssetCard(
          name: data['name'] as String? ?? '未知资产',
          value: (data['value'] as num?)?.toDouble() ?? 0,
          assetType: data['type'] as String? ?? 'unknown',
          riskLevel: data['risk_level'] as String?,
          tags: (data['tags'] as List<dynamic>?)?.cast<String>() ?? [],
          privacyMode: data['privacy_mode'] as bool? ?? false,
          onTap: () {
            _sendMessage('告诉我更多关于${data['name'] ?? '这个资产'}的信息');
          },
        ),
      );
    } catch (e) {
      print('Error parsing ASSET_CARD data: $e');
    }
  }
}

if (text.contains('<WIDGET:PRODUCT_CARD')) {
  final match = RegExp(r'<WIDGET:PRODUCT_CARD data="([^"]*)"').firstMatch(text);
  if (match != null) {
    try {
      final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';
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
          onTap: () {
            _sendMessage('我对${data['name'] ?? '这个产品'}感兴趣');
          },
        ),
      );
    } catch (e) {
      print('Error parsing PRODUCT_CARD data: $e');
    }
  }
}
```

### 3. 添加依赖包

在 `pubspec.yaml` 中添加URL启动器：

```yaml
dependencies:
  url_launcher: ^6.2.2
```

### 4. 更新导入语句

在 `chat_page.dart` 顶部添加：

```dart
import '../../../../shared/widgets/asset_card.dart';
import '../../../../shared/widgets/product_card.dart';
```

### 5. 测试数据验证

创建测试脚本验证Widget渲染：

```dart
// 在 frontend/test/widget_test.dart 中添加
testWidgets('AssetCard displays correctly', (WidgetTester tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: AssetCard(
          name: '北京朝阳区公寓',
          value: 5000000,
          assetType: 'real_estate',
          riskLevel: 'low',
          tags: ['residential', 'beijing'],
          privacyMode: false,
        ),
      ),
    ),
  );

  expect(find.text('北京朝阳区公寓'), findsOneWidget);
  expect(find.text('¥500.0万'), findsOneWidget);
  expect(find.text('低风险'), findsOneWidget);
});

testWidgets('ProductCard displays correctly', (WidgetTester tester) async {
  await tester.pumpWidget(
    MaterialApp(
      home: Scaffold(
        body: ProductCard(
          name: '余额宝',
          provider: '天弘基金',
          category: 'investment',
          description: '低风险货币基金',
          price: '1元起投',
          roi: '年化收益约2.5%',
          priority: 'high',
        ),
      ),
    ),
  );

  expect(find.text('余额宝'), findsOneWidget);
  expect(find.text('天弘基金'), findsOneWidget);
  expect(find.text('推荐'), findsOneWidget);
});
```

## 🔄 部署步骤

### 步骤1：创建Widget文件
1. 创建 `frontend/lib/shared/widgets/asset_card.dart`
2. 创建 `frontend/lib/shared/widgets/product_card.dart`

### 步骤2：更新解析逻辑
1. 修改 `frontend/lib/features/chat/presentation/pages/chat_page.dart`
2. 添加新的case到 `_parseWidgetsFromMetaData` 和 `_parseEmbeddedWidgets`

### 步骤3：添加依赖
1. 更新 `pubspec.yaml`
2. 运行 `flutter pub get`

### 步骤4：测试验证
1. 运行单元测试
2. 在聊天界面测试新卡片显示

## 📊 预期效果

完成后，用户将在聊天界面看到：

1. **ASSET_CARD**：
   - 显示资产名称、价值、类型
   - 风险等级标签（低/中/高风险）
   - 资产标签（如residential, beijing）
   - 支持隐私模式（遮蔽确切数值）

2. **PRODUCT_CARD**：
   - 显示产品名称、服务商
   - 产品描述和推荐原因
   - 价格和预期收益信息
   - "联系咨询"和"立即购买"按钮
   - 高优先级产品的特殊标识

3. **交互功能**：
   - 点击卡片发送相关询问消息
   - 联系按钮拨打电话
   - 购买按钮打开网页链接

## 🎯 商业化价值

- **用户体验**：丰富的视觉展示和直观的操作界面
- **转化率**：直接的购买和联系入口
- **个性化**：基于用户风险分析的精准推荐
- **信任度**：专业的产品展示和服务商信息

完成这些准备工作后，前端就能完美显示后端生成的推荐卡片，实现完整的商业化闭环！