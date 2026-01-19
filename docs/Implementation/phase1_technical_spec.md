# Phase 1: 架构解耦与基础夯实 - 技术方案

> **文档版本**: v1.0  
> **适用范围**: 开发者 & AI Coding Assistant  
> **预计工期**: 4 周 (W1-W4)

---

## 0. 文档导读 (How to Use This Document)

### 对于开发者
- 阅读 **Section 1-4** 了解模块职责与关键实现要点
- 参考 **Section 5** 的代码示例进行开发
- 使用 **Section 6** 的验收清单进行自测

### 对于 AI Coding Assistant
- **任务拆解时**: 参考 Section 2 的模块边界定义
- **代码生成时**: 遵循 Section 3 的接口契约和命名规范
- **重构代码时**: 使用 Section 4 的迁移映射表

---

## 1. Phase 1 目标与原则 (Goals & Principles)

### 1.1 核心目标
1. **拆解 `ChatAgent` 上帝类** → 3 个职责单一的模块
2. **隔离 Mock 逻辑** → 通过接口抽象，Mock 实现与生产代码分离
3. **解决 Stale Context** → 新 `ContextManager` 替代 Plan E workaround
4. **稳定 LLM 输出** → Pydantic Structured Output 校验层
5. **提升测试覆盖** → 核心服务单元测试 > 70%

### 1.2 设计原则
| 原则 | 说明 |
| :--- | :--- |
| **单一职责 (SRP)** | 每个类/模块只负责一件事 |
| **依赖倒置 (DIP)** | 依赖抽象接口，不依赖具体实现 |
| **开闭原则 (OCP)** | 对扩展开放，对修改关闭 |
| **向后兼容** | Phase 1 结束，所有现有 API 表现不变 |

---

## 2. 模块拆解方案 (Module Breakdown)

### 2.1 从 `ChatAgent` 拆分的目标模块

```
原 ChatAgent (1677 lines)
    │
    ├──▶ ConversationOrchestrator (会话编排器)
    │       负责: 管理对话流程、调度各服务、维护上下文
    │
    ├──▶ LLMCaller (LLM 调用器)
    │       负责: 封装 LLM API 调用、流式输出、重试逻辑
    │
    ├──▶ UIComponentInjector (UI 组件注入器)
    │       负责: 解析 LLM 输出、生成前端 UI 组件
    │
    └──▶ ContextManager (上下文管理器) [新增]
            负责: 管理用户会话状态、替代 Plan E 机制
```

### 2.2 模块职责详解

#### 2.2.1 ConversationOrchestrator
**文件**: `backend/app/services/conversation_orchestrator.py` (新建)

**职责**:
- 接收用户消息，调度处理流程
- 调用 `ContextManager` 获取/更新上下文
- 调用 `LLMCaller` 生成回复
- 调用 `UIComponentInjector` 注入 UI 组件
- 触发后台信息提取任务

**关键方法**:
```python
class ConversationOrchestrator:
    async def process_message(
        self, 
        user_id: int, 
        message: str
    ) -> AsyncIterator[str]:
        """主入口: 处理用户消息并返回流式响应"""
        
    async def _build_prompt_context(
        self, 
        user_id: int
    ) -> dict:
        """构建 Prompt 上下文 (用户画像 + 资产 + 记忆)"""
```

**AI Coding 指引**:
- 不要在此类中直接调用 OpenAI API，使用 `LLMCaller`
- 不要在此类中处理 JSON 字段的 ORM 问题，由 `ContextManager` 封装
- 保持此类为"调度者"角色，不实现具体业务逻辑

---

#### 2.2.2 LLMCaller
**文件**: `backend/app/services/llm_caller.py` (新建)

**职责**:
- 封装所有 LLM API 调用
- 处理流式输出
- 实现重试和降级逻辑
- 过滤 `<Thought>` 思维链内容

**接口定义**:
```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """LLM 提供者抽象接口 - 用于依赖注入"""
    
    @abstractmethod
    async def generate_stream(
        self, 
        messages: list[dict], 
        system_prompt: str
    ) -> AsyncIterator[str]:
        """生成流式响应"""
        
    @abstractmethod
    async def generate(
        self, 
        messages: list[dict], 
        system_prompt: str
    ) -> str:
        """生成完整响应"""


class DeepSeekProvider(LLMProvider):
    """DeepSeek 实现"""
    pass


class MockLLMProvider(LLMProvider):
    """Mock 实现 - 用于开发和测试"""
    pass
```

**AI Coding 指引**:
- Mock 逻辑只能出现在 `MockLLMProvider` 中
- 生产代码中通过 `settings.USE_MOCK_LLM` 选择 Provider
- 所有 `<Thought>` 过滤逻辑集中在 `_filter_thought_blocks()` 方法

---

#### 2.2.3 UIComponentInjector
**文件**: `backend/app/services/ui_component_injector.py` (新建)

**职责**:
- 解析 LLM 输出文本
- 识别需要渲染为 UI 组件的内容
- 调用 `UIComponentService` 生成组件数据
- 将组件数据注入响应

