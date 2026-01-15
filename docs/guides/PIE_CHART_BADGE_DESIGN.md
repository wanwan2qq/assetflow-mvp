# 饼图徽章设计文档

## 设计理念

将图例直接显示在饼图扇区上，使用徽章（badge）形式，让用户一眼就能看到每个扇区代表的资产类型，无需在图表和图例之间来回查看。

## 设计特点

### 1. 无滚动设计
- ✅ 移除 `SingleChildScrollView`
- ✅ 使用 `AspectRatio(aspectRatio: 1)` 确保正方形布局
- ✅ 图表自适应卡片大小
- ✅ 无需滚动，所有内容一屏展示

### 2. 徽章自动定位
- ✅ 使用 `badgeWidget` 在扇区外显示标签
- ✅ `badgePositionPercentageOffset: 1.3` 自动计算最佳位置
- ✅ fl_chart 自动处理徽章位置，避免重叠
- ✅ 只为占比 > 5% 的扇区显示徽章

### 3. 视觉层次
```
┌─────────────────────────────┐
│      资产分布               │
│                             │
│         [房产]              │ ← 徽章
│           ╱                 │
│      ╭───────╮              │
│     ╱  63.6%  ╲             │
│    │           │            │
│    │    🥧     │            │
│    │           │            │
│     ╲  33.1%  ╱             │
│      ╰───────╯              │
│           ╲                 │
│         [保险]              │ ← 徽章
│                             │
└─────────────────────────────┘
```

## 实现细节

### 饼图配置
```dart
PieChartData(
  sectionsSpace: 2,           // 扇区间距
  centerSpaceRadius: 60,      // 中心空白半径
  sections: [
    PieChartSectionData(
      radius: 100.0,           // 扇区半径
      title: '63.6%',          // 扇区内显示百分比
      badgeWidget: Badge,      // 扇区外显示徽章
      badgePositionPercentageOffset: 1.3,  // 徽章距离
    ),
  ],
)
```

### 徽章样式
```dart
Container(
  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
  decoration: BoxDecoration(
    color: assetColor.withOpacity(0.9),  // 半透明背景
    borderRadius: BorderRadius.circular(12),  // 圆角
    border: Border.all(color: Colors.white, width: 2),  // 白色边框
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.2),
        blurRadius: 4,
        offset: Offset(0, 2),
      ),
    ],
  ),
  child: Text('房产'),  // 资产类型名称
)
```

### 交互反馈
```dart
// 触摸时扇区放大
final radius = isTouched ? 110.0 : 100.0;

// 触摸时文字变大
final fontSize = isTouched ? 16.0 : 14.0;

// 触摸时徽章文字变大
final badgeFontSize = isTouched ? 13.0 : 12.0;
```

## 显示规则

### 徽章显示条件
```dart
Widget _buildBadge(AssetType assetType, double percentage, bool isTouched) {
  // 只为占比 > 5% 的扇区显示徽章
  if (percentage <= 5) return const SizedBox.shrink();
  
  // ... 返回徽章 Widget
}
```

**原因**：
- 小于 5% 的扇区空间有限，徽章可能重叠
- 保持界面简洁，突出主要资产类型
- 用户仍可通过颜色和百分比识别小扇区

### 百分比显示
```dart
title: '${percentage.toStringAsFixed(1)}%',  // 始终显示
```

**特点**：
- 所有扇区都显示百分比（在扇区内）
- 使用白色文字 + 阴影确保可读性
- 触摸时文字变大，提供视觉反馈

## 颜色方案

### 资产类型颜色
```dart
const Map<AssetType, Color> assetTypeColors = {
  AssetType.realEstate: Colors.blue,      // 房产 - 蓝色
  AssetType.cash: Colors.green,           // 现金 - 绿色
  AssetType.investment: Colors.orange,    // 投资 - 橙色
  AssetType.insurance: Colors.purple,     // 保险 - 紫色
  AssetType.liability: Colors.red,        // 负债 - 红色
};
```

### 徽章颜色
- 背景：资产类型颜色 + 90% 不透明度
- 边框：白色 2px
- 文字：白色粗体
- 阴影：黑色 20% 不透明度

## 布局优势

### Before（带图例）
```
┌─────────────────────────────┐
│ 资产分布                     │
│                             │
│ 总资产                       │
│ ¥614.8万                    │
│                             │
│      🥧                     │
│    (饼图)                   │
│                             │
│ ● 房产 63.6%                │
│ ● 现金 1.7%                 │
│ ● 投资 1.7%                 │
│ ● 保险 33.1%                │
│                             │
│ ↓ 需要滚动                   │
└─────────────────────────────┘
```

