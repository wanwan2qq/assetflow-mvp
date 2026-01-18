# AssetFlow Frontend

AssetFlow前端是一个基于Flutter Web的AI原生家庭资产配置顾问应用，提供对话式交互、实时数据同步和可视化仪表板。

## 🚀 核心特性

### AI对话式交互
- **自然语言输入**: 通过聊天完成资产盘点，无需填表
- **实时流式响应**: WebSocket连接，即时反馈
- **生成式UI**: 动态生成估值卡片、行动卡片、图表组件
- **上下文记忆**: AI记住用户说过的每一句话

### 实时数据同步
- **WebSocket连接**: 双向实时通信
- **自动重连**: 指数退避策略，最多5次重试
- **心跳机制**: 30秒间隔，检测连接健康
- **连接状态管理**: 5种状态 (disconnected, connecting, connected, reconnecting, error)
- **优雅降级**: 连接失败时显示友好提示

### 可视化仪表板
- **资产分布饼图**: 动态数据聚合，统一颜色方案
- **四象限配置图**: 标准普尔模型可视化
- **健康度评分**: 综合评估投资组合
- **风险预警卡片**: 实时识别配置风险

### 状态管理 (Riverpod)
- **响应式更新**: 自动依赖追踪
- **类型安全**: 编译时类型检查
- **易于测试**: 纯函数式Provider
- **持久化存储**: Token和用户信息本地存储

## 🛠 技术栈

- **Flutter** 3.10+ - 跨平台移动应用框架
- **Riverpod** 2.0 - 响应式状态管理
- **GoRouter** - 声明式路由系统
- **fl_chart** - 原生图表库 (饼图、四象限图)
- **Dio** - HTTP客户端 (API调用)
- **WebSocket** - 原生WebSocket (实时通信)
- **SharedPreferences** - 本地持久化存储
- **Freezed** - 不可变数据类
- **JSON Annotation** - 序列化支持
- **Build Runner** - 代码生成工具

## 📁 项目结构

```
lib/
├── core/                      # 核心功能
│   ├── api/                  # API客户端
│   │   └── api_client.dart   # 生成的API客户端
│   ├── models/               # 数据模型
│   │   ├── user.dart         # 用户模型
│   │   ├── asset.dart        # 资产模型
│   │   └── chat_message.dart # 聊天消息模型
│   ├── providers/            # 全局状态管理
│   │   ├── auth_provider.dart  # 认证状态
│   │   └── websocket_provider.dart  # WebSocket状态
│   ├── router/               # 路由配置
│   │   └── app_router.dart   # GoRouter配置
│   ├── services/             # 业务服务
│   │   ├── api_service.dart  # API服务封装
│   │   ├── websocket_service.dart  # WebSocket服务
│   │   └── token_storage_service.dart  # Token存储
│   ├── theme/                # 主题配置
│   │   └── app_theme.dart    # 应用主题
│   └── navigation/           # 导航组件
│       └── app_navigation.dart  # 底部导航栏
├── features/                 # 功能模块
│   ├── auth/                 # 认证模块
│   │   ├── data/             # 数据层
│   │   ├── domain/           # 业务逻辑层
│   │   └── presentation/     # 展示层
│   │       ├── pages/        # 页面
│   │       │   └── login_page.dart
│   │       └── widgets/      # 组件
│   ├── chat/                 # 聊天模块
│   │   ├── presentation/
│   │   │   ├── pages/
│   │   │   │   └── chat_page.dart
│   │   │   ├── widgets/
│   │   │   │   ├── message_bubble.dart
│   │   │   │   ├── valuation_card.dart
│   │   │   │   └── action_card.dart
│   │   │   └── providers/
│   │   │       └── chat_provider.dart
│   ├── dashboard/            # 仪表板模块
│   │   └── presentation/
│   │       ├── pages/
│   │       │   └── dashboard_page.dart
│   │       └── widgets/
│   │           ├── asset_summary_card.dart
│   │           └── health_score_card.dart
│   └── profile/              # 个人中心模块
│       └── presentation/
│           ├── pages/
│           │   └── profile_page.dart
│           └── widgets/
├── shared/                   # 共享组件
│   └── widgets/              # 通用UI组件
│       ├── portfolio_chart.dart  # 资产分布饼图
│       ├── sp_quadrant_chart.dart  # 四象限图
│       ├── loading_indicator.dart
│       └── error_widget.dart
├── generated/                # 生成的代码
│   └── api/                  # OpenAPI生成的客户端
└── main.dart                 # 应用入口
```

