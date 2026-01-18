# AssetFlow - AI原生家庭资产配置顾问

AssetFlow是一个基于标准普尔四象限模型的AI原生家庭资产配置平台，通过对话式交互帮助用户完成资产盘点、分析和配置建议。

## 🚀 核心特性

### AI对话式交互
- **自然语言理解**: 通过聊天完成资产信息收集，无需填表
- **智能信息提取**: 自动从对话中提取资产、用户画像和财务目标
- **实时流式响应**: WebSocket + SSE流式输出，即时反馈
- **上下文记忆**: 4层记忆架构确保AI记住用户说过的每一句话

### 4层认知记忆架构
```
L0 (对话历史) ← 滑动窗口，防止上下文断裂
L1 (结构化事实) ← 资产、用户画像（即时一致性）
L2 (认知状态) ← 采集状态、财务目标（即时一致性）
L3 (心理洞察) ← 风险偏好、决策风格（最终一致性）
L4 (向量记忆) ← 语义搜索、长期记忆（最终一致性）
```

### 智能资产分析
- **标准普尔四象限模型**: 要花的钱、保命的钱、生钱的钱、保本升值的钱
- **动态配置建议**: 基于年龄、家庭结构、风险偏好的个性化建议
- **可视化仪表板**: 资产分布饼图、四象限配置图、健康度评分
- **风险预警**: 实时识别配置风险并提供行动建议

### 技术亮点
- 🧠 **双进程认知架构**: System 1快速思考 + System 2深度分析
- 🔄 **上下文刷新机制**: 确保AI立即看到用户提供的信息
- 🎯 **生成式UI**: 动态生成估值卡片、行动卡片、图表组件
- 🔐 **安全认证**: JWT Token + SMS验证 + 持久化存储
- 📊 **向量搜索**: pgvector + BGE本地嵌入模型

## 🛠️ 技术栈

### 后端 (Python 3.11+)
- **框架**: FastAPI 0.104+ (异步高性能)
- **数据库**: PostgreSQL 16 + pgvector (向量搜索)
- **ORM**: SQLModel (类型安全)
- **AI**: LangChain + DeepSeek/OpenAI + BGE嵌入模型
- **搜索**: Tavily API (实时信息检索)
- **缓存**: Redis 7
- **测试**: pytest + hypothesis (属性测试)

### 前端 (Flutter 3.10+)
- **框架**: Flutter Web (跨平台)
- **状态管理**: Riverpod 2.0 (响应式)
- **路由**: GoRouter (声明式)
- **图表**: fl_chart (原生图表)
- **WebSocket**: 原生WebSocket + 心跳机制
- **持久化**: SharedPreferences (Token存储)

## 📦 项目结构

```
assetflow/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── api/api_v1/        # API路由 (认证、资产、聊天、推荐)
│   │   ├── core/              # 核心配置 (数据库、认证、错误处理)
│   │   ├── models/            # 数据模型 (用户、资产、认知、记忆)
│   │   └── services/          # 业务服务
│   │       ├── chat_agent.py  # 核心AI对话引擎
│   │       ├── memory_service.py  # 向量记忆服务 (L4)
│   │       ├── insight_service.py # 心理洞察分析 (L3)
│   │       └── information_extraction.py  # LLM信息提取
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # 测试套件 (单元+集成+E2E)
│   └── pyproject.toml         # Python依赖 (uv)
├── frontend/                  # Flutter前端
│   ├── lib/
│   │   ├── core/             # 核心功能
│   │   │   ├── providers/    # Riverpod状态管理
│   │   │   ├── services/     # WebSocket、API、Token存储
│   │   │   └── router/       # GoRouter路由配置
│   │   ├── features/         # 功能模块
│   │   │   ├── auth/         # 登录、验证码
│   │   │   ├── chat/         # AI聊天界面
│   │   │   ├── dashboard/    # 资产仪表板
│   │   │   └── profile/      # 个人中心
│   │   └── shared/widgets/   # 共享组件 (图表、卡片)
│   ├── test/                 # 测试文件
│   └── pubspec.yaml          # Dart依赖
├── docs/                     # 项目文档
│   ├── Memory/               # 记忆架构文档
│   ├── guides/               # 操作指南
│   └── fix_summary/          # 修复总结
├── scripts/                  # 工具脚本
│   ├── debug/                # 调试脚本
│   ├── start_backend_lan.sh  # 启动后端 (局域网)
│   └── start_frontend_lan.sh # 启动前端 (局域网)
└── README.md                 # 本文档
```

