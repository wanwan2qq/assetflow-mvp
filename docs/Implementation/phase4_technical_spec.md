# Phase 4: 可执行方案与用户体验 - 技术方案

> **文档版本**: v1.0  
> **适用范围**: 开发者 & AI Coding Assistant  
> **预计工期**: 3 周 (W12-W14)  
> **依赖**: Phase 1-3 完成

---

## 0. 文档导读 (How to Use This Document)

### 对于开发者
- 阅读 **Section 1** 了解目标与问题诊断
- 重点关注 **Section 2** 的消息处理全流程架构
- 参考 **Section 3** 解决当前数据提取问题
- 使用 **Section 4** 实现 ActionReasoner

### 对于 AI Coding Assistant
- **问题定位时**: 参考 Section 3 的诊断清单
- **代码修复时**: 遵循 Section 2 的数据流图
- **新功能开发时**: 使用 Section 4 的设计规范

---

## 1. Phase 4 目标与原则 (Goals & Principles)

### 1.1 核心目标

| 编号 | 目标 | 说明 |
| :--- | :--- | :--- |
| **G1** | 修复数据提取链路 | 用户画像、心理分析、长期记忆正确入库 |
| **G2** | ActionReasoner 方案生成 | 基于用户资产+画像生成可执行建议 |
| **G3** | 端到端对话体验优化 | 减少废话，增加"下一步"行动引导 |
| **G4** | 家庭画像升级 | 家庭成员图谱 + 生命周期事件追踪 |

### 1.2 设计原则

| 原则 | 说明 |
| :--- | :--- |
| **数据可追溯** | 每次提取/更新记录日志和来源 |
| **链路可观测** | 关键节点增加日志和监控 |
| **渐进增强** | 新功能通过 Feature Flag 控制 |
| **用户价值优先** | 减少技术术语，增加可操作建议 |

---

## 2. 消息处理全流程架构 (Message Processing Architecture)

### 2.1 系统四层架构 (参考 backend_refactoring_plan.md)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AssetFlow 后端系统架构 (Phase 1-4)                       │
└─────────────────────────────────────────────────────────────────────────────────┘

