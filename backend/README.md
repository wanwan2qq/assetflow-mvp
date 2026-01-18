# AssetFlow Backend

AssetFlow后端是一个AI驱动的家庭资产配置顾问系统，基于FastAPI构建，采用双进程认知架构和4层记忆系统，提供智能对话式资产管理服务。

## 🚀 核心特性

### AI对话引擎
- **LangChain集成**: 使用DeepSeek/OpenAI进行自然语言理解
- **流式响应**: WebSocket + SSE实时流式输出
- **思维链推理**: Chain of Thought内部推理过程
- **上下文感知**: Fact Sheet + 对话历史 + 向量记忆

### 双进程认知架构
**System 1 (快速思考 - 即时一致性)**
- 信息提取: LLM驱动的结构化数据提取
- 数据库写入: 更新L1/L2层数据
- 上下文刷新: 确保AI立即看到新数据
- 延迟: ~600ms (阻塞，必须完成)

**System 2 (慢速思考 - 最终一致性)**
- 心理洞察: 分析用户心理特征和决策风格
- 向量记忆: 生成嵌入并存储到向量数据库
- 延迟: ~2-5s (异步，不阻塞响应)

### 4层记忆架构
```
L0 (对话历史) ← 滑动窗口，防止上下文断裂
L1 (结构化事实) ← 资产、用户画像（即时一致性）
L2 (认知状态) ← 采集状态、财务目标（即时一致性）
L3 (心理洞察) ← 风险偏好、决策风格（最终一致性）
L4 (向量记忆) ← 语义搜索、长期记忆（最终一致性）
```

### Phase 4: 向量记忆 (Vector Memory)
- **长期记忆**: pgvector驱动的语义记忆存储
- **RAG集成**: 检索增强生成，上下文感知对话
- **本地嵌入**: BAAI/bge-large-zh-v1.5 (1024维)
- **语义搜索**: 余弦相似度搜索，智能记忆召回
- **优雅降级**: 嵌入失败时使用关键词搜索

### 投资组合分析
- **标准普尔四象限模型**: 要花的钱、保命的钱、生钱的钱、保本升值的钱
- **动态配置建议**: 基于年龄、家庭、风险偏好的个性化调整
- **风险预警**: 房产占比、流动性、保险、负债分析
- **健康度评分**: 综合评估投资组合健康状况

## 🛠 技术栈

- **框架**: FastAPI 0.104+ (异步高性能)
- **Python**: 3.11+
- **数据库**: PostgreSQL 16 + pgvector
- **ORM**: SQLModel (类型安全)
- **缓存**: Redis 7
- **认证**: JWT (python-jose)
- **AI**: LangChain + DeepSeek/OpenAI
- **嵌入模型**: BAAI/bge-large-zh-v1.5 (1024维，本地)
- **向量搜索**: pgvector HNSW索引
- **搜索**: Tavily API (实时信息检索)
- **测试**: pytest + hypothesis (属性测试)
- **代码质量**: Ruff (格式化和检查)
- **包管理**: uv (快速Python包管理器)

## 📋 环境要求

- Python 3.11+
- PostgreSQL 16+ (with pgvector extension)
- Redis 7+
- Docker & Docker Compose (可选)

## 🚀 快速开始

### 1. 环境设置