## 🚀 快速开始

### 环境要求
- Python 3.11+ (推荐使用 uv 包管理器)
- Flutter 3.10+
- PostgreSQL 16+ (with pgvector extension)
- Redis 7+
- Node.js 18+ (用于OpenAPI代码生成)

### 1. 后端设置

```bash
# 进入后端目录
cd backend

# 安装 uv (Python包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入配置:
# - POSTGRES_* (数据库配置)
# - OPENAI_API_KEY (DeepSeek或OpenAI)
# - TAVILY_API_KEY (搜索API)
# - SECRET_KEY (JWT密钥)

# 启动数据库 (Docker)
docker-compose up postgres redis -d

# 初始化数据库 (包含pgvector扩展)
python scripts/init_phase4_db.py

# 运行数据库迁移
alembic upgrade head

# 验证安装
python scripts/verify_phase4.py

# 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端设置

```bash
# 进入前端目录
cd frontend

# 安装依赖
flutter pub get

# 生成代码 (Riverpod、Freezed、JSON)
flutter pub run build_runner build --delete-conflicting-outputs

# 同步API客户端 (确保后端已启动)
./scripts/sync_api.sh

# 启动前端服务
flutter run -d chrome --web-port 8080
```

### 3. 访问应用

- **前端**: http://localhost:8080
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

### 局域网访问 (可选)

```bash
# 启动后端 (局域网模式)
./scripts/start_backend_lan.sh

# 启动前端 (局域网模式)
./scripts/start_frontend_lan.sh

# 访问: http://<your-ip>:8080
```

## 🧪 测试

### 后端测试
```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_chat_agent.py -v

# 运行端到端测试
pytest tests/test_e2e_core_functionality.py -v

# 生成覆盖率报告
pytest --cov=app --cov-report=html
```

### 前端测试
```bash
cd frontend

# 运行所有测试
flutter test

# 运行特定测试
flutter test test/core/providers/auth_provider_test.dart
```

### 集成测试
```bash
# 运行完整的集成测试套件
./scripts/run_integration_tests.sh

# 系统健康检查
python scripts/system_health_check.py
```

## 📚 核心架构

### 双进程认知架构 (Dual-Process Architecture)

系统采用双进程认知架构，模拟人类的快速思考和慢速思考：

**System 1 (快速思考 - 即时一致性)**
- 信息提取: 从对话中提取结构化数据
- 数据库写入: 更新L1/L2层数据
- 上下文刷新: 确保AI立即看到新数据
- 延迟: ~600ms (阻塞，必须完成)

**System 2 (慢速思考 - 最终一致性)**
- 心理洞察: 分析用户心理特征和决策风格
- 向量记忆: 生成嵌入并存储到向量数据库
- 延迟: ~2-5s (异步，不阻塞响应)

### 4层记忆架构

```
┌─────────────────────────────────────────────┐
│ L0: 对话历史 (Sliding Window)              │
│ - 最近10条消息                              │
│ - 防止上下文断裂                            │
│ - 理解用户引用 ("那个"、"之前的")          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ L1: 结构化事实 (Immediate Consistency)     │
│ - UserProfile: 年龄、家庭、职业、收入       │
│ - UserAsset: 房产、现金、投资、保险、负债   │
│ - 即时写入，即时可见                        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ L2: 认知状态 (Immediate Consistency)       │
│ - UserCognition.collection_status           │
│ - UserCognition.financial_goals             │
│ - 跟踪信息采集进度                          │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ L3: 心理洞察 (Eventual Consistency)        │
│ - UserCognition.risk_profile                │
│ - 决策风格、风险偏好、情绪状态              │
│ - 顾问策略笔记                              │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ L4: 向量记忆 (Eventual Consistency)        │
│ - VectorMemory: 语义搜索                    │
│ - BGE嵌入模型 (1024维)                     │
│ - pgvector HNSW索引                         │
└─────────────────────────────────────────────┘
```

### 关键修复: 上下文刷新机制

**问题**: AI不记得用户刚说的话
```
用户: "我35岁"
AI: "为了更好地建议，请问您多大年纪？" ❌
```

**解决方案**: 在System 1完成后立即刷新上下文
```python
# 1. 提取信息并写入数据库
await extract_and_store_information(message, user_id)