╔═════════════════════════════════════════════════════════════════════════════════╗
║  Layer 0: API Gateway                                                           ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║   ┌──────────────────┐       ┌──────────────────┐                              ║
║   │  FastAPI         │       │  WebSocket       │                              ║
║   │  Endpoints       │       │  Handler         │                              ║
║   │  /api/*          │       │  /ws/chat/{uid}  │                              ║
║   └────────┬─────────┘       └────────┬─────────┘                              ║
║            │                          │                                         ║
╚════════════╪══════════════════════════╪═════════════════════════════════════════╝
             │                          │
             ▼                          ▼
╔═════════════════════════════════════════════════════════════════════════════════╗
║  Layer 1: Orchestration (编排层)                                                 ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║   ┌────────────────────────────────────────────────────────────────────────┐   ║
║   │           ConversationOrchestrator (Phase 1) ⭐ 核心                    │   ║
║   │                                                                        │   ║
║   │   process_message() → 7-Step 消息处理流程                              │   ║
║   │   _background_extraction_pipeline() → 后台提取                          │   ║
║   └────────────────────────────────────────────────────────────────────────┘   ║
║                                        │                                        ║
║                    ┌───────────────────┼───────────────────┐                   ║
║                    │                   │                   │                   ║
║                    ▼                   ▼                   ▼                   ║
║   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐      ║
║   │  ContextManager    │  │  ChatHistoryService│  │  ActionOrchestrator│      ║
║   │  (Phase 1)         │  │  (Phase 1)         │  │  (Phase 4) 🆕      │      ║
║   │  上下文缓存/刷新    │  │  聊天记录持久化     │  │  方案执行编排       │      ║
║   └────────────────────┘  └────────────────────┘  └────────────────────┘      ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝
             │                          │                    │
             ▼                          ▼                    ▼
╔═════════════════════════════════════════════════════════════════════════════════╗
║  Layer 2: Core Intelligence (核心智能层)                                         ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             ║
║   │  LLMProvider     │  │  RAGEngine       │  │  ActionReasoner  │             ║
║   │  (Phase 1)       │  │  (Phase 3)       │  │  (Phase 4) 🆕    │             ║
║   │                  │  │                  │  │                  │             ║
║   │  流式 LLM 调用    │  │  知识检索+规则    │  │  方案推理生成     │             ║
║   │  (DeepSeek)      │  │  增强回答         │  │  可执行建议       │             ║
║   └──────────────────┘  └──────────────────┘  └──────────────────┘             ║
║            │                     │                     │                        ║
║            │            ┌───────┴───────┐              │                        ║
║            │            ▼               ▼              │                        ║
║            │  ┌──────────────────┐  ┌──────────────────┐                       ║
║            │  │ KnowledgeRetriever│  │  RuleEngine     │                       ║
║            │  │ (Phase 3)        │  │  (Phase 3)      │                       ║
║            │  │ Hybrid Search    │  │  政策约束评估    │                       ║
║            │  └──────────────────┘  └──────────────────┘                       ║
║            │                                                                    ║
║   ┌────────┴────────┐                                                          ║
║   ▼                 ▼                                                          ║
║   ┌──────────────────┐  ┌──────────────────┐                                   ║
║   │  InformationExtractor│  │ InsightService  │                                ║
║   │  (Phase 1)       │  │  (Phase 1)       │                                   ║
║   │  资产/画像提取    │  │  心理分析        │                                   ║
║   └──────────────────┘  └──────────────────┘                                   ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝
             │                          │                    │
             ▼                          ▼                    ▼
╔═════════════════════════════════════════════════════════════════════════════════╗
║  Layer 3: Domain Services (领域服务层)                                           ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             ║
║   │ RealEstateEngine │  │ PortfolioAnalyzer│  │ FamilyProfileSvc │             ║
║   │ (Phase 2)        │  │ (Phase 2)        │  │ (Phase 4) 🆕     │             ║
║   │                  │  │                  │  │                  │             ║
║   │ 房产金融分析      │  │ 资产配置象限     │  │ 家庭成员图谱     │             ║
║   │ 杠杆/租售比       │  │ S&P 4象限模型    │  │ 生命周期事件     │             ║
║   └──────────────────┘  └──────────────────┘  └──────────────────┘             ║
║            │                     │                     │                        ║
║   ┌────────┴─────────────────────┴─────────────────────┴────────┐              ║
║   ▼                                                             ▼              ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             ║
║   │ PropertyValuation│  │ SwapSimulator    │  │ UIComponentInject│             ║
║   │ (Phase 2)        │  │ (Phase 2)        │  │ (Phase 1)        │             ║
║   │ 房产估值 (多源)   │  │ 房产置换模拟     │  │ 智能组件注入     │             ║
║   └──────────────────┘  └──────────────────┘  └──────────────────┘             ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝
             │                          │                    │
             ▼                          ▼                    ▼
╔═════════════════════════════════════════════════════════════════════════════════╗
║  Layer 4: Data & Memory (数据与记忆层)                                           ║
╠═════════════════════════════════════════════════════════════════════════════════╣
║                                                                                 ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐             ║
║   │ L1: 用户数据      │  │ L2: 认知状态     │  │ L3: 向量记忆     │             ║
║   │                  │  │                  │  │                  │             ║
║   │ - User           │  │ - UserCognition  │  │ - VectorMemory   │             ║
║   │ - UserProfile    │  │ - 心理画像       │  │ - MemoryService  │             ║
║   │ - UserAsset      │  │ - 风险偏好       │  │ - BGE Embedding  │             ║
║   │ - RealEstateAsset│  │                  │  │                  │             ║
║   │ - FamilyProfile🆕│  │                  │  │                  │             ║
║   │ - ActionPlan 🆕  │  │                  │  │                  │             ║
║   └──────────────────┘  └──────────────────┘  └──────────────────┘             ║
║            │                     │                     │                        ║
║   ┌────────┴─────────────────────┴─────────────────────┴────────┐              ║
║   ▼                                                                            ║
║   ┌──────────────────────────────────────────────────────────────────────┐     ║
║   │                 Knowledge Base (知识库 - Phase 3)                     │     ║
║   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │     ║
║   │  │PolicyKnowledge│  │ FAQKnowledge │  │ProductKnowledge│              │     ║
║   │  │ 政策知识      │  │ 常见问题     │  │ 产品知识      │              │     ║
║   │  └──────────────┘  └──────────────┘  └──────────────┘                │     ║
║   └──────────────────────────────────────────────────────────────────────┘     ║
║                                                                                 ║
║   ┌─────────────────────────────────────────────────────────────────────────┐  ║
║   │                          Storage Layer                                  │  ║
║   │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │  ║
║   │   │    Redis     │  │  PostgreSQL  │  │   pgvector   │                 │  ║
║   │   │   (缓存)      │  │  (持久化)    │  │  (向量检索)  │                 │  ║
║   │   └──────────────┘  └──────────────┘  └──────────────┘                 │  ║
║   └─────────────────────────────────────────────────────────────────────────┘  ║
║                                                                                 ║
╚═════════════════════════════════════════════════════════════════════════════════╝

Legend: 🆕 = Phase 4 新增   ⭐ = 核心入口

### 2.2 详细流程图 (7-Step Process)

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│          ConversationOrchestrator.process_message() - 7步处理流程                 │
└──────────────────────────────────────────────────────────────────────────────────┘

用户消息 ─────────────────────────────────────────────────────────────────────────▶

┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📩 STEP 0: 保存用户消息                                                          │
│   chat_history_service.save_user_message(user_id, message)                      │
│   - 消息立即入库 (chatmessage 表)                                                │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 📂 STEP 1: 加载上下文 (ContextManager.get_context)                               │
│                                                                                  │
│   ┌─ 缓存策略 ────────────────────────────────────────────────────────────────┐  │
│   │ 1. 检查 Redis 缓存 (TTL: 1小时)                                           │  │
│   │ 2. 缓存未命中 → 从 PostgreSQL 加载                                        │  │
│   │    - UserProfile, UserAsset, UserCognition, ChatSession                  │  │
│   │ 3. 构建 ConversationContext 对象                                          │  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   ConversationContext {                                                          │
│     user_id: int                                                                 │
│     conversation_history: list[dict]   ← 最近对话记录                            │
│     user_profile: UserProfile | None   ← 用户画像                                │
│     assets: list[UserAsset]            ← 资产列表                                │
│     cognition: UserCognition | None    ← 心理分析结果                            │
│     created_at: datetime                                                         │
│   }                                                                              │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 💬 STEP 2: 添加消息到上下文                                                       │
│   context.add_message("user", message)                                           │
│   context_manager.update_in_memory(user_id, context)                             │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🤖 STEP 3: 构建 LLM 输入并调用                                                    │
│                                                                                  │
│   ┌─ _get_system_prompt(context) ──────────────────────────────────────────────┐ │
│   │ 基于用户阶段选择 system prompt                                              │ │
│   │   - 初始阶段 → 信息收集型 prompt                                           │ │
│   │   - 分析阶段 → 建议生成型 prompt                                           │ │
│   └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│   ┌─ _build_messages(context) ─────────────────────────────────────────────────┐ │
│   │ 构建消息列表:                                                               │ │
│   │   1. context_summary (画像+资产摘要)                                        │ │
│   │   2. recent history (最近N轮对话)                                          │ │
│   │   3. current message                                                        │ │
│   └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│   ┌─ _build_context_summary(context) ───────────────────────────────────────────┐ │
│   │ 生成上下文摘要 (注入到 LLM):                                                │ │
│   │   "用户画像: 35岁, 已婚, 风险偏好中等 | 资产: 3项, 总值 500万"              │ │
│   └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
│   ┌─ LLMProvider.generate_stream(messages, system_prompt) ──────────────────────┐ │
│   │ 流式调用 DeepSeek API                                                       │ │
│   │   for chunk in response:                                                    │ │
│   │       full_response += chunk                                                │ │
│   │       yield chunk  ──────────────────────────▶ 实时返回给用户               │ │
│   └───────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 💾 STEP 4: 添加 AI 响应到上下文                                                   │
│   context.add_message("assistant", full_response)                               │
│   context_manager.update_in_memory(user_id, context)                             │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🎨 STEP 5: UI 组件注入 (UIComponentInjector)                                     │
│                                                                                  │
│   enhanced_response, ui_components = ui_injector.extract_and_inject(...)        │
│                                                                                  │
│   ┌─ 触发条件 ─────────────────────────────────────────────────────────────────┐  │
│   │ - 检测到资产描述 → 注入 AssetCard                                          │  │
│   │ - 检测到投资组合分析 → 注入 PortfolioChart                                 │  │
│   │ - 检测到置换方案 → 注入 SwapSimulatorCard                                  │  │
│   └───────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                  │
│   if enhanced_response != full_response:                                         │
│       yield enhanced_response[len(full_response):]  ──▶ 追加 UI 组件到响应      │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 💾 STEP 6: 保存 AI 消息                                                          │
│   chat_history_service.save_ai_message(user_id, enhanced_response)              │
└──────────────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🔄 STEP 7: 后台提取管道 (Fire-and-Forget)                                         │
│                                                                                  │
│   asyncio.create_task(_background_extraction_pipeline(message, user_id, context))│
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────────┐  │
│   │ _background_extraction_pipeline()                                          │  │
│   │                                                                            │  │
│   │   ┌─ Step A: 信息提取 ⚠️ ─────────────────────────────────────────────────┐│  │
│   │   │ _trigger_information_extraction(message, user_id, context)           ││  │
│   │   │                                                                      ││  │
│   │   │   1. extract_information(user_message, recent_history)               ││  │
│   │   │      → 返回 { assets: [...], risk_profile: {...} }                   ││  │
│   │   │                                                                      ││  │
│   │   │   2. asset_extraction_service.update_user_state(user_id, result)     ││  │
│   │   │      → 持久化到 userprofile / userasset 表                           ││  │
│   │   │                                                                      ││  │
│   │   │   ❌ 问题: user_profile 字段可能未被正确保存                          ││  │
│   │   │   ❌ 问题: MemoryService.add_memory() 未被调用                        ││  │
│   │   └──────────────────────────────────────────────────────────────────────┘│  │
│   │                                                                            │  │
│   │   ┌─ Step B: 缓存刷新 ───────────────────────────────────────────────────┐│  │
│   │   │ context_manager.invalidate(user_id)                                  ││  │
│   │   │   → 使 Redis 缓存失效，下次请求重新从 DB 加载                        ││  │
│   │   └──────────────────────────────────────────────────────────────────────┘│  │
│   │                                                                            │  │
│   │   ┌─ Step C: 心理分析 (条件触发) ⚠️ ──────────────────────────────────────┐│  │
│   │   │ _trigger_insight_analysis(user_id, context)                          ││  │
│   │   │                                                                      ││  │
│   │   │   if message_count >= 3 and message_count % 3 == 0:                  ││  │
│   │   │       insight_service.analyze_user_psychology(user_id)               ││  │
│   │   │       → 更新 usercognition 表                                        ││  │
│   │   │                                                                      ││  │
│   │   │   ❌ 问题: message_count 从 context 获取可能不准确                    ││  │
│   │   └──────────────────────────────────────────────────────────────────────┘│  │
│   └─────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────────────────────▶
                                                                         响应给用户
```

### 2.3 关键模块职责

| 模块 | 文件 | 职责 |
| :--- | :--- | :--- |
| **ConversationOrchestrator** | `conversation_orchestrator.py` | 消息处理核心编排器，7步流程 |
| **ContextManager** | `context_manager.py` | 上下文加载/缓存/刷新 |
| **LLMProvider** | `llm_caller.py` | LLM 调用封装 (DeepSeek) |
| **UIComponentInjector** | `ui_component_injector.py` | UI 组件检测与注入 |
| **InformationExtractor** | `information_extraction.py` | 资产/画像信息提取 |
| **InsightService** | `insight_service.py` | 用户心理分析 (System 2) |
| **MemoryService** | `memory_service.py` | 长期记忆 (向量存储) |
| **ChatHistoryService** | `chat_history_service.py` | 聊天记录持久化 |

### 2.4 数据存储层

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              数据存储架构                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

        ┌─────────────────┐              ┌─────────────────┐
        │   ContextManager │              │   MemoryService  │
        │   (统一入口)      │              │   (向量检索)      │
        └────────┬────────┘              └────────┬────────┘
                 │                                │
        ┌────────┴────────────────────────────────┴────────┐
        │                                                   │
        ▼                                                   ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│    Redis      │      │  PostgreSQL   │      │   pgvector    │
│   (L1 缓存)    │      │   (持久层)     │      │   (向量层)     │
├───────────────┤      ├───────────────┤      ├───────────────┤
│               │      │               │      │               │
│ context:{uid} │      │ user          │      │ vector_memory │
│   TTL: 1hr    │      │ userprofile   │      │ - user_id     │
│               │      │ userasset     │      │ - embedding   │
│               │      │ usercognition │      │ - text        │
│               │      │ chatsession   │      │ - metadata    │
│               │      │ chatmessage   │      │               │
│               │      │ action_plan   │      │ policy/faq/   │
│               │      │ family_profile│      │ product_know  │
│               │      │               │      │ ledge         │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        └──────────────────────┴──────────────────────┘
                               │
                         Cache Strategy:
                         1. Check Redis (fast)
                         2. Load from PostgreSQL
                         3. Update Redis cache

---

## 3. 问题诊断与修复方案

### 3.1 已识别问题

| 问题 | 现象 | 根因分析 |
| :--- | :--- | :--- |
| **P1** 用户画像未入库 | userprofile 表无新数据 | `extract_information` 返回格式与 `update_user_state` 期望不匹配 |
| **P2** 心理分析未执行 | usercognition 表无更新 | `_trigger_insight_analysis` 仅在 message_count % 3 == 0 时触发 |
| **P3** 长期记忆未存储 | vector_memory 表无数据 | `MemoryService.add_memory()` 未被调用 |
| **P4** 上下文未刷新 | LLM 未感知新提取数据 | 缓存刷新后下次请求才生效 |

### 3.2 修复方案

#### 3.2.1 修复信息提取链路 (P1)

**问题代码位置**: `conversation_orchestrator.py:_trigger_information_extraction`

```python
# 当前代码检查:
if extraction_result and (
    extraction_result.get("assets") or 
    extraction_result.get("risk_profile")  # ⚠️ 可能字段名不匹配
):
```

**修复方案**:
1. 统一 `extract_information` 返回格式
2. 增加显式日志记录提取内容
3. 添加 `user_profile` 字段检查

#### 3.2.2 修复心理分析触发频率 (P2)

**当前逻辑**: 每 3 条消息触发一次，但 `message_count` 从 context 获取可能不准确

**修复方案**:
1. 使用数据库记录的消息数而非缓存数
2. 增加触发条件: 检测到重要用户信息变化时强制触发

#### 3.2.3 添加长期记忆存储 (P3)

**问题**: `MemoryService.add_memory()` 未被调用

**修复方案**: 在提取管道中添加记忆存储步骤

```python
# 在 _background_extraction_pipeline 中添加:
async def _store_important_memories(self, user_id: int, extraction_result: dict):
    """存储重要信息到长期记忆"""
    from app.services.memory_service import get_memory_service
    
    memory_service = get_memory_service()
    
    # 存储提取的资产信息
    for asset in extraction_result.get("assets", []):
        await memory_service.add_memory(
            user_id=user_id,
            text=f"用户资产: {asset.get('name', '')} - {asset.get('type', '')}",
            metadata={"source": "extraction", "type": "asset"}
        )
    
    # 存储用户画像变化
    if profile := extraction_result.get("user_profile"):
        await memory_service.add_memory(
            user_id=user_id,
            text=f"用户画像更新: {profile}",
            metadata={"source": "extraction", "type": "profile"}
        )
```

### 3.3 增强的数据流监控

**新增日志点**:
```python
# 在关键节点添加结构化日志
logger.info(f"📥 [EXTRACT] user={user_id} assets={len(assets)} profile={bool(profile)}")
logger.info(f"💾 [PERSIST] user={user_id} saved_assets={len(saved)} saved_profile={bool(saved_profile)}")
logger.info(f"🧠 [MEMORY] user={user_id} memories_added={len(memories)}")
logger.info(f"🎯 [INSIGHT] user={user_id} analyzed={success}")
```

---

## 4. ActionReasoner 设计 (可执行方案生成器)

### 4.1 ActionPlan 数据模型

**文件**: `backend/app/models/action_plan.py`

```python
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import JSON
from sqlmodel import Field as SQLField, SQLModel


class ActionPriority(str, Enum):
    """行动优先级"""
    HIGH = "high"       # 立即行动
    MEDIUM = "medium"   # 近期行动 (1-3个月)
    LOW = "low"         # 长期规划

class ActionCategory(str, Enum):
    """行动类别"""
    ASSET_ALLOCATION = "asset_allocation"   # 资产配置
    INSURANCE = "insurance"                 # 保险规划
    REAL_ESTATE = "real_estate"             # 房产相关
    INVESTMENT = "investment"               # 投资建议
    DEBT_MANAGEMENT = "debt_management"     # 负债管理
    TAX_PLANNING = "tax_planning"           # 税务规划


class ActionStep(BaseModel):
    """单个行动步骤"""
    step_number: int
    action: str                             # 具体行动描述
    expected_outcome: str                   # 预期效果
    timeline: str                           # 时间建议
    dependencies: list[str] = []            # 前置条件
    resources: list[str] = []               # 需要的资源/文件


class ActionPlan(SQLModel, table=True):
    """
    可执行方案
    
    基于用户资产+画像+知识库推理生成的个性化行动建议
    """
    __tablename__ = "action_plan"
    
    id: int | None = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="user.id")
    
    # 方案基本信息
    title: str                              # 方案标题
    category: ActionCategory
    priority: ActionPriority
    summary: str                            # 一句话摘要
    
    # 方案内容
    steps: list[dict] = SQLField(sa_column=JSON)  # ActionStep 列表
    expected_benefits: list[str] = SQLField(sa_column=JSON)  # 预期收益
    potential_risks: list[str] = SQLField(sa_column=JSON)    # 潜在风险
    
    # 数据依据
    based_on_assets: list[int] = SQLField(sa_column=JSON, default=[])  # 关联资产ID
    based_on_knowledge: list[int] = SQLField(sa_column=JSON, default=[])  # 关联知识ID
    
    # 状态跟踪
    status: str = SQLField(default="pending")  # pending/in_progress/completed/dismissed
    completed_steps: list[int] = SQLField(sa_column=JSON, default=[])
    
    # 元数据
    confidence: float = SQLField(default=0.5)
    created_at: datetime = SQLField(default_factory=datetime.utcnow)
    updated_at: datetime = SQLField(default_factory=datetime.utcnow)
```

### 4.2 ActionReasoner 服务

**文件**: `backend/app/services/action_reasoner.py`

**职责**:
- 分析用户资产配置
- 结合用户画像生成个性化建议
- 调用 RAG 知识库增强推理
- 生成可执行的 ActionPlan

**关键方法**:
```python
class ActionReasoner:
    """
    可执行方案推理器
    
    基于用户资产、画像和知识库生成个性化行动建议
    """
    
    async def generate_plan(
        self,
        user_id: int,
        focus_area: ActionCategory | None = None
    ) -> list[ActionPlan]:
        """
        生成可执行方案
        
        流程:
        1. 加载用户资产和画像
        2. 分析资产配置问题 (PortfolioAnalyzer)
        3. 检索相关知识 (RAGEngine)
        4. 使用 LLM 推理生成方案
        5. 存储并返回 ActionPlan
        """
    
    async def analyze_gaps(
        self,
        user_id: int
    ) -> dict:
        """
        分析用户资产配置缺口
        
        Returns:
            {
                "insurance_gap": [...],      # 保险缺口
                "emergency_fund_gap": ...,   # 应急金缺口
                "investment_suggestions": [...],
                "debt_optimization": [...]
            }
        """
    
    async def prioritize_actions(
        self,
        plans: list[ActionPlan]
    ) -> list[ActionPlan]:
        """根据紧迫性和影响度排序"""
```

### 4.3 ActionReasoner Prompt

**文件**: `prompts/action/action_plan_generator.yaml`

```yaml
system_instruction: |
  你是一位专业的家庭财务规划师。请基于用户的资产状况和个人画像，生成可执行的行动方案。

  ## 用户资产概况
  {{ asset_summary }}

  ## 用户画像
  {{ user_profile }}

  ## 相关知识参考
  {{ knowledge_context }}

  ## 需要分析的方向
  {{ focus_area }}

  ## 输出要求
  请生成一个具体的行动方案，包含:
  1. 方案标题 (一句话说明目标)
  2. 3-5个具体步骤 (每步包含: 具体行动、预期效果、时间建议)
  3. 预期收益 (2-3点)
  4. 潜在风险 (1-2点)
  5. 置信度评估 (0-1)

  请返回 JSON 格式:
  {
      "title": "...",
      "category": "asset_allocation|insurance|real_estate|...",
      "priority": "high|medium|low",
      "summary": "...",
      "steps": [
          {
              "step_number": 1,
              "action": "...",
              "expected_outcome": "...",
              "timeline": "...",
              "dependencies": [],
              "resources": []
          }
      ],
      "expected_benefits": ["..."],
      "potential_risks": ["..."],
      "confidence": 0.8
  }

metadata:
  version: "1.0"
  category: "action"
  description: "可执行方案生成"
```

---

## 5. FamilyProfileService 设计

### 5.1 家庭成员模型

```python
class FamilyMember(BaseModel):
    """家庭成员"""
    relation: str           # self/spouse/child/parent
    age: int | None
    occupation: str | None
    income: float | None
    insurance_coverage: list[str] = []
    special_needs: list[str] = []


class LifecycleEvent(BaseModel):
    """生命周期事件"""
    event_type: str         # marriage/child_birth/retirement/education
    expected_date: str | None
    financial_impact: float | None
    notes: str | None


class FamilyProfile(SQLModel, table=True):
    """家庭画像"""
    __tablename__ = "family_profile"
    
    id: int | None
    user_id: int
    members: list[dict]     # FamilyMember 列表
    lifecycle_events: list[dict]  # LifecycleEvent 列表
    total_income: float | None
    total_expenses: float | None
    financial_goals: list[str]
```

---

## 6. Feature Flag 配置

**文件**: `backend/app/core/config.py`

```python
class Settings(BaseSettings):
    # Phase 4: ActionReasoner Feature Flags
    ENABLE_ACTION_REASONER: bool = True
    ENABLE_FAMILY_PROFILE: bool = True
    ENABLE_MEMORY_STORAGE: bool = True          # 新增: 长期记忆存储
    ENABLE_ENHANCED_EXTRACTION: bool = True     # 新增: 增强信息提取
    ACTION_PLAN_AUTO_GENERATE: bool = False     # 自动生成行动计划
```

---

## 7. 验收清单 (Acceptance Checklist)

### Week 12 验收
- [ ] 修复 `extract_information` 返回格式
- [ ] 修复 `update_user_state` 数据持久化
- [ ] 添加 `MemoryService.add_memory` 调用
- [ ] 增加数据流日志监控

### Week 13 验收
- [ ] `ActionPlan` 数据模型创建
- [ ] `ActionReasoner.generate_plan()` 实现
- [ ] `FamilyProfileService` 实现

### Week 14 验收
- [ ] 端到端对话测试
- [ ] 减少废话建议占比 ≤ 20%
- [ ] 行动建议可执行性评估

---

## 附录: AI Coding 快速参考

### 关键文件
```
backend/app/
├── services/
│   ├── conversation_orchestrator.py  # 消息处理核心 ⭐
│   ├── information_extraction.py     # 信息提取
│   ├── asset_extraction_service.py   # 资产持久化
│   ├── insight_service.py            # 心理分析
│   ├── memory_service.py             # 长期记忆
│   ├── action_reasoner.py            # 方案生成 (NEW)
│   └── family_profile.py             # 家庭画像 (NEW)
├── models/
│   └── action_plan.py                # 方案模型 (NEW)
└── prompts/
    └── action/
        └── action_plan_generator.yaml # 方案提示词 (NEW)
```

### 调试命令
```bash
# 查看信息提取日志
grep "📥 \[EXTRACT\]" backend.log

# 查看数据持久化日志
grep "💾 \[PERSIST\]" backend.log

# 查看记忆存储日志
grep "🧠 \[MEMORY\]" backend.log
```