```bash
# 克隆项目
cd backend

# 初始化数据库（包含 pgvector）
python init_phase4_db.py

# 验证 Phase 4 安装
python verify_phase4.py

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
├── app/                       # 应用主目录
│   ├── api/                  # API路由
│   │   └── api_v1/           # API v1版本
│   │       ├── auth.py       # 认证端点 (登录、验证码)
│   │       ├── assets.py     # 资产管理端点
│   │       ├── chat.py       # WebSocket聊天端点
│   │       ├── profile.py    # 用户画像端点
│   │       └── recommendations.py  # 推荐端点
│   ├── core/                 # 核心配置和工具
│   │   ├── config.py         # 应用配置 (环境变量)
│   │   ├── database.py       # 数据库配置 (SQLModel)
│   │   ├── auth.py           # JWT认证
│   │   ├── error_handling.py # 全局错误处理
│   │   └── responses.py      # 标准响应格式
│   ├── models/               # 数据模型 (SQLModel)
│   │   ├── user.py           # User, UserProfile, UserAsset
│   │   ├── cognition.py      # UserCognition (L2/L3)
│   │   ├── memory.py         # VectorMemory (L4)
│   │   ├── chat.py           # ChatMessage (L0)
│   │   ├── interaction.py    # UserInteraction
│   │   ├── commercial.py     # CommercialProduct
│   │   └── audit.py          # AuditLog
│   ├── services/             # 业务逻辑服务
│   │   ├── chat_agent.py     # 核心AI对话引擎
│   │   ├── memory_service.py # 向量记忆服务 (L4)
│   │   ├── insight_service.py # 心理洞察分析 (L3)
│   │   ├── information_extraction.py  # LLM信息提取
│   │   ├── asset_extraction_service.py  # 资产提取和存储
│   │   ├── portfolio_analyzer.py  # 投资组合分析
│   │   ├── recommendation_service.py  # 推荐系统
│   │   ├── chat_history_service.py  # 聊天历史管理
│   │   ├── profile_asset_service.py  # 用户画像服务
│   │   ├── search_tools.py   # 搜索工具 (Tavily)
│   │   ├── ui_component_service.py  # UI组件生成
│   │   ├── sms_service.py    # SMS验证码服务
│   │   └── audit.py          # 审计日志服务
│   ├── utils/                # 工具函数
│   └── main.py               # FastAPI应用入口
├── alembic/                  # 数据库迁移
│   ├── env.py                # Alembic配置
│   ├── script.py.mako        # 迁移脚本模板
│   └── versions/             # 迁移版本
│       ├── eb0a9c8ddf6e_initial_migration.py
│       ├── phase4_enable_pgvector_extension.py
│       └── phase4_add_vector_memory_table.py
├── tests/                    # 测试文件
│   ├── conftest.py           # pytest配置
│   ├── test_auth_system.py   # 认证测试
│   ├── test_chat_websocket_integration.py  # WebSocket测试
│   ├── test_e2e_core_functionality.py  # E2E测试
│   ├── test_portfolio_analyzer.py  # 投资组合测试
│   └── test_*_properties.py  # 属性测试 (hypothesis)
├── scripts/                  # 工具脚本
│   ├── init_phase4_db.py     # 初始化pgvector数据库
│   ├── verify_phase4.py      # 验证Phase 4安装
│   ├── test_*.py             # 各种测试脚本
│   └── debug/                # 调试脚本
├── docker-compose.yml        # Docker配置
├── Dockerfile.dev            # 开发环境Docker
├── pyproject.toml            # 项目配置 (uv)
├── alembic.ini               # Alembic配置
└── README.md                 # 本文档
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

**认证**
- `POST /api/v1/auth/send-sms` - 发送验证码
- `POST /api/v1/auth/login` - 手机号登录
- `POST /api/v1/auth/login/device` - 设备ID登录
- `POST /api/v1/auth/bind-phone` - 绑定手机号

**资产管理**
- `GET /api/v1/assets/` - 获取资产列表
- `POST /api/v1/assets/` - 创建资产
- `PUT /api/v1/assets/{asset_id}` - 更新资产
- `DELETE /api/v1/assets/{asset_id}` - 删除资产
- `POST /api/v1/assets/{asset_id}/confirm` - 确认资产

**用户画像**
- `GET /api/v1/profile/` - 获取用户画像
- `PUT /api/v1/profile/` - 更新用户画像
- `GET /api/v1/profile/completeness` - 获取信息完整度

**投资组合**
- `GET /api/v1/portfolio/health` - 投资组合健康分析
- `GET /api/v1/portfolio/summary` - 投资组合摘要

**AI聊天**
- `WebSocket /api/v1/chat/ws/chat/{user_id}` - WebSocket聊天连接
- `GET /api/v1/chat/history` - 获取聊天历史
- `DELETE /api/v1/chat/history` - 清空聊天历史

**推荐系统**
- `GET /api/v1/recommendations/` - 获取推荐产品
- `POST /api/v1/recommendations/track` - 跟踪用户交互

**健康检查**
- `GET /` - 根端点
- `GET /health` - 健康检查

完整的API文档可在 http://localhost:8000/docs 查看 (Swagger UI)。

## 🧠 核心服务详解

### 1. ChatAgent (chat_agent.py)

**职责**: 核心AI对话引擎

**关键方法**:
```python
async def process_message(
    message: str, 
    user_id: int, 
    user_profile: UserProfile | None = None
) -> AsyncIterator[str]:
    """处理用户消息并返回流式响应"""
    # 1. 构建上下文 (Fact Sheet + 对话历史 + 向量记忆)
    # 2. 调用LLM生成响应 (流式)
    # 3. 过滤思维链 (<Thought>块)
    # 4. 生成UI组件
    # 5. System 1: 提取信息 + 刷新上下文
    # 6. System 2: 心理洞察 + 向量记忆 (异步)