# 2. 🔄 立即从数据库刷新上下文
await refresh_context_from_db(user_id, context)

# 3. 下一轮对话时，AI能看到最新数据
```

**效果**: AI立即记住用户提供的信息
```
用户: "我35岁"
AI: "基于您35岁的年龄，我建议..." ✅
```

## 🎯 核心功能详解

### 1. AI对话引擎 (chat_agent.py)

**特性**:
- 自然语言理解和生成
- 流式响应 (SSE)
- 上下文感知 (Fact Sheet + 对话历史)
- 思维链推理 (Chain of Thought)
- 动态UI组件生成

**Persona设计**:
- 首席资产配置专家角色
- 温暖而专业的语气
- 共情能力 (识别焦虑、压力)
- 结果导向 (直接给建议，不机械收集信息)

### 2. 信息提取 (information_extraction.py)

**LLM驱动的提取**:
- 从自然对话中提取结构化数据
- 支持模糊表达 ("差不多50万"、"三四十岁")
- 上下文理解 ("那个房子"、"改成100万")
- 置信度评分

**提取内容**:
- 资产: 类型、金额、位置、面积
- 用户画像: 年龄、家庭、职业、收入、风险偏好
- 财务目标: 退休、购房、教育、财富增长

### 3. 投资组合分析 (portfolio_analyzer.py)

**标准普尔四象限模型**:
- 要花的钱 (10%): 应急资金
- 保命的钱 (20%): 保险保障
- 生钱的钱 (30%): 高风险投资
- 保本升值 (40%): 稳健投资

**动态调整**:
- 年龄: 年轻人增加"生钱的钱"
- 家庭: 有孩子增加"要花的钱"和"保命的钱"
- 风险偏好: 保守型增加"保本升值"

**风险预警**:
- 房产占比过高 (>60%)
- 流动性不足 (<3个月生活费)
- 保险缺失
- 负债过高 (>50%)

### 4. 向量记忆 (memory_service.py)

**技术栈**:
- 嵌入模型: BAAI/bge-large-zh-v1.5 (1024维)
- 向量数据库: pgvector
- 索引: HNSW (快速近似搜索)
- 相似度: 余弦相似度

**功能**:
- 语义搜索: 找到相关的历史对话
- 长期记忆: 存储重要生活事件
- 优雅降级: 嵌入失败时使用关键词搜索

### 5. 心理洞察 (insight_service.py)

**分析维度**:
- 风险承受能力 (tolerance)
- 决策风格 (decision_style)
- 信心水平 (confidence_level)
- 当前情绪 (current_sentiment)
- 损失厌恶 (loss_aversion)
- 不确定性容忍度 (uncertainty_tolerance)
- 财务素养 (financial_literacy)
- 家庭责任感 (family_responsibility)
- 规划视野 (planning_horizon)

**顾问策略**:
- Comfort Mode: 安抚焦虑用户
- Growth Mode: 激励保守用户
- Analytical Mode: 满足理性用户
- Empathy Mode: 支持压力用户

## 🎨 前端架构

### 状态管理 (Riverpod)

**Provider类型**:
- `authStateProvider`: 认证状态
- `webSocketServiceProvider`: WebSocket连接
- `chatMessagesProvider`: 聊天消息列表
- `dashboardDataProvider`: 仪表板数据

**特性**:
- 响应式更新
- 自动依赖追踪
- 类型安全
- 易于测试

### WebSocket服务

**功能**:
- 自动重连 (指数退避)
- 心跳机制 (30s间隔)
- 连接状态管理
- 错误处理和恢复
- 动态URL (支持局域网)

**连接状态**:
- `disconnected`: 未连接
- `connecting`: 连接中
- `connected`: 已连接
- `reconnecting`: 重连中
- `error`: 错误

### 可视化组件

**PortfolioChart (资产分布饼图)**:
- 动态数据聚合
- 统一颜色方案
- 空状态处理
- 响应式布局
- 百分比显示 (>5%)

**SPQuadrantChart (四象限图)**:
- 标准普尔模型可视化
- 当前配置 vs 理想配置
- 缺口分析
- 建议显示

**生成式UI组件**:
- `ValuationCard`: 房产估值确认
- `ActionCard`: 风险预警和行动建议
- `PortfolioChart`: 动态生成的图表

## 📖 文档

### 记忆架构文档
- [Phase 4 完成报告](docs/Memory/PHASE4_COMPLETE.md)
- [双进程架构图](docs/Memory/DUAL_PROCESS_ARCHITECTURE_DIAGRAM.md)
- [上下文断裂修复](docs/Memory/CONTEXT_DISCONTINUITY_FIX_SUMMARY.md)
- [LLM提取重构](docs/Memory/LLM_EXTRACTION_REFACTOR_SUMMARY.md)

### 操作指南
- [启动指南](docs/guides/STARTUP_GUIDE.md)
- [局域网访问](docs/guides/LAN_ACCESS_FIX_COMPLETE.md)
- [仪表板优化](docs/guides/DASHBOARD_OPTIMIZATION.md)
- [聊天页面优化](docs/guides/CHAT_PAGE_OPTIMIZATION.md)

### 修复总结
- [登录修复](docs/fix_summary/LOGIN_FIX_REPORT.md)
- [用户上下文记忆修复](docs/fix_summary/USER_CONTEXT_MEMORY_FIX.md)
- [双响应Bug修复](docs/fix_summary/double_response_bug_fix_summary.md)

## 🔧 开发工具

### 调试脚本 (scripts/debug/)
- `debug_auth_state.py`: 认证状态调试
- `debug_websocket_connection_issue.py`: WebSocket连接测试
- `test_complete_chat_flow.py`: 完整聊天流程测试
- `test_profile_complete_flow.py`: 用户画像流程测试

### 系统工具
```bash
# 系统健康检查
python scripts/system_health_check.py

