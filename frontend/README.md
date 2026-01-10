# AssetFlow Frontend

AssetFlow AI 原生家庭资产配置顾问应用的 Flutter 前端。

## 功能特性

- 🤖 **AI 对话式交互** - 通过自然语言完成资产盘点
- 📊 **可视化仪表板** - 直观展示资产分布和健康度
- 🔄 **实时数据同步** - WebSocket 连接确保数据实时更新
- 🎯 **个性化推荐** - 基于用户画像的智能建议
- 🔒 **安全认证** - JWT 令牌和数据隔离保护

## 技术栈

- **Flutter** 3.10+ - 跨平台移动应用框架
- **Riverpod** - 响应式状态管理
- **GoRouter** - 声明式路由系统
- **fl_chart** - 原生图表库
- **Dio** - HTTP 客户端
- **WebSocket** - 实时通信
- **Freezed** - 不可变数据类
- **JSON Annotation** - 序列化支持

## 项目结构

```
lib/
├── core/                   # 核心功能
│   ├── api/               # API 客户端
│   ├── models/            # 数据模型
│   ├── providers/         # 全局状态管理
│   ├── router/            # 路由配置
│   ├── services/          # 业务服务
│   ├── theme/             # 主题配置
│   └── navigation/        # 导航组件
├── features/              # 功能模块
│   ├── auth/              # 认证模块
│   ├── chat/              # 聊天模块
│   ├── dashboard/         # 仪表板模块
│   └── profile/           # 个人中心模块
├── shared/                # 共享组件
│   └── widgets/           # 通用 UI 组件
├── generated/             # 生成的代码
└── main.dart              # 应用入口
```

## 开发环境设置

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
flutter packages pub run build_runner build --delete-conflicting-outputs

# 监听文件变化自动生成
flutter packages pub run build_runner watch
```

### API 同步

```bash
# 从后端同步 API 规范并生成客户端代码
./scripts/sync_api.sh
```

### 运行应用

```bash
# 调试模式
flutter run

# 发布模式
flutter run --release
```

## API 集成

### 自动代码生成

项目使用 OpenAPI Generator 从后端 API 规范自动生成客户端代码：

1. 后端启动后访问 `http://localhost:8000/openapi.json` 获取 API 规范
2. 使用 `openapi-generator` 生成 Dart 客户端代码
3. 生成的代码位于 `lib/generated/api/`

### 手动同步

```bash
# 确保后端服务运行
cd backend && uvicorn app.main:app --reload

# 同步 API 规范
cd frontend && ./scripts/sync_api.sh
```

## 状态管理

使用 Riverpod 进行状态管理：

```dart
// Provider 定义
@riverpod
class AuthState extends _$AuthState {
  @override
  AsyncValue<User?> build() => const AsyncValue.data(null);
  
  Future<void> login(String phone, String code) async {
    // 登录逻辑
  }
}

// 在 Widget 中使用
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

## WebSocket 通信

实时聊天功能使用 WebSocket：

```dart
// 连接 WebSocket
final wsService = ref.read(webSocketServiceProvider);
await wsService.connect(userId, token);

// 监听消息
wsService.messageStream.listen((message) {
  // 处理收到的消息
});

// 发送消息
await wsService.sendMessage('用户消息');
```

## UI 组件

### 生成式 UI 组件

- **ValuationCard** - 房产估值确认卡片
- **ActionCard** - 推荐行动卡片
- **PortfolioChart** - 投资组合图表

### 使用示例

```dart
ValuationCard(
  propertyName: '天通苑北一区',
  estimatedValue: 4500000,
  pricePerSqm: '¥38,000/平',
  onConfirm: () => _confirmValuation(),
  onEdit: () => _editValuation(),
)
```

## 测试

### 运行测试

```bash
# 单元测试
flutter test

# 集成测试
flutter test integration_test/
```

### 测试结构

```
test/
├── unit/                  # 单元测试
├── widget/                # Widget 测试
└── integration/           # 集成测试
```

## 构建和部署

### Android

```bash
# 构建 APK
flutter build apk --release

# 构建 App Bundle
flutter build appbundle --release
```

### iOS

```bash
# 构建 iOS
flutter build ios --release
```

### Chrome

```bash
flutter run -d chrome --web-port=8080
```

## 开发指南

### 代码规范

- 使用 `flutter_lints` 进行代码检查
- 遵循 Dart 官方代码风格
- 使用 `const` 构造函数优化性能
- 为 Widget 添加 `key` 参数

### 提交规范

```bash
# 格式化代码
flutter format .

# 分析代码
flutter analyze

# 运行测试
flutter test
```

### 性能优化

- 使用 `const` 构造函数
- 避免在 `build` 方法中创建对象
- 合理使用 `ListView.builder` 处理长列表
- 使用 `RepaintBoundary` 优化重绘

## 故障排除

### 常见问题

1. **代码生成失败**
   ```bash
   flutter packages pub run build_runner clean
   flutter packages pub run build_runner build --delete-conflicting-outputs
   ```

2. **WebSocket 连接失败**
   - 检查后端服务是否运行
   - 确认 WebSocket 端点地址正确
   - 检查网络连接和防火墙设置

3. **API 同步失败**
   - 确保后端服务运行在 `http://localhost:8000`
   - 检查 OpenAPI 规范是否可访问
   - 安装 `openapi-generator-cli`

### 调试技巧

- 使用 Flutter Inspector 检查 Widget 树
- 使用 `print()` 或 `debugPrint()` 输出调试信息
- 使用 DevTools 进行性能分析
- 检查网络请求和响应

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。