## 🚀 开发环境设置

### 前置要求

- Flutter 3.10+
- Dart 3.0+
- Android Studio / VS Code
- 后端服务运行在 `http://localhost:8000`

### 安装依赖

```bash
cd frontend
flutter pub get
```

### 代码生成

```bash
# 生成 Riverpod、Freezed、JSON 序列化代码
flutter pub run build_runner build --delete-conflicting-outputs

# 监听文件变化自动生成 (开发时推荐)
flutter pub run build_runner watch
```

### API 同步

```bash
# 从后端同步 API 规范并生成客户端代码
# 确保后端服务已启动在 http://localhost:8000
./scripts/sync_api.sh
```

### 运行应用

```bash
# 调试模式 (Chrome)
flutter run -d chrome --web-port 8080

# 发布模式
flutter run --release -d chrome

# 局域网模式 (支持移动设备访问)
./scripts/start_frontend_lan.sh
```

## 🧪 测试

### 运行测试

```bash
# 单元测试
flutter test

# 特定测试文件
flutter test test/core/providers/auth_provider_test.dart

# 集成测试
flutter test integration_test/

# 生成覆盖率报告
flutter test --coverage
```

### 测试结构

```
test/
├── core/                     # 核心功能测试
│   ├── providers/            # Provider测试
│   ├── services/             # 服务测试
│   └── router/               # 路由测试
├── features/                 # 功能模块测试
│   ├── auth/                 # 认证测试
│   ├── chat/                 # 聊天测试
│   └── dashboard/            # 仪表板测试
├── shared/                   # 共享组件测试
│   └── widgets/              # Widget测试
└── integration/              # 集成测试
```

## 🎯 核心功能详解

### 1. 状态管理 (Riverpod)

**AuthProvider (认证状态)**:
```dart
@riverpod
class AuthState extends _$AuthState {
  @override
  AsyncValue<User?> build() {
    _initializeAuthState();  // 从持久化存储恢复
    return const AsyncValue.loading();
  }
  
  Future<void> login(String phone, String code) async {
    // 1. 清除旧认证信息
    // 2. 调用后端登录API
    // 3. 存储Token和用户信息
    // 4. 更新状态
  }
  
  Future<void> logout() async {
    // 1. 清除持久化存储
    // 2. 清除内存状态
    // 3. 更新状态
  }
}
```

**使用示例**:
```dart
class LoginPage extends ConsumerWidget {
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    
    return authState.when(
      data: (user) => user != null ? HomePage() : LoginForm(),
      loading: () => LoadingWidget(),
      error: (error, _) => ErrorWidget(error),
    );
  }
}
```

### 2. WebSocket服务

**连接管理**:
```dart
class WebSocketService {
  // 连接状态
  WebSocketConnectionState _connectionState;
  
  // 自动重连参数
  int _reconnectAttempts = 0;
  static const int _maxReconnectAttempts = 5;
  
  // 心跳机制
  Timer? _heartbeatTimer;
  static const Duration _heartbeatInterval = Duration(seconds: 30);
  
  Future<void> connect(int userId, String token) async {
    // 1. 动态获取WebSocket URL (支持局域网)
    // 2. 建立WebSocket连接
    // 3. 设置消息监听
    // 4. 启动心跳机制
  }
  
  Future<void> sendMessage(String message) async {
    // 1. 检查连接状态
    // 2. 发送消息到sink
    // 3. 错误处理
  }
  
  void _scheduleReconnect() {
    // 指数退避策略
    final delay = Duration(
      milliseconds: (_initialReconnectDelay.inMilliseconds * 
        (1 << _reconnectAttempts)).clamp(
          _initialReconnectDelay.inMilliseconds,
          _maxReconnectDelay.inMilliseconds,
        ),
    );
    
    _reconnectTimer = Timer(delay, _attemptReconnect);
  }
}
```