```

**特性**:
- Fact Sheet生成: 防止AI幻觉
- 思维链推理: Chain of Thought内部推理
- 上下文刷新: 确保AI记住用户说的话
- 动态UI生成: 估值卡片、行动卡片、图表

### 2. MemoryService (memory_service.py)

**职责**: L4向量记忆管理

**关键方法**:
```python
async def add_memory(
    user_id: int, 
    text: str, 
    metadata: dict | None = None
) -> VectorMemory | None:
    """添加新记忆到向量存储"""
    # 1. 生成嵌入 (BGE模型)
    # 2. 存储到VectorMemory表
    # 3. 返回记忆对象

async def retrieve_relevant(
    user_id: int, 
    query_text: str, 
    limit: int = 3,
    similarity_threshold: float = 0.7
) -> list[dict]:
    """检索相关记忆 (语义搜索)"""
    # 1. 生成查询嵌入
    # 2. pgvector余弦相似度搜索
    # 3. 返回相关记忆列表
```

**技术细节**:
- 嵌入模型: BAAI/bge-large-zh-v1.5 (1024维)
- 向量数据库: pgvector
- 索引: HNSW (快速近似搜索)
- 优雅降级: 嵌入失败时使用关键词搜索

### 3. InsightService (insight_service.py)

**职责**: L3心理洞察分析

**关键方法**:
```python
async def analyze_user_psychology(
    user_id: int
) -> dict:
    """分析用户心理特征"""
    # 1. 获取最近对话历史
    # 2. 调用LLM分析心理特征
    # 3. 更新UserCognition.risk_profile
    # 4. 生成顾问策略笔记
```

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

### 4. InformationExtraction (information_extraction.py)

**职责**: LLM驱动的信息提取

**关键方法**:
```python
async def extract_information(
    user_message: str,
    conversation_history: list[dict]
) -> dict:
    """从对话中提取结构化信息"""
    # 1. 构建提取提示词
    # 2. 调用LLM提取
    # 3. 解析JSON结果
    # 4. 返回提取结果
```

**提取内容**:
- 资产: 类型、金额、位置、面积
- 用户画像: 年龄、家庭、职业、收入、风险偏好
- 财务目标: 退休、购房、教育、财富增长
- 采集状态: 各类资产的采集完成度

### 5. PortfolioAnalyzer (portfolio_analyzer.py)

**职责**: 投资组合分析

**关键方法**:
```python
def analyze_portfolio(
    assets: list[UserAsset],
    profile: UserProfile | None = None
) -> PortfolioAnalysis:
    """分析投资组合健康度"""
    # 1. 计算净资产
    # 2. 分析资产分布
    # 3. 标准普尔四象限分析
    # 4. 风险预警
    # 5. 生成建议
