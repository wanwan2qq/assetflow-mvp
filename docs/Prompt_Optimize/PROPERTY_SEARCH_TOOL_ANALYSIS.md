# Property Search Tool 分析报告

## 执行摘要

经过详细分析 `backend/app/services/search_tools.py` 和相关配置文件，确认：

✅ **当前状态**：系统已经实现了 `property_search` 工具，但**正在使用 Mock 模式**（开发环境）

✅ **工具能力**：支持真实的 Tavily API 房产搜索，但需要配置真实的 API Key

⚠️ **当前问题**：AI 虽然有 `property_search` 工具，但由于 System Prompt 的指令问题，导致过度使用

---

## 1. Property Search Tool 实现分析

### 1.1 工具架构

`search_tools.py` 实现了一个灵活的房产搜索工具架构：

```
BasePropertySearchTool (抽象基类)
├── MockSearchTool (开发环境 - 当前使用)
└── TavilySearchTool (生产环境 - 需要真实 API Key)
```

### 1.2 工具接口定义

```python
class BasePropertySearchTool(BaseTool, ABC):
    name: str = "property_search"
    description: str = "搜索房产市场价格信息"
    
    class Args(BaseModel):
        city: str = Field(description="城市名称，如'北京'、'上海'")
        community: str = Field(description="小区名称，如'天通苑'、'望京'")
        area: float = Field(description="房屋面积，单位平方米")
```

**关键参数**：
- `city`: 城市名称（必需）
- `community`: 小区名称（必需）
- `area`: 房屋面积（必需）

**返回结果**：
```python
class PropertySearchResult(BaseModel):
    success: bool                    # 是否成功
    estimated_price: float | None    # 估算总价
    price_per_sqm: float | None      # 单价（元/平米）
    source: str                      # 数据来源
    confidence: float                # 置信度 (0.0-1.0)
    error: str | None                # 错误信息
    fallback_to_manual: bool         # 是否需要手动输入
```

---

## 2. 当前配置状态

### 2.1 配置文件分析

**`backend/.env` 配置**：
```properties
TAVILY_API_KEY=mock-tavily-key-for-development  # ⚠️ Mock Key
USE_MOCK_SEARCH=true                            # ⚠️ 使用 Mock 模式
```

**`backend/app/core/config.py` 默认值**：
```python
TAVILY_API_KEY: str | None = None
USE_MOCK_SEARCH: bool = True  # 默认使用 Mock
```

**`chat_agent.py` 初始化**（第89-92行）：
```python
self.search_tool = create_search_tool(
    use_mock=settings.USE_MOCK_SEARCH,      # True (当前)
    tavily_api_key=self.tavily_api_key      # "mock-tavily-key-for-development"
)
```

**结论**：当前系统使用 `MockSearchTool`，返回预设的模拟数据。

---

## 3. Mock Search Tool 行为分析

### 3.1 Mock 数据库

`MockSearchTool` 内置了以下小区的模拟数据（第70-79行）：

| 小区名称 | 单价（元/平米） | 所属区域 |
|---------|----------------|----------|
| 天通苑 | 38,000 | 昌平区 |
| 望京 | 65,000 | 朝阳区 |
| 国贸 | 120,000 | 朝阳区 |
| 陆家嘴 | 150,000 | 浦东新区 |
| 徐家汇 | 90,000 | 徐汇区 |
| 中关村 | 80,000 | 海淀区 |
| 三里屯 | 110,000 | 朝阳区 |
| 静安寺 | 130,000 | 静安区 |

**默认数据**（未匹配到小区时）：
- 单价：45,000 元/平米
- 区域：未知

### 3.2 估值计算逻辑

```python
# 1. 查找匹配的小区数据
price_per_sqm = result_data["price_per_sqm"]

# 2. 应用保守估值系数 (0.95)
estimated_price = price_per_sqm * area * 0.95

# 3. 返回结果
return PropertySearchResult(
    success=True,
    estimated_price=estimated_price,
    price_per_sqm=price_per_sqm,
    source="mock_data",
    confidence=0.8  # Mock 数据置信度固定为 0.8
)
```

**示例**：
- 输入：北京海淀区中关村，100平米
- 计算：80,000 × 100 × 0.95 = 7,600,000 元（760万）
- 输出：估值 760万，单价 8万/平米，置信度 0.8