**关键方法**:
```python
class UIComponentInjector:
    def extract_and_inject(
        self, 
        llm_response: str, 
        context: dict
    ) -> tuple[str, list[UIComponent]]:
        """从 LLM 响应中提取并注入 UI 组件"""
```

**AI Coding 指引**:
- 此模块是对现有 `extract_ui_components` 方法的封装
- 与 `UIComponentService` 的关系: Injector 负责"何时注入"，Service 负责"如何生成"

---

#### 2.2.4 ContextManager
**文件**: `backend/app/services/context_manager.py` (新建)

**职责**:
- 替代 Plan E 中的 `_refresh_context_from_db` workaround
- 管理用户会话状态 (内存 + 持久化)
- 封装 JSON 字段的 ORM 问题 (`flag_modified`)
- 提供一致的上下文读写接口

**关键特性**:
```python
class ContextManager:
    def __init__(self, cache_backend: CacheBackend = None):
        """支持可选的缓存后端 (Redis/Memory)"""
        
    async def get_context(self, user_id: int) -> ConversationContext:
        """获取用户上下文 (优先从缓存，然后 DB)"""
        
    async def update_context(
        self, 
        user_id: int, 
        updates: dict
    ) -> None:
        """更新上下文 (同时更新缓存和 DB)"""
        
    async def invalidate(self, user_id: int) -> None:
        """主动失效缓存 (信息提取完成后调用)"""
```

**AI Coding 指引**:
- 所有 `flag_modified` 调用都封装在此类内部
- 缓存失效策略: 写操作自动失效，读操作优先缓存
- 不要在其他服务中直接操作 `UserCognition.collection_status`

---

## 3. 接口契约与数据结构 (Interface Contracts)

### 3.1 核心数据结构

```python
# backend/app/models/context.py (新建)

from pydantic import BaseModel
from typing import Any

class ConversationContext(BaseModel):
    """会话上下文 - 统一的上下文数据结构"""
    
    user_id: int
    session_id: str | None = None
    
    # 对话历史 (最近 N 条)
    conversation_history: list[dict[str, str]] = []
    
    # 用户画像 (来自 L1 UserProfile)
    user_profile: dict[str, Any] | None = None
    
    # 已提取资产 (来自 L1 UserAsset)
    extracted_assets: list[dict[str, Any]] = []
    
    # 认知状态 (来自 L2 UserCognition)
    cognition: dict[str, Any] | None = None
    
    # 当前阶段
    current_stage: str = "initial"
    
    # 相关记忆 (来自 L3 VectorMemory, 可选)
    relevant_memories: list[str] = []
```

### 3.2 依赖注入配置

```python
# backend/app/core/dependencies.py (新建)

from functools import lru_cache
from app.core.config import settings
from app.services.llm_caller import LLMProvider, DeepSeekProvider, MockLLMProvider

@lru_cache()
def get_llm_provider() -> LLMProvider:
    """获取 LLM Provider 实例 (单例)"""
    if settings.USE_MOCK_LLM:
        return MockLLMProvider()
    return DeepSeekProvider(api_key=settings.OPENAI_API_KEY)
```

---

## 4. 迁移映射表 (Migration Mapping)

### 4.1 代码迁移对照

| 原代码位置 (`chat_agent.py`) | 目标模块 | 迁移说明 |
| :--- | :--- | :--- |
| `ChatAgent.__init__` | 拆分 | LLM 初始化 → `LLMCaller`; 服务初始化 → `Orchestrator` |
| `ChatAgent.process_message` | `ConversationOrchestrator.process_message` | 保持签名兼容 |
| `ChatAgent._process_message_mock` | `MockLLMProvider.generate_stream` | Mock 逻辑隔离 |
| `ChatAgent._filter_thought_blocks` | `LLMCaller._filter_thought_blocks` | 保持逻辑不变 |
| `ChatAgent._generate_mock_response` | `MockLLMProvider._generate_response` | Mock 逻辑隔离 |
| `ChatAgent._enhance_response_with_ui_components` | `UIComponentInjector.extract_and_inject` | 提取为独立模块 |
| `ChatAgent._refresh_context_from_db` | `ContextManager.get_context` | 核心逻辑升级 |
| `ChatAgent._background_extraction_pipeline` | `ConversationOrchestrator._trigger_background_tasks` | 保持后台执行 |
| `ChatAgent.contexts` (内存字典) | `ContextManager` (缓存层) | 升级为可配置缓存 |

### 4.2 文件变更清单

| 操作 | 文件路径 | 说明 |
| :--- | :--- | :--- |
| **新建** | `services/conversation_orchestrator.py` | 会话编排器 |
| **新建** | `services/llm_caller.py` | LLM 调用器 + Provider 接口 |
| **新建** | `services/ui_component_injector.py` | UI 组件注入器 |
| **新建** | `services/context_manager.py` | 上下文管理器 |
| **新建** | `models/context.py` | 上下文数据结构 |
| **新建** | `core/dependencies.py` | 依赖注入配置 |
| **修改** | `services/chat_agent.py` | 重构为 Facade，调用新模块 |
| **修改** | `api/api_v1/endpoints/chat.py` | 保持不变 (调用 `get_chat_agent`) |
| **修改** | `core/config.py` | 添加 `USE_MOCK_LLM` 配置 |