# 测试上下文刷新
python scripts/test_context_discontinuity_fix.py

# 测试双进程架构
python scripts/test_dual_process_architecture.py

# 测试向量记忆
python scripts/test_phase4_vector_memory.py
```

## 🚀 部署

### 生产环境配置

**环境变量**:
```bash
# 数据库
POSTGRES_SERVER=your-db-host
POSTGRES_USER=assetflow
POSTGRES_PASSWORD=strong-password
POSTGRES_DB=assetflow

# AI服务
OPENAI_API_KEY=your-deepseek-or-openai-key
OPENAI_API_BASE=https://api.deepseek.com  # 可选
TAVILY_API_KEY=your-tavily-key

# 安全
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8天

# CORS (添加生产域名)
BACKEND_CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

**数据库设置**:
```bash
# 1. 安装pgvector扩展
psql -U postgres -d assetflow -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 2. 运行迁移
alembic upgrade head

# 3. 验证安装
python scripts/verify_phase4.py
```

**HTTPS配置**:
- 使用Nginx反向代理
- 配置SSL证书 (Let's Encrypt)
- WebSocket升级到WSS

**监控和日志**:
- 配置日志级别 (INFO/WARNING)
- 设置日志轮转
- 监控API响应时间
- 跟踪错误率

### Docker部署 (推荐)

```bash
# 构建镜像
docker-compose -f docker-compose.prod.yml build

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f backend

# 停止服务
docker-compose down
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发流程
1. Fork项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启Pull Request

### 代码规范
- Python: 遵循PEP 8，使用Ruff格式化
- Dart: 遵循Dart Style Guide，使用`dart format`
- 提交前运行测试: `pytest` 和 `flutter test`
- 更新相关文档

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 联系

如有问题，请创建Issue或联系项目维护者。

---

**项目状态**: ✅ Phase 4 完成 (向量记忆)  
**测试覆盖率**: 95%+  
**最后更新**: 2026年1月16日

## 🎯 路线图

### 已完成 ✅
- [x] Phase 1: 基础架构和认证
- [x] Phase 2: LLM信息提取
- [x] Phase 3: 心理洞察分析
- [x] Phase 4: 向量记忆 (RAG)
- [x] 上下文刷新机制
- [x] 双进程认知架构
- [x] 生成式UI组件
- [x] 局域网访问支持

### 进行中 🚧
- [ ] 商业产品推荐优化
- [ ] 用户行为分析
- [ ] A/B测试框架

### 计划中 📋
- [ ] 移动端App (iOS/Android)
- [ ] 多语言支持
- [ ] 语音交互
- [ ] 数据导出功能
- [ ] 家庭账户共享