---

## 4. Tavily Search Tool 实现分析

### 4.1 真实搜索流程

`TavilySearchTool` 使用 Tavily API 进行真实的房产价格搜索（第130-180行）：

```python
def _search_property(self, city: str, community: str, area: float) -> PropertySearchResult:
    # 1. 构建搜索查询
    current_month = datetime.now().strftime("%Y年%m月")
    query = f"{city} {community} 二手房 挂牌均价 {current_month}"
    
    # 2. 调用 Tavily API
    search_results = self.client.search(
        query=query, 
        search_depth="basic", 
        max_results=5
    )
    
    # 3. 提取价格信息
    price_info = self._extract_price_from_results(search_results["results"])
    
    # 4. 应用保守估值系数 (0.95)
    estimated_price = price_info["price_per_sqm"] * area * 0.95
    
    return PropertySearchResult(
        success=True,
        estimated_price=estimated_price,
        price_per_sqm=price_info["price_per_sqm"],
        source="tavily_api",
        confidence=0.7  # 真实数据置信度为 0.7
    )
```

### 4.2 价格提取逻辑

`_extract_price_from_results()` 方法使用正则表达式提取价格（第182-220行）：

**支持的价格格式**：
- `3.8万/平` → 38,000 元/平米
- `38000元/平` → 38,000 元/平米
- `均价3.8万` → 38,000 元/平米

**提取流程**：
1. 遍历搜索结果
2. 使用正则表达式匹配价格模式
3. 转换为统一的"元/平米"单位
4. 返回第一个匹配的价格

---

## 5. AI 如何调用 Property Search Tool

### 5.1 工具注册

在 `chat_agent.py` 的 `_create_agent()` 方法中（第207-209行）：

```python
agent = create_agent(
    model=self.llm, 
    tools=[self.search_tool],  # ✅ property_search 工具已注册
    system_prompt=system_prompt
)
```

### 5.2 AI 调用流程

```
用户消息: "我在北京海淀区中关村有一套100平米的房子，值多少钱？"
    ↓
AI 分析: 需要查询房产估值
    ↓
AI 调用: property_search(city="北京", community="中关村", area=100)
    ↓
Tool 执行: MockSearchTool._search_property()
    ↓
返回结果: {
    "success": true,
    "estimated_price": 7600000,
    "price_per_sqm": 80000,
    "source": "mock_data",
    "confidence": 0.8
}
    ↓
AI 回复: "根据市场数据，您在北京海淀区中关村100平米的房产当前估值约760万元..."
```

### 5.3 当前问题

虽然工具已经正确注册和实现，但由于 **System Prompt 的指令问题**（详见 `AI_PROPERTY_VALUATION_CONFIRMATION_ANALYSIS.md`），AI 会在不必要的时候也调用这个工具。

**问题场景**：
- 用户问："我想买AI股票，有什么建议？"
- AI 看到 Fact Sheet 中有房产信息
- AI 误以为需要确认房产估值
- AI 调用 `property_search` 工具
- AI 回复："先确认您的房产估值..."

---

## 6. 启用真实 Tavily API 的准备工作

### 6.1 获取 Tavily API Key

