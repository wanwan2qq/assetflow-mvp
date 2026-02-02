# Phase 3 技术方案：交互重构 (UI Tooling)

## 1. 背景与问题 (Context & Problems)

当前 UI 卡片的触发机制依赖于 `UIComponentInjector` 中的**正则表达式 (Regex)** 和硬编码规则 (Hard-coded rules)。
- **误触发**: 用户提到"价值"时，即使是在闲聊，也会弹出估值卡。
- **割裂感**: UI 卡片与 AI 回复的内容有时不匹配，因为 AI 不知道卡片被触发了。
- **扩展难**: 每新增一种卡片，都需要写复杂的 Python 逻辑来判断触发条件。

## 2. 目标 (Goals)

将 UI 卡片的触发权完全交给 **LLM**。
- **Tool Calling**: 定义 UI 组件为 Tool (例如 `show_valuation_card`)。
- **Context Aware**: LLM 根据当前对话上下文，决定是否调用工具。
- **Unified Stream**: 将工具调用的结果（UI配置数据）作为流的一部分或元数据返回给前端。

## 3. 核心架构设计 (Architecture Design)

### 3.1 LLM 层改造 (LLMProvider)

支持 OpenAI 格式的 Tool Calling。

- **Interface Updated**:
  ```python
  async def generate_stream(
      self, 
      messages: list[dict], 
      system_prompt: str,
      tools: list[dict] | None = None,  # New Argument
      tool_choice: str | dict = "auto",
      **kwargs
  ) -> AsyncIterator[str | ToolCall]:
  ```
  *(注：为了保持兼容性，Stream 可能会继续 yield 字符串，但我们可以定义一种特殊的协议，或者让 Provider 内部处理 ToolCall 并转为特殊标记)*

  **方案选择**: 鉴于前端目前通过 `<WIDGET>` 标签解析，最平滑的过渡方案是：
  1. LLM 发起 Tool Call。
  2. Orchestrator 捕获 Tool Call。
  3. Orchestrator 执行 Tool (生成 Widget JSON)。
  4. Orchestrator 将 Widget JSON 包装为 `<WIDGET>` 标签拼接在回复末尾。

### 3.2 工具定义 (UI Tools Definition)

在 `app/services/ui_tools.py` 中定义 Pydantic Models，并导出为 OpenAI Tools Schema。

```python
class ShowValuationCard(BaseModel):
    """
    当用户询问房产价值、估值，或需要展示房产详细财务数据时调用。
    """
    asset_id: int | None = Field(description="特定房产ID，如果不指定则展示所有或默认")

class ShowActionPlan(BaseModel):
    """
    当用户询问理财方案、行动计划、下一步建议时调用。
    """
    focus_area: str | None = Field(description="方案关注领域: protection, growth, etc.")
```

### 3.3 编排层逻辑 (Orchestrator Logic)

重构 `process_message`:

```python
# 1. Prepare Tools
tools = [convert_to_openai_tool(ShowValuationCard), ...]

# 2. Call LLM
response_stream = llm.generate_stream(..., tools=tools)

# 3. Handle Stream
async for chunk in response_stream:
    if is_tool_call(chunk):
        # Accumulate tool call arguments
        pass
    else:
        yield chunk

# 4. Finalize Tool Call (Post-stream or during stream if possible)
if tool_called:
    widget_tag = ui_component_service.generate_from_tool(tool_name, tool_args)
    yield widget_tag  # Send <WIDGET...> to frontend
```

### 3.4 前端适配 (Frontend)

- **保持不变**: 前端继续解析 `<WIDGET>` 标签。
- **变化**: 标签的生成源头变了，不仅更准，而且 AI 的文字回复会配合卡片（因为 AI 知道自己调用了工具）。

## 4. 实施步骤 (Implementation Steps)

### Step 1: 升级 LLMProvider
- 修改 `DeepSeekProvider`，使用 `langchain` 的 `bind_tools` 功能。
- 处理 Streaming 中的 ToolCallChunk。

### Step 2: 定义 UI Tools
- 创建 `app/services/ui_tools.py`。
- 实现 Schema 生成。

### Step 3: 改造 Orchestrator
- 移除 regex injector 逻辑。
- 接入 Tool Calling 处理流。
- 编写 `ToolRunner` 逻辑，将 Tool Call 映射回 `UIComponentService` 的调用。

## 5. 风险与对策
- **LLM 不调用工具**: Prompt 中需加强引导 ("如果需要展示数据，请务必调用相应工具")。
- **延迟增加**: Tool Calling 可能会增加推理耗时。对策：仅在复杂意图下启用 Tools。
