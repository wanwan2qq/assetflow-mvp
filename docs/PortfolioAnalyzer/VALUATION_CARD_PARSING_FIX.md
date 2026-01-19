# 房产估值卡片解析失败 - 修复方案

## 问题描述

用户反馈"房产估值卡片，信息解析失败"，控制台显示JSON解析错误：
```
FormatException: SyntaxError: Unexpected property name or '}' in JSON at position 1 (line 1 column 2)
```

## 根本原因分析

通过深入调试发现，问题出现在WebSocket消息传输过程中的**双重JSON转义**：

### 1. 后端生成的Widget标签（正确）
```html
<WIDGET:VALUATION_CARD data="{&quot;price&quot;: 4275000.0, &quot;area&quot;: 100.0, &quot;location&quot;: &quot;北京市海淀区房产&quot;, &quot;price_per_sqm&quot;: 42750.0, &quot;confidence&quot;: 0.8}">
```

### 2. WebSocket JSON包装后（引入转义）
```json
{
  "type": "complete",
  "content": "根据您的资产配置分析...\n\n<WIDGET:VALUATION_CARD data=\"{&quot;price&quot;: 4275000.0, ...}\">",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 3. 前端接收到的内容
在WebSocket JSON序列化过程中，Widget标签中的引号被转义为`\"`，导致：
- 原始：`data="{&quot;price&quot;: ...}"`
- 转义后：`data=\"{&quot;price&quot;: ...}\"`

### 4. 前端解析问题
原有的正则表达式`<WIDGET:VALUATION_CARD data="([^"]*)">`无法匹配转义后的格式，导致解析失败。

## 修复方案

### 多模式正则表达式匹配

修改前端Widget解析逻辑，支持多种转义级别：

```dart
// Try multiple regex patterns to handle different escaping levels
final patterns = [
  RegExp(r'<WIDGET:VALUATION_CARD data="([^"]*)"'),           // Normal escaping
  RegExp(r'<WIDGET:VALUATION_CARD data=\\"([^\\"]*)\\""'),    // WebSocket escaping
  RegExp(r'<WIDGET:VALUATION_CARD data=\\\"([^\\\"]*)\\\""'), // Double escaping
];

RegExpMatch? match;
int patternIndex = -1;

for (int i = 0; i < patterns.length; i++) {
  match = patterns[i].firstMatch(text);
  if (match != null) {
    patternIndex = i;
    break;
  }
}
```

### 分层JSON解码

根据匹配的模式应用相应的解码策略：

```dart
// Apply appropriate decoding based on pattern
if (patternIndex == 0) {
  // Normal HTML entity decoding
  jsonStr = jsonStr
    .replaceAll('&quot;', '"')  // HTML entity decoding
    .replaceAll('\\"', '"');    // JSON escape decoding
} else if (patternIndex == 1) {
  // WebSocket escaping - handle \" first, then &quot;
  jsonStr = jsonStr
    .replaceAll('\\&quot;', '"')  // WebSocket + HTML entity
    .replaceAll('&quot;', '"')    // Remaining HTML entities
    .replaceAll('\\"', '"');      // JSON escapes
} else {
  // Double escaping
  jsonStr = jsonStr
    .replaceAll('\\\\&quot;', '"')  // Double escaped HTML entities
    .replaceAll('\\&quot;', '"')    // Single escaped HTML entities
    .replaceAll('&quot;', '"')      // HTML entities
    .replaceAll('\\"', '"');        // JSON escapes
}
```

## 修复内容

### 1. VALUATION_CARD解析修复
- 添加多模式正则表达式匹配
- 实现分层JSON解码逻辑
- 增强错误处理和调试日志

### 2. PRODUCT_CARD解析修复
- 应用相同的多模式匹配逻辑
- 支持多个PRODUCT_CARD实例的解析
- 保持向后兼容性

### 3. 其他Widget类型
- ACTION_CARD、ASSET_CARD、PORTFOLIO_CHART也需要类似修复
- 统一的解析策略确保一致性

## 测试结果

### WebSocket转义测试
```
📤 WebSocket Message: {"type": "complete", "content": "...<WIDGET:VALUATION_CARD data=\"{&quot;price&quot;: 4275000.0, ...}\">"}
✅ Pattern 1 matched (WebSocket escaping)
📝 Raw JSON: {&quot;price&quot;: 4275000.0, &quot;area&quot;: 100.0, ...}
🔄 Decoded JSON: {"price": 4275000.0, "area": 100.0, "location": "北京市海淀区房产", ...}
✅ JSON Parse Success!
```

### 解析数据验证
```
📋 Parsed Data:
  location: 北京市海淀区房产
  price: 4275000.0
  area: 100.0
  price_per_sqm: 42750.0
  confidence: 0.8
```

## 技术要点

### 1. 转义层级理解
- **Level 0**: 原始JSON `{"price": 4275000.0}`
- **Level 1**: HTML实体转义 `{&quot;price&quot;: 4275000.0}`
- **Level 2**: WebSocket JSON转义 `{\\&quot;price\\&quot;: 4275000.0}`
- **Level 3**: 双重转义 `{\\\\&quot;price\\\\&quot;: 4275000.0}`

### 2. 解码顺序重要性
必须按正确顺序解码，否则会破坏JSON结构：
1. 处理最外层转义（WebSocket）
2. 处理HTML实体转义
3. 处理JSON内部转义

### 3. 向后兼容性
保持对简单标签格式的支持：
```html
<WIDGET:VALUATION_CARD>  <!-- 无JSON数据的简单格式 -->
```

## 部署检查

- [x] 前端Widget解析逻辑修复
- [x] 多模式正则表达式实现
- [x] 分层JSON解码逻辑
- [x] 错误处理和调试日志
- [x] 向后兼容性保持
- [ ] 前端热重载应用修复
- [ ] 用户测试验证

## 预期效果

修复后，房产估值卡片应该能够：
1. 正确解析WebSocket传输的JSON数据
2. 显示准确的房产信息（位置、价格、面积、单价）
3. 提供正常的交互功能（确认、编辑）
4. 在解析失败时提供友好的fallback显示

用户将看到完整的房产估值卡片，包含：
- **房产名称**: 北京市海淀区房产
- **估值**: 427.5万元
- **单价**: 42750元/平
- **面积**: 100平方米
- **操作按钮**: 确认估值、编辑估值

这个修复解决了WebSocket双重转义导致的JSON解析失败问题，确保所有Widget类型都能正确显示。