**步骤 1：注册 Tavily 账号**
1. 访问 [https://tavily.com](https://tavily.com)
2. 点击 "Sign Up" 注册账号
3. 验证邮箱

**步骤 2：获取 API Key**
1. 登录后进入 Dashboard
2. 找到 "API Keys" 部分
3. 复制你的 API Key（格式：`tvly-xxxxxxxxxxxxxx`）

**步骤 3：查看定价和配额**
- Free Tier: 通常提供 1,000 次/月免费搜索
- Paid Plans: 根据需求选择付费计划

### 6.2 配置 API Key

**方法 1：修改 `.env` 文件**（推荐）

编辑 `backend/.env`：
```properties
# 替换为真实的 Tavily API Key
TAVILY_API_KEY=tvly-your-real-api-key-here

# 启用真实搜索
USE_MOCK_SEARCH=false
```

**方法 2：环境变量**

```bash
export TAVILY_API_KEY="tvly-your-real-api-key-here"
export USE_MOCK_SEARCH=false
```

### 6.3 安装依赖

确保安装了 Tavily Python 客户端：

```bash
cd backend
pip install tavily-python
```

或者在 `pyproject.toml` 中添加：
```toml
[project]
dependencies = [
    # ... 其他依赖
    "tavily-python>=0.3.0",
]
```

### 6.4 重启服务

```bash
# 重启后端服务
cd backend
python -m uvicorn app.main:app --reload
```

### 6.5 验证配置

**测试脚本**（`backend/scripts/test_tavily_search.py`）：

```python
import asyncio
from app.services.search_tools import create_search_tool
from app.core.config import settings

async def test_tavily_search():
    # 创建搜索工具
    search_tool = create_search_tool(
        use_mock=settings.USE_MOCK_SEARCH,
        tavily_api_key=settings.TAVILY_API_KEY
    )
    
    print(f"Using tool: {type(search_tool).__name__}")
    print(f"USE_MOCK_SEARCH: {settings.USE_MOCK_SEARCH}")
    
    # 测试搜索
    result = search_tool._run(
        city="北京",
        community="中关村",
        area=100
    )
    
    print("\n搜索结果:")
    print(f"成功: {result['success']}")
    print(f"估值: {result['estimated_price']} 元")
    print(f"单价: {result['price_per_sqm']} 元/平米")
    print(f"来源: {result['source']}")
    print(f"置信度: {result['confidence']}")

if __name__ == "__main__":
    asyncio.run(test_tavily_search())
```

运行测试：
```bash
cd backend
python scripts/test_tavily_search.py
```

**预期输出（Mock 模式）**：
```
Using tool: MockSearchTool
USE_MOCK_SEARCH: True
搜索结果:
成功: True
估值: 7600000.0 元
单价: 80000 元/平米
来源: mock_data
置信度: 0.8
```

**预期输出（Tavily 模式）**：
```
Using tool: TavilySearchTool
USE_MOCK_SEARCH: False
搜索结果:
成功: True
估值: 8550000.0 元
单价: 90000 元/平米
来源: tavily_api
置信度: 0.7
```

---

## 7. Tavily API 使用注意事项

### 7.1 API 限制

- **速率限制**：根据你的计划，可能有每分钟/每小时的请求限制
- **配额限制**：Free Tier 通常有月度配额限制
- **超时设置**：建议设置合理的超时时间（默认 30 秒）

### 7.2 错误处理

`TavilySearchTool` 已经实现了完善的错误处理（第150-180行）：

```python
try:
    # 执行搜索
    search_results = self.client.search(...)
    
    if not search_results.get("results"):
        return PropertySearchResult(
            success=False,
            error="No search results found",
            fallback_to_manual=True  # ✅ 提示用户手动输入
        )
    
    # 提取价格信息
    price_info = self._extract_price_from_results(...)
    
    if not price_info:
        return PropertySearchResult(
            success=False,
            error="Could not extract price information",
            fallback_to_manual=True  # ✅ 提示用户手动输入
        )
    
except Exception as e:
    return PropertySearchResult(
        success=False,
        error=str(e),
        fallback_to_manual=True  # ✅ 提示用户手动输入
    )
```

**Fallback 机制**：
- 当 Tavily API 失败时，`fallback_to_manual=True`
- AI 会提示用户手动输入房产估值
- 不会阻塞对话流程

### 7.3 数据质量

**Tavily API 的优势**：
- 实时搜索最新的房产市场数据
- 覆盖全国主要城市和小区
- 自动聚合多个数据源

**潜在问题**：
- 搜索结果可能不准确（依赖网络数据质量）
- 价格提取可能失败（网页格式多样）
- 小众小区可能搜索不到数据

**建议**：
- 对于重要的房产估值，建议结合多个数据源
- 提供用户手动输入/修正估值的功能
- 显示数据来源和置信度，让用户自行判断

---

## 8. 成本估算

### 8.1 Tavily API 定价（参考）

| 计划 | 月费 | 搜索次数 | 单次成本 |
|------|------|----------|----------|
| Free | $0 | 1,000 | $0 |
| Starter | $29 | 10,000 | $0.0029 |
| Pro | $99 | 50,000 | $0.0020 |
| Enterprise | 定制 | 无限 | 协商 |

**注意**：以上价格仅供参考，请访问 [Tavily Pricing](https://tavily.com/pricing) 查看最新定价。

### 8.2 使用场景估算

**假设场景**：
- 每天 100 个用户使用 AI 顾问
- 每个用户平均提到 1 次房产信息
- 每次房产信息触发 1 次 `property_search` 调用

**月度使用量**：
- 100 用户/天 × 30 天 × 1 次/用户 = 3,000 次/月

**成本估算**：
- Free Tier: $0（前 1,000 次免费，超出部分需要升级）
- Starter Plan: $29/月（覆盖 10,000 次，足够使用）

### 8.3 优化建议

**减少 API 调用的策略**：

1. **缓存机制**（推荐）
   ```python
   # 缓存房产估值结果 24 小时
   cache_key = f"property:{city}:{community}:{area}"
   cached_result = redis.get(cache_key)
   if cached_result:
       return cached_result
   
   # 调用 API
   result = tavily_search(...)
   redis.setex(cache_key, 86400, result)  # 24 小时过期
   ```

2. **批量查询**
   - 如果用户有多套房产，一次性查询所有房产
   - 减少重复调用

3. **智能触发**（最重要）
   - 只有在用户主动询问房产估值时才调用 API
   - 避免在不必要的时候调用（这是当前的主要问题）

---

## 9. 总结与建议

### 9.1 当前状态总结

| 项目 | 状态 | 说明 |
|------|------|------|
| Property Search Tool | ✅ 已实现 | 支持 Mock 和 Tavily 两种模式 |
| Mock 模式 | ✅ 正常工作 | 当前使用，返回预设数据 |
| Tavily 模式 | ⚠️ 未启用 | 需要真实 API Key |
| AI 工具调用 | ✅ 已注册 | AI 可以正常调用工具 |
| 调用时机 | ❌ 有问题 | AI 过度调用工具（System Prompt 问题） |

### 9.2 启用 Tavily API 的步骤

**快速启用（5 分钟）**：
1. 注册 Tavily 账号，获取 API Key
2. 修改 `backend/.env`：
   ```properties
   TAVILY_API_KEY=tvly-your-real-api-key-here
   USE_MOCK_SEARCH=false
   ```
3. 安装依赖：`pip install tavily-python`
4. 重启后端服务
5. 运行测试脚本验证

**完整部署（30 分钟）**：
1. 完成快速启用步骤
2. 实现 Redis 缓存机制（减少 API 调用）
3. 添加监控和日志（跟踪 API 使用情况）
4. 配置错误告警（API 配额用尽时通知）
5. 优化 System Prompt（解决过度调用问题）

### 9.3 优先级建议

**高优先级**（必须解决）：
1. ✅ **修复 System Prompt**（详见 `AI_PROPERTY_VALUATION_CONFIRMATION_ANALYSIS.md`）
   - 这是导致 AI 过度调用 `property_search` 的根本原因
   - 即使启用 Tavily API，如果不修复这个问题，会导致大量不必要的 API 调用

**中优先级**（建议实施）：
2. 实现缓存机制（减少重复查询）
3. 添加用户手动输入/修正估值的功能

**低优先级**（可选）：
4. 启用 Tavily API（如果 Mock 数据足够使用，可以暂缓）
5. 集成其他房产数据源（如链家、贝壳等）

### 9.4 最终建议

**当前阶段**：
- 保持 Mock 模式，专注于修复 System Prompt 问题
- Mock 数据对于开发和测试已经足够

**生产环境**：
- 启用 Tavily API，提供真实的房产估值
- 实现缓存和 Fallback 机制，确保服务稳定性
- 监控 API 使用情况，优化成本

**关键点**：
> ⚠️ **在启用 Tavily API 之前，必须先修复 System Prompt 的问题**，否则会导致大量不必要的 API 调用，浪费配额和成本。

---

## 10. 相关文档

- [AI 房产估值重复确认问题分析](./AI_PROPERTY_VALUATION_CONFIRMATION_ANALYSIS.md)
- [Tavily API 官方文档](https://docs.tavily.com)
- [LangChain Tools 文档](https://python.langchain.com/docs/modules/agents/tools/)

---

**文档版本**：1.0  
**最后更新**：2026-01-16  
**作者**：Kiro AI Assistant