**动态URL支持**:
```dart
String _getWebSocketUrl() {
  final currentHost = Uri.base.host;
  
  // localhost使用localhost:8000
  if (currentHost == 'localhost' || currentHost == '127.0.0.1') {
    return 'ws://localhost:8000';
  }
  
  // 局域网IP使用相同IP的8000端口
  return 'ws://$currentHost:8000';
}
```

### 3. 可视化组件

**PortfolioChart (资产分布饼图)**:

**特性**:
- 动态数据聚合: 自动按资产类型分组
- 统一颜色方案: `assetTypeColors`常量
- 空状态处理: 友好的空状态UI
- 响应式布局: 使用Wrap自适应
- 百分比显示: 仅显示>5%的标签

**实现**:
```dart
class PortfolioChart extends StatelessWidget {
  final List<Asset> assets;
  
  Map<AssetType, double> _calculateAssetDistribution() {
    final distribution = <AssetType, double>{};
    
    for (final asset in assets) {
      if (asset.assetType != AssetType.liability) {
        distribution[asset.assetType] = 
            (distribution[asset.assetType] ?? 0.0) + asset.value;
      }
    }
    
    return distribution;
  }
  
  List<PieChartSectionData> _buildPieChartSections(
    Map<AssetType, double> distribution,
    double totalValue,
  ) {
    if (totalValue == 0) return [];  // 防止除零
    
    return distribution.entries.map((entry) {
      final percentage = (entry.value / totalValue) * 100;
      
      return PieChartSectionData(
        color: assetTypeColors[entry.key] ?? Colors.grey,
        value: percentage,
        title: percentage > 5 ? '${percentage.toStringAsFixed(1)}%' : '',
        radius: 45,
        centerSpaceRadius: 45,
      );
    }).toList();
  }
}
```

**SPQuadrantChart (四象限图)**:

**特性**:
- 标准普尔模型可视化
- 当前配置 vs 理想配置对比
- 缺口分析
- 响应式布局 (AspectRatio 1:1)

**实现**:
```dart
class SPQuadrantChart extends StatelessWidget {
  final Map<String, double> currentAllocations;
  final Map<String, double> idealAllocations;
  
  Widget _buildQuadrantGrid(BuildContext context, data) {
    return AspectRatio(
      aspectRatio: 1.0,  // 确保正方形
      child: GridView.count(
        crossAxisCount: 2,
        children: [
          _buildQuadrant('要花的钱', data['spend'], Colors.blue),
          _buildQuadrant('保命的钱', data['protect'], Colors.green),
          _buildQuadrant('生钱的钱', data['grow'], Colors.orange),
          _buildQuadrant('保本升值', data['preserve'], Colors.purple),
        ],
      ),
    );
  }
}
```

### 4. 生成式UI组件

**ValuationCard (房产估值卡片)**:
```dart
class ValuationCard extends StatelessWidget {
  final String propertyName;
  final double estimatedValue;
  final String pricePerSqm;
  final VoidCallback onConfirm;
  final VoidCallback onEdit;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      child: Column(
        children: [
          Text('房产估值确认'),
          Text(propertyName),
          Text('估值: ¥${estimatedValue.toStringAsFixed(0)}'),
          Text(pricePerSqm),
          Row(
            children: [
              ElevatedButton(
                onPressed: onConfirm,
                child: Text('确认'),
              ),
              TextButton(
                onPressed: onEdit,
                child: Text('修改'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
```

**ActionCard (行动建议卡片)**:
```dart
class ActionCard extends StatelessWidget {
  final String type;  // diversification, liquidity, insurance
  final String title;
  final String description;
  final String priority;  // high, medium, low
  
  Color _getPriorityColor() {
    switch (priority) {
      case 'high': return Colors.red;
      case 'medium': return Colors.orange;
      case 'low': return Colors.blue;
      default: return Colors.grey;
    }
  }
}
```

## 🎨 UI/UX优化

### 连接状态可视化