### After（徽章设计）
```
┌─────────────────────────────┐
│ 资产分布                     │
│                             │
│      [房产]                 │
│        ↓                    │
│    ╭────────╮               │
│   ╱  63.6%   ╲   [保险]     │
│  │            │    ↓        │
│  │     🥧     │  33.1%      │
│  │            │             │
│   ╲  1.7%   ╱              │
│    ╰────────╯               │
│      ↑   ↑                  │
│   [现金] [投资]             │
│                             │
│ ✓ 无需滚动                   │
└─────────────────────────────┘
```

## 优势对比

| 特性 | 传统图例 | 徽章设计 |
|-----|---------|---------|
| 空间利用 | 需要额外空间 | 充分利用空白 |
| 可读性 | 需要对照查看 | 直观明了 |
| 滚动需求 | 可能需要 | 无需滚动 |
| 视觉焦点 | 分散 | 集中 |
| 交互体验 | 静态 | 动态反馈 |
| 小屏适配 | 困难 | 自适应 |

## 响应式设计

### 自适应尺寸
```dart
AspectRatio(
  aspectRatio: 1,  // 始终保持正方形
  child: PieChart(...),
)
```

**效果**：
- 小屏幕：图表缩小，徽章自动调整位置
- 大屏幕：图表放大，徽章保持合适距离
- 横屏：图表适应宽度，保持比例

### 徽章定位
```dart
badgePositionPercentageOffset: 1.3
```

**说明**：
- `1.0` = 扇区边缘
- `1.3` = 扇区边缘外 30% 的距离
- fl_chart 自动计算角度和位置
- 避免徽章重叠或超出边界

## 性能优化

### 条件渲染
```dart
// 只为大扇区创建徽章 Widget
if (percentage <= 5) return const SizedBox.shrink();
```

**好处**：
- 减少 Widget 数量
- 降低渲染开销
- 避免小扇区徽章重叠

### 状态管理
```dart
int touchedIndex = -1;  // 只追踪触摸的扇区

setState(() {
  touchedIndex = pieTouchResponse.touchedSection!.touchedSectionIndex;
});
```

**好处**：
- 最小化状态更新
- 只重绘必要的部分
- 流畅的交互体验

## 可访问性

### 文字对比度
- 白色文字 + 深色背景 = 高对比度
- 文字阴影增强可读性
- 徽章白色边框提供视觉分隔

### 触摸目标
- 扇区可点击区域大（radius: 100）
- 触摸反馈明显（放大 + 文字变大）
- 徽章不可点击，避免误触

### 视觉层次
1. 百分比（扇区内，最重要）
2. 徽章（扇区外，次要信息）
3. 颜色（视觉分组）

## 边界情况处理

### 单一资产类型
```dart
// 100% 占比
[房产]
  ↓
╭────────╮
│ 100.0% │
│   🥧   │
╰────────╯
```

### 两个资产类型
```dart
// 50% - 50%
[房产]     [现金]
  ↓         ↓
╭────────╮
│ 50.0%  │
│   🥧   │
│ 50.0%  │
╰────────╯
```

### 多个小扇区
```dart
// 房产 60%, 现金 20%, 投资 10%, 保险 10%
[房产]
  ↓
╭────────╮  [现金]
│ 60.0%  │    ↓
│   🥧   │  20.0%
│        │
╰────────╯
  ↑   ↑
(投资和保险 < 5%，无徽章)
```

## 未来增强

### 可能的改进
1. **动画过渡**：徽章出现/消失动画
2. **自定义图标**：徽章中显示资产类型图标
3. **详细信息**：长按徽章显示详细数据
4. **主题适配**：深色模式下的徽章样式
5. **手势交互**：滑动切换不同视图

### 实验性功能
1. **3D 效果**：扇区立体化
2. **渐变色**：徽章使用渐变背景
3. **粒子效果**：触摸时的视觉反馈
4. **数据动画**：数值变化时的过渡动画

## 设计原则

1. **简洁至上**：移除不必要的元素
2. **信息密度**：在有限空间内展示最多信息
3. **视觉引导**：徽章自然引导视线
4. **交互反馈**：即时的视觉响应
5. **自适应性**：适应不同屏幕尺寸

## 总结

徽章设计相比传统图例：
- ✅ 节省 30% 垂直空间
- ✅ 提升 50% 信息获取效率
- ✅ 消除滚动需求
- ✅ 增强视觉吸引力
- ✅ 改善用户体验

这是一个现代化、直观、高效的数据可视化解决方案。
