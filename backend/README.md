# AssetFlow Backend

AssetFlow 是一个 AI 驱动的家庭资产配置顾问系统的后端服务，基于 FastAPI 构建，提供完整的资产管理、投资组合分析和 AI 聊天功能。

## 🚀 功能特性

### 核心功能
- **用户认证与授权**: JWT 令牌认证，安全的用户数据隔离
- **资产管理**: 支持多种资产类型的 CRUD 操作
- **投资组合分析**: 净资产计算、房产占比分析、流动性比率计算
- **AI 聊天集成**: WebSocket 实时通信，流式响应处理
- **推荐系统**: 基于投资组合健康度的个性化推荐
- **错误处理**: 优雅的错误处理和自动重试机制

### 技术特性
- **高性能**: 异步 FastAPI 框架，支持高并发
- **数据库**: PostgreSQL + SQLModel ORM
- **缓存**: Redis 缓存支持
- **实时通信**: WebSocket 支持
- **AI 集成**: LangChain + OpenAI 集成
- **容器化**: Docker 开发环境支持

## 🛠 技术栈

- **框架**: FastAPI 0.104+
- **Python**: 3.11+
- **数据库**: PostgreSQL 15
- **ORM**: SQLModel
- **缓存**: Redis 7
- **认证**: JWT (python-jose)
- **AI**: LangChain + OpenAI
- **搜索**: Tavily API
- **测试**: pytest + hypothesis
- **代码质量**: Ruff

## 📋 环境要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (可选)

## 🚀 快速开始

### 1. 环境设置

```bash
# 克隆项目
cd backend

# 安装 uv (推荐的 Python 包管理器)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

关键环境变量：
```env
# 数据库配置
POSTGRES_SERVER=localhost
POSTGRES_USER=assetflow
POSTGRES_PASSWORD=assetflow123
POSTGRES_DB=assetflow
POSTGRES_PORT=5432

# Redis 配置
REDIS_URL=redis://localhost:6379

# AI 服务配置
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key

# 应用配置
SECRET_KEY=your_secret_key
ENVIRONMENT=development
```

### 3. 数据库设置

#### 使用 Docker (推荐)
```bash
# 启动数据库服务
docker-compose up postgres redis -d

# 等待服务启动
docker-compose logs -f postgres
```

#### 手动安装
```bash
# 安装 PostgreSQL 和 Redis
brew install postgresql redis

# 启动服务
brew services start postgresql
brew services start redis

# 创建数据库
createdb assetflow
```

### 4. 数据库迁移

```bash
# 运行数据库迁移
alembic upgrade head
```

### 5. 启动应用

```bash
# 开发模式启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用 Docker
docker-compose up backend
```

应用将在 http://localhost:8000 启动

- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 🧪 测试

### 运行测试套件

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_assets.py

# 运行端到端测试
pytest tests/test_e2e_core_functionality.py

# 运行集成测试
pytest tests/test_complete_user_flow_integration.py

# 生成测试覆盖率报告
pytest --cov=app --cov-report=html
```

### 测试类型

- **单元测试**: 核心业务逻辑测试
- **集成测试**: API 端点和数据库集成测试
- **端到端测试**: 完整用户流程测试
- **属性测试**: 使用 Hypothesis 进行属性验证

## 📁 项目结构

```
backend/
├── app/                    # 应用主目录
│   ├── api/               # API 路由
│   │   └── api_v1/        # API v1 版本
│   ├── core/              # 核心配置和工具
│   │   ├── config.py      # 应用配置
│   │   ├── database.py    # 数据库配置
│   │   ├── security.py    # 安全相关
│   │   └── error_handling.py # 错误处理
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑服务
│   └── utils/             # 工具函数
├── tests/                 # 测试文件
├── alembic/              # 数据库迁移
├── scripts/              # 脚本工具
├── docker-compose.yml    # Docker 配置
├── Dockerfile.dev        # 开发环境 Docker
├── pyproject.toml        # 项目配置
└── README.md            # 项目文档
```

## 🔧 开发工具

### 代码质量

```bash
# 代码格式化和检查
ruff check .
ruff format .

# 类型检查 (如果使用 mypy)
mypy app/
```

### 数据库操作

```bash
# 创建新的迁移
alembic revision --autogenerate -m "描述变更"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 系统健康检查

```bash
# 运行系统健康检查
python scripts/system_health_check.py

# 运行集成测试套件
bash scripts/run_integration_tests.sh
```

## 🚀 部署

### Docker 部署

```bash
# 构建生产镜像
docker build -t assetflow-backend .

# 使用 docker-compose 部署
docker-compose -f docker-compose.prod.yml up -d
```

### 生产环境配置

1. **环境变量**: 设置生产环境的环境变量
2. **数据库**: 配置生产数据库连接
3. **缓存**: 配置 Redis 集群
4. **监控**: 设置日志和监控
5. **安全**: 配置 HTTPS 和安全头

## 📊 API 文档

### 主要端点

- `GET /` - 根端点
- `GET /health` - 健康检查
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/assets/` - 获取资产列表
- `POST /api/v1/assets/` - 创建资产
- `GET /api/v1/portfolio/health` - 投资组合健康分析
- `WebSocket /api/v1/chat/ws` - AI 聊天 WebSocket

完整的 API 文档可在 http://localhost:8000/docs 查看。

## 🔍 监控和日志

### 健康检查端点

- `/health` - 基础健康检查
- 数据库连接检查
- Redis 连接检查
- AI 服务可用性检查

### 日志配置

应用使用结构化日志，支持：
- 请求/响应日志
- 错误追踪
- 性能监控
- 业务事件记录

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 代码规范

- 遵循 PEP 8 代码风格
- 使用 Ruff 进行代码检查
- 编写单元测试
- 更新文档

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库服务状态
   docker-compose ps postgres
   
   # 查看数据库日志
   docker-compose logs postgres
   ```

2. **Redis 连接失败**
   ```bash
   # 检查 Redis 服务
   docker-compose ps redis
   
   # 测试 Redis 连接
   redis-cli ping
   ```

3. **依赖安装问题**
   ```bash
   # 清理并重新安装
   uv sync --reinstall
   ```

4. **测试失败**
   ```bash
   # 运行详细测试
   pytest -v --tb=short
   
   # 运行特定测试
   pytest tests/test_specific.py -v
   ```

### 性能优化

- 使用数据库连接池
- 实施 Redis 缓存策略
- 优化 SQL 查询
- 使用异步处理

## 📞 支持

如有问题或建议，请：
1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue
3. 联系开发团队

---

**版本**: 0.1.0  
**最后更新**: 2026年1月8日