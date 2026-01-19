# 推荐卡片不显示 - 快速修复指南

## 🔍 问题诊断

从浏览器控制台日志分析：
```
Received WebSocket message: {"type": "chunk", "content": "\\n<WIDGET:ACTION_CARD data=\"{&quot;type":..."}
```

**问题根源**：JSON转义格式不匹配
- 后端发送：`&quot;` (HTML转义)
- 前端解析：只处理了 `&quot;` → `"`，但可能还有其他转义字符

## 🚀 立即修复步骤

### 步骤1: 重新构建前端

```bash
cd frontend
flutter clean
flutter pub get
flutter run -d chrome --hot
```

### 步骤2: 修复JSON解析逻辑

在 `frontend/lib/features/chat/presentation/pages/chat_page.dart` 中找到 `_parseEmbeddedWidgets` 方法，修改JSON解析部分：

**查找这两个位置并修改**：

#### 位置1: ASSET_CARD解析 (约第643行)
```dart
// 原代码
final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';

// 修改为
final jsonStr = match.group(1)
  ?.replaceAll('&quot;', '"')  // HTML转义
  ?.replaceAll('\\&quot;', '"') // 双重转义
  ?.replaceAll('\\"', '"')     // JSON转义
  ?? '{}';
print('🔍 Parsing ASSET_CARD JSON: $jsonStr');
```

#### 位置2: PRODUCT_CARD解析 (约第690行)
```dart
// 原代码  
final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';

// 修改为
final jsonStr = match.group(1)
  ?.replaceAll('&quot;', '"')  // HTML转义
  ?.replaceAll('\\&quot;', '"') // 双重转义
  ?.replaceAll('\\"', '"')     // JSON转义
  ?? '{}';
print('🔍 Parsing PRODUCT_CARD JSON: $jsonStr');
```

### 步骤3: 添加调试日志

在每个 `widgets.add()` 后添加成功日志：

```dart
widgets.add(AssetCard(...));
print('✅ Successfully created ASSET_CARD widget');

widgets.add(ProductCard(...));
print('✅ Successfully created PRODUCT_CARD widget');
```

### 步骤4: 测试验证

1. **重启应用**：
   ```bash
   flutter run -d chrome --hot
   ```

2. **输入测试消息**：
   ```
   我35岁已婚有孩子，月支出2万。在北京有套500万的房子，银行50万现金，买了100万股票基金。帮我分析一下资产配置。
   ```

3. **检查浏览器控制台**：
   - 应该看到 `🔍 Parsing ASSET_CARD JSON: {...}` 日志
   - 应该看到 `✅ Successfully created ASSET_CARD widget` 日志
   - 如果看到解析错误，说明JSON格式仍有问题

## 🔧 高级调试方法

### 方法1: 添加临时测试按钮

在聊天页面添加一个测试按钮来直接测试组件：

```dart
// 在 ChatPage 的 build 方法中添加
FloatingActionButton(
  onPressed: () {
    setState(() {
      _messages.add(ChatMessage(
        text: '测试消息',
        isUser: false,
        timestamp: DateTime.now(),
        embeddedWidgets: [
          AssetCard(
            name: '测试资产',
            value: 1000000,
            assetType: 'real_estate',
            riskLevel: 'low',
            tags: ['test'],
          ),
          ProductCard(
            name: '测试产品',
            provider: '测试服务商',
            category: 'investment',
            description: '测试描述',
            priority: 'high',
          ),
        ],
      ));
    });
  },
  child: Icon(Icons.test_tube),
)
```

### 方法2: 检查组件导入

确认 `chat_page.dart` 顶部有正确的导入：

```dart
import '../../../../shared/widgets/asset_card.dart';
import '../../../../shared/widgets/product_card.dart';
```

### 方法3: 验证组件文件

确认这些文件存在且无语法错误：
- `frontend/lib/shared/widgets/asset_card.dart`
- `frontend/lib/shared/widgets/product_card.dart`

运行语法检查：
```bash
flutter analyze
```

## 📊 预期结果

修复后，用户输入分析请求时应该看到：

1. **ASSET_CARD**：
   - 显示新增资产信息
   - 包含资产价值、类型、风险等级
   - 有编辑和查看按钮

2. **PRODUCT_CARD**：
   - 显示推荐产品信息
   - 包含服务商、价格、收益信息
   - 有"联系咨询"和"立即购买"按钮

3. **PORTFOLIO_CHART**：
   - 显示资产分布饼图
   - 各类资产占比可视化

## 🆘 如果仍然不工作

### 检查清单：

1. **前端是否重新构建**？
   ```bash
   flutter clean && flutter pub get && flutter run
   ```

2. **浏览器控制台是否有错误**？
   - 打开开发者工具 → Console
   - 查看红色错误信息

3. **后端是否正常运行**？
   - 检查后端日志
   - 确认WebSocket连接正常

4. **组件文件是否存在**？
   ```bash
   ls frontend/lib/shared/widgets/asset_card.dart
   ls frontend/lib/shared/widgets/product_card.dart
   ```

5. **依赖是否正确安装**？
   ```bash
   flutter pub deps
   ```

### 最后的解决方案：

如果以上都不工作，可以临时使用简化版本：

```dart
// 在 _parseEmbeddedWidgets 方法开头添加
if (text.contains('<WIDGET:ASSET_CARD') || text.contains('<WIDGET:PRODUCT_CARD')) {
  widgets.add(
    Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Text('🎉 检测到推荐卡片！组件正在加载中...'),
      ),
    ),
  );
}
```

这样至少可以确认检测逻辑是否工作。

## 📞 需要帮助？

如果问题仍然存在，请提供：
1. 浏览器控制台的完整错误日志
2. `flutter doctor` 的输出
3. 当前的 `pubspec.yaml` 内容

这样我们可以进一步诊断问题！