---

## 5. 代码示例 (Code Examples)

### 5.1 重构后的 ChatAgent (Facade 模式)

```python
# backend/app/services/chat_agent.py (重构后)

"""
ChatAgent - 重构为 Facade 模式
保持对外接口不变，内部委托给新模块
"""

from app.services.conversation_orchestrator import ConversationOrchestrator
from app.core.dependencies import get_llm_provider

class ChatAgent:
    """ChatAgent Facade - 保持向后兼容"""
    
    def __init__(self):
        llm_provider = get_llm_provider()
        self._orchestrator = ConversationOrchestrator(llm_provider)
    
    async def process_message(
        self, 
        message: str, 
        user_id: int, 
        user_profile=None
    ):
        """保持原签名，委托给 Orchestrator"""
        async for chunk in self._orchestrator.process_message(user_id, message):
            yield chunk
    
    def extract_ui_components(self, response: str):
        """保持原方法，委托给 UIComponentInjector"""
        return self._orchestrator.ui_injector.extract_components(response)
    
    # ... 其他方法保持签名，委托实现
```

### 5.2 LLM Provider 接口实现

```python
# backend/app/services/llm_caller.py

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from langchain_openai import ChatOpenAI
from app.core.config import settings

class LLMProvider(ABC):
    @abstractmethod
    async def generate_stream(self, messages: list, system_prompt: str) -> AsyncIterator[str]:
        pass


class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=api_key,
            base_url=settings.OPENAI_API_BASE,
            streaming=True
        )
    
    async def generate_stream(self, messages: list, system_prompt: str) -> AsyncIterator[str]:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        async for chunk in self.llm.astream(full_messages):
            if hasattr(chunk, "content") and chunk.content:
                yield chunk.content


class MockLLMProvider(LLMProvider):
    """开发环境 Mock 实现"""
    
    async def generate_stream(self, messages: list, system_prompt: str) -> AsyncIterator[str]:
        # 从原 _generate_mock_response 迁移
        mock_response = self._generate_mock_response(messages[-1]["content"])
        for word in mock_response.split():
            yield word + " "
    
    def _generate_mock_response(self, message: str) -> str:
        # 原 ChatAgent._generate_mock_response 代码迁移至此
        ...
```

---

## 6. 验收清单 (Acceptance Checklist)

### Week 1 验收
- [ ] `ConversationOrchestrator` 模块创建并可编译
- [ ] `LLMCaller` + `LLMProvider` 接口定义完成
- [ ] `MockLLMProvider` 实现并通过基础测试
- [ ] 原 `ChatAgent` 改为 Facade，所有现有测试通过

### Week 2 验收
- [ ] `ContextManager` 模块创建
- [ ] Stale Context 问题验证修复 (用户连续输入信息，AI 能立即感知)
- [ ] JSON 字段更新逻辑封装在 `ContextManager` 内部
- [ ] Redis 缓存集成 (可选，支持降级到内存)

### Week 3 验收
- [ ] `UIComponentInjector` 模块创建
- [ ] LLM 输出增加 Pydantic 校验层
- [ ] 单元测试覆盖率 > 50%

### Week 4 验收
- [ ] 端到端回归测试通过
- [ ] 单元测试覆盖率 > 70%
- [ ] 系统启动正常，API 响应时间无劣化
- [ ] 文档更新完成

---

## 7. 风险与注意事项 (Risks & Notes)

| 风险 | 影响 | 缓解措施 |
| :--- | :--- | :--- |
| 重构引入回归 Bug | 高 | 每周进行完整回归测试 |
| 接口变更影响前端 | 中 | Phase 1 严格保持 API 签名不变 |
| Redis 不可用 | 低 | `ContextManager` 支持降级到内存缓存 |

---

## 附录: AI Coding 快速参考

### 常用命令
```bash
# 启动后端服务
cd backend && uvicorn app.main:app --reload

# 运行测试
cd backend && pytest tests/ -v

# 数据库迁移
cd backend && alembic upgrade head
```

### 命名规范
- 类名: `PascalCase` (e.g., `ConversationOrchestrator`)
- 函数/方法: `snake_case` (e.g., `process_message`)
- 私有方法: `_snake_case` (e.g., `_build_prompt_context`)
- 常量: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)

### 文件组织
```
backend/app/
├── api/                    # API 层 (不变)
├── core/
│   ├── config.py          # 添加 USE_MOCK_LLM
│   └── dependencies.py    # 新建: 依赖注入
├── models/
│   └── context.py         # 新建: 上下文数据结构
└── services/
    ├── chat_agent.py      # 重构: Facade
    ├── conversation_orchestrator.py  # 新建
    ├── llm_caller.py      # 新建
    ├── ui_component_injector.py      # 新建
    └── context_manager.py # 新建
```
