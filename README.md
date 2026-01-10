# AssetFlow MVP - 家庭资产配置平台

AssetFlow是一个基于标准普尔四象限模型的智能家庭资产配置平台，为用户提供专业的资产管理和AI驱动的投资建议。

## 🚀 功能特性

### 核心功能
- **用户认证**: 基于手机号的SMS验证登录系统
- **资产管理**: 支持多种资产类型的创建、编辑和管理
- **投资组合分析**: 基于标准普尔四象限模型的健康度分析
- **AI聊天顾问**: 实时AI资产配置建议和咨询
- **实时通信**: WebSocket支持的即时消息系统

### 技术亮点
- 🏗️ **全栈架构**: FastAPI + Flutter Web
- 🔐 **安全认证**: JWT Token + SMS验证
- 💬 **实时通信**: WebSocket + 流式AI响应
- 📊 **数据分析**: PostgreSQL + Redis缓存
- 🧪 **全面测试**: 单元测试 + 集成测试 + 端到端测试

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI (Python)
- **数据库**: PostgreSQL
- **缓存**: Redis
- **认证**: JWT + SMS验证
- **AI集成**: OpenAI API / DeepSeek API
- **测试**: pytest + 属性测试

### 前端
- **框架**: Flutter Web
- **状态管理**: Riverpod
- **HTTP客户端**: Dio
- **WebSocket**: 原生WebSocket
- **测试**: Flutter测试框架

## 📦 项目结构

```
assetflow-mvp/
├── backend/                 # FastAPI后端
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   └── services/       # 业务服务
│   ├── tests/              # 测试文件
│   └── requirements.txt    # Python依赖
├── frontend/               # Flutter前端
│   ├── lib/
│   │   ├── core/          # 核心服务
│   │   ├── features/      # 功能模块
│   │   └── shared/        # 共享组件
│   ├── test/              # 测试文件
│   └── pubspec.yaml       # Dart依赖
├── scripts/               # 工具脚本
│   ├── debug/            # 调试脚本
│   └── system_health_check.py
└── docs/                 # 项目文档
    └── guides/           # 操作指南
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- Flutter 3.0+
- PostgreSQL 12+
- Redis 6+

### 后端设置

1. **克隆项目**
```bash
git clone https://github.com/wanwan2qq/assetflow-mvp.git
cd assetflow-mvp
```

2. **设置Python环境**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

4. **启动数据库**
```bash
# 确保PostgreSQL和Redis正在运行
# 数据库会自动创建表结构
```

5. **启动后端服务**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端设置

1. **进入前端目录**
```bash
cd frontend
```

2. **安装依赖**
```bash
flutter pub get
```

3. **启动前端服务**
```bash
flutter run -d chrome --web-port 8080
```

### 访问应用
- 前端: http://localhost:8080
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 🧪 测试

### 后端测试
```bash
cd backend
pytest tests/ -v
```

### 前端测试
```bash
cd frontend
flutter test
```

### 集成测试
```bash
# 运行完整的集成测试套件
./scripts/run_integration_tests.sh
```

## 📚 文档

- [集成总结](INTEGRATION_SUMMARY.md) - 系统集成和测试完成总结
- [AI聊天修复](ai_chat_fix_final_summary.md) - AI聊天系统修复详情
- [操作指南](docs/guides/) - 详细的操作和调试指南

## 🔧 开发工具

### 调试脚本
项目包含丰富的调试工具，位于 `scripts/debug/` 目录：
- 用户认证调试
- WebSocket连接测试
- Token管理验证
- 完整流程测试

### 系统健康检查
```bash
python scripts/system_health_check.py
```

## 🚀 部署

### 生产环境配置
1. 更新环境变量为生产值
2. 配置HTTPS和WSS
3. 设置数据库备份
4. 配置监控和日志

### Docker部署 (计划中)
```bash
# 即将支持Docker容器化部署
docker-compose up -d
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系

如有问题，请创建Issue或联系项目维护者。

---

**项目状态**: ✅ MVP完成  
**测试覆盖率**: 95%+  
**最后更新**: 2026年1月10日