```

**分析指标**:
- 净资产: 总资产 - 总负债
- 房产占比: 房产价值 / 总资产
- 流动性比率: 现金 / 月支出
- 四象限配置: 当前 vs 理想
- 风险等级: low / medium / high / critical

## 🔍 关键技术实现

### 上下文刷新机制 (Context Refresh)

**问题**: AI不记得用户刚说的话
```python
# 用户: "我35岁"
# AI: "为了更好地建议，请问您多大年纪？" ❌
```

**解决方案**: 在System 1完成后立即刷新上下文
```python
async def _refresh_context_from_db(
    user_id: int, 
    context: ChatContext
) -> None:
    """从数据库刷新上下文"""
    # 1. 重新加载UserProfile
    profile = await db.get(UserProfile, user_id)
    context.user_profile = profile.to_dict()
    
    # 2. 重新加载UserAssets
    assets = await db.get_all(UserAsset, user_id)
    context.extracted_assets = [a.to_dict() for a in assets]
    
    # 3. 重新加载UserCognition
    cognition = await db.get(UserCognition, user_id)
    context.current_stage = calculate_stage(cognition)
```

**效果**: AI立即记住用户提供的信息
```python
# 用户: "我35岁"
# AI: "基于您35岁的年龄，我建议..." ✅
```

### Fact Sheet生成

**目的**: 防止AI幻觉，确保基于事实回答

**实现**:
```python
async def _generate_fact_sheet(user_id: int) -> str:
    """生成用户信息事实表"""
    # 1. 从数据库加载所有确认的数据
    profile = await db.get(UserProfile, user_id)
    assets = await db.get_all(UserAsset, user_id)
    cognition = await db.get(UserCognition, user_id)
    
    # 2. 格式化为结构化文本
    fact_sheet = f"""
    【用户基本画像】
    • 年龄段: {profile.age_range}岁
    • 家庭结构: {profile.family_structure}
    • 职业: {profile.occupation}
    • 收入范围: {profile.income_range}
    
    【资产清单】
    1. [房产] {asset.name} | 估值: {asset.value}万 | 位置: {asset.location}
    2. [现金] {asset.value}万
    ...
    
    [重要提示] 请基于以上已确认的用户信息回答问题，严禁编造数据。
    """
    
    return fact_sheet
```

### 思维链过滤 (Thought Filter)

**目的**: 隐藏AI的内部推理过程，只显示最终回复

**实现**:
```python
def _filter_thought_blocks(text: str) -> tuple[str, str]:
    """过滤<Thought>块"""
    import re
    
    # 提取思维链内容 (用于日志)
    thought_pattern = r'<Thought>(.*?)</Thought>'
    thought_matches = re.findall(thought_pattern, text, re.DOTALL)
    thought_content = "\n---\n".join(thought_matches)
    
    # 从响应中移除思维链
    filtered_text = re.sub(thought_pattern, '', text, flags=re.DOTALL)
    
    # 清理多余空白
    filtered_text = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_text).strip()
    
    return filtered_text, thought_content
```

**效果**:
- 用户看到: 简洁的回复
- 日志记录: 完整的推理过程

### 向量搜索 (Vector Search)

**实现**:
```python
async def retrieve_relevant(
    user_id: int,
    query_text: str,
    limit: int = 3,
    similarity_threshold: float = 0.7
) -> list[dict]:
    """语义搜索相关记忆"""
    # 1. 生成查询嵌入
    query_embedding = self.embeddings.embed_query(query_text)
    
    # 2. pgvector余弦相似度搜索
    query = text("""
        SELECT 
            id, content, metadata, created_at,
            1 - (embedding <=> :embedding::vector) as similarity
        FROM vector_memory
        WHERE user_id = :user_id
            AND embedding IS NOT NULL
            AND 1 - (embedding <=> :embedding::vector) >= :threshold
        ORDER BY embedding <=> :embedding::vector
        LIMIT :limit
    """)
    
    result = await session.execute(query, {
        'embedding': str(query_embedding),
        'user_id': user_id,
        'threshold': similarity_threshold,
        'limit': limit
    })
    
    return [dict(row) for row in result]
```

**优势**:
- 语义理解: "房贷压力" 能匹配 "月供负担重"
- 快速搜索: HNSW索引，毫秒级响应
- 优雅降级: 嵌入失败时使用关键词搜索

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