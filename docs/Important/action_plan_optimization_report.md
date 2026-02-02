# Action Plan 系统代码深度审计与优化计划

## 1. 审计综述 (Overview)

经过对前后端代码 (`Backend: ActionReasoner/API`, `Frontend: ActionPlanCard/Service`) 与需求文档的逐行比对，我们发现了 **1 个严重功能缺陷**、**2 个潜在稳定性风险** 以及 **3 个主要的功能缺失**。

整体来看，核心流程（生成->采纳->展示）已跑通，但由于数据加载机制的问题，**步骤状态无法同步**，导致"执行跟踪"功能实际上不可用。

## 2. 严重缺陷 (Critical Issues)

### 🚨 2.1 步骤状态无法同步 (Status Sync Failure)
*   **现象**: 用户在前端勾选完成某个步骤后，刷新页面状态会重置为 "Pending"。
*   **原因**:
    *   后端 `read_plans` 接口仅查询了 `ActionPlan` 主表，**未执行 Eager Loading** (`selectinload`) 加载关联的 `steps_list`。
    *   `ActionPlan` 模型包含 `original_steps_snapshot` (JSON快照) 和 `steps_list` (实时关联表) 两个字段。
    *   前端逻辑是：优先取 `steps_list`，没有则取 `snapshot`。
    *   由于后端没返回 `steps_list`，前端被迫使用**静态的快照数据**，导致用户永远看到的是初始状态。
*   **影响**: 严重。导致 Phase 4 核心价值 "执行跟踪" 完全失效。
*   **修复方案**: 在 `api_v1/endpoints/action_plans.py` 中引入 `selectinload(ActionPlan.steps_list)`。

### 🚨 2.2 JSON 解析脆弱性 (Fragile JSON Parsing)
*   **现象**: `ActionReasoner` 使用正则表达式 `re.search(r'\{.*\}', ...)` 提取 LLM 返回的 JSON。
*   **风险**: 如果 LLM 返回的内容包含嵌套大括号（如代码块、数学公式），或者 JSON 格式有微小错误（如末尾多逗号），正则截取将失败，导致生成任务报错。
*   **修复方案**: 引入健壮的 JSON 修复库 (如 `json_repair`) 或使用 LLM Provider 的 Native JSON Mode。

## 3. 代码质量与隐患 (Technical Debts)

### ⚠️ 3.1 API 逻辑冗余与误导
*   **位置**: `api_v1/endpoints/action_plans.py` -> `adopt_plan`
*   **代码**:
    ```python
    # ❌ 错误地使用了硬编码的 Category WEALTH_GROWTH 进行查询，且查询结果被后续逻辑覆盖
    plan = await reasoner.get_active_plan_by_category(current_user.id, ActionCategory.WEALTH_GROWTH)
    ```
*   **建议**: 删除该冗余代码，避免误导维护者。

### ⚠️ 3.2 意图识别精度不足
*   **位置**: `ConversationOrchestrator.py`
*   **逻辑**: 使用简单的字符串匹配 (`if "重新生成" in message`) 判断用户是否想强制重置方案。
*   **风险**: 用户输入 "我不想重新生成" 也会触发重置。
*   **建议**: 将意图判断逻辑升级为 LLM 分类或基于语义的判断。

## 4. 需求差异分析 (Gap Analysis)

对比 `docs/Important/action_plan_requirements.md`，以下功能尚未实现：

| 需求项 | 现状 | 缺失功能 | 优先级 |
| :--- | :--- | :--- | :--- |
| **执行跟踪** | 前端有勾选框，后端有 API | **核心 Bug**: 状态无法持久化展示 (见 2.1) | **P0 (Blocker)** |
| **智能路由** | 实现了基础的 7 天规则 | 硬编码在 Python 代码中，不可配；缺少多维度路由 | P1 |
| **用户自主权** | 仅支持采纳/忽略 | **不支持编辑步骤** (Add/Edit Step) | P2 |
| **反馈机制** | 仅支持 Dismiss 动作 | **不支持收集 Dismiss 原因** (前端无弹窗，后端无字段) | P2 |
| **数据统计** | 后端有 stats 接口 | 前端 Dashboard 已实现基础展示，但缺乏趋势图 | P3 |

## 5. 执行计划 (Execution Plan)

建议分两阶段进行优化：

### 第一阶段：核心修复 (Immediate Fixes) - 预计 1 小时
1.  **[Backend]** 修复 API `read_plans` 和 `read_plan` 的 N+1 问题，添加 `selectinload`。
2.  **[Backend]** 清理 `adopt_plan` 中的冗余代码。
3.  **[Backend]** 增强 `ActionReasoner` 的 JSON 解析逻辑。
4.  **[Config]** 将 "7天过期" 提取为配置文件参数。

### 第二阶段：功能补全 (Feature Completion) - 预计 3 小时
1.  **[Frontend]** 实现 "编辑步骤" 功能 (支持编辑 `Pending` 状态的方案)。
2.  **[Frontend]** 实现 "Dismiss 弹窗"，收集用户拒绝原因。
3.  **[Backend]** 升级 `ActionPlan` 模型，增加 `dismiss_reason` 字段。
4.  **[Backend]** 完善 `Orchestrator` 的意图识别逻辑。

---
**Next Step**: 请批准执行 **第一阶段** 的修复工作。