**连接状态指示器**:
```dart
Widget _buildConnectionStatus(WebSocketConnectionState state) {
  switch (state) {
    case WebSocketConnectionState.connected:
      return Row(
        children: [
          Icon(Icons.circle, color: Colors.green, size: 8),
          Text('已连接'),
        ],
      );
    case WebSocketConnectionState.connecting:
      return Row(
        children: [
          SizedBox(
            width: 12,
            height: 12,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          Text('连接中...'),
        ],
      );
    case WebSocketConnectionState.reconnecting:
      return Row(
        children: [
          Icon(Icons.refresh, color: Colors.orange, size: 16),
          Text('重连中...'),
        ],
      );
    case WebSocketConnectionState.error:
      return Row(
        children: [
          Icon(Icons.error, color: Colors.red, size: 16),
          Text('连接失败'),
        ],
      );
    default:
      return SizedBox.shrink();
  }
}
```

### 优雅的空状态

**空状态设计**:
```dart
Widget _buildEmptyState() {
  return Center(
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(
          Icons.pie_chart_outline,
          size: 64,
          color: Colors.grey[400],
        ),
        SizedBox(height: 16),
        Text(
          '暂无资产数据',
          style: TextStyle(
            fontSize: 18,
            color: Colors.grey[600],
          ),
        ),
        SizedBox(height: 8),
        Text(
          '请先添加资产',
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey[500],
          ),
        ),
      ],
    ),
  );
}
```

### 加载状态

**骨架屏**:
```dart
Widget _buildLoadingSkeleton() {
  return Shimmer.fromColors(
    baseColor: Colors.grey[300]!,
    highlightColor: Colors.grey[100]!,
    child: Column(
      children: [
        Container(height: 200, color: Colors.white),
        SizedBox(height: 16),
        Container(height: 100, color: Colors.white),
      ],
    ),
  );
}
```

## 📖 最佳实践

### 1. Provider使用

**DO**: 使用`ref.watch`监听状态变化
```dart
final authState = ref.watch(authStateProvider);
```

**DON'T**: 在build方法外使用`ref.watch`
```dart
// ❌ 错误
void _handleLogin() {
  final authState = ref.watch(authStateProvider);  // 不会响应变化
}

// ✅ 正确
void _handleLogin() {
  final authState = ref.read(authStateProvider.notifier);
  authState.login(phone, code);
}
```

### 2. WebSocket使用

**DO**: 在dispose时断开连接
```dart
@override
void dispose() {
  ref.read(webSocketServiceProvider).disconnect();
  super.dispose();
}
```

**DON'T**: 忘记处理连接错误
```dart
// ❌ 错误
await wsService.sendMessage(message);

// ✅ 正确
try {
  await wsService.sendMessage(message);
} catch (e) {
  showErrorSnackBar('发送失败: $e');
}
```

### 3. 状态管理

**DO**: 使用AsyncValue处理异步状态
```dart
authState.when(
  data: (user) => HomePage(),
  loading: () => LoadingPage(),
  error: (error, _) => ErrorPage(error),
);
```

**DON'T**: 直接访问异步数据
```dart
// ❌ 错误
final user = authState.value;  // 可能为null

// ✅ 正确
final user = authState.when(
  data: (user) => user,
  loading: () => null,
  error: (_, __) => null,
);
```

## 🔧 故障排除

### 常见问题

**1. WebSocket连接失败**
```bash
# 检查后端服务
curl http://localhost:8000/health

# 检查WebSocket端点
wscat -c ws://localhost:8000/api/v1/chat/ws/chat/1?token=your-token
```

**2. 代码生成失败**
```bash
# 清理并重新生成
flutter clean
flutter pub get
flutter pub run build_runner clean
flutter pub run build_runner build --delete-conflicting-outputs
```

**3. API同步失败**
```bash
# 确保后端运行
curl http://localhost:8000/openapi.json

# 手动生成API客户端
openapi-generator-cli generate \
  -i http://localhost:8000/openapi.json \
  -g dart \
  -o lib/generated/api
```

**4. Token过期**
```dart
// 检查Token状态
ref.read(authStateProvider.notifier).debugTokenState();

// 强制刷新Token
ref.read(authStateProvider.notifier).forceTokenRefresh();
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。