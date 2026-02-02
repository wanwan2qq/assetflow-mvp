# Phase 4 Technical Design: Action Plan Implementation

## 1. Overview

Phase 4 introduces the **Action Plan** feature, transforming AssetFlow from a passive analysis tool into a proactive financial advisor. This phase focuses on generating concrete, actionable steps ("Action Plans") based on user assets, profile, and knowledge base insights.

## 2. Architecture

The core of this phase is the `ActionReasoner` service, which orchestrates the generation and management of action plans.

```mermaid
graph TD
    User([User]) <--> Orchestrator[Conversation Orchestrator]
    Orchestrator -->|Trigger| ActionReasoner[Action Reasoner]
    
    subgraph "Action Reasoner Service"
        GapAnalysis[Gap Analysis Engine]
        LLMGen[LLM Plan Generator]
        PlanManager[Plan Lifecycle Manager]
    end
    
    ActionReasoner -->|Read| Context[User Context (Assets/Profile)]
    ActionReasoner -->|Retrieve| RAG[RAG Engine (Knowledge)]
    ActionReasoner -->|Store| DB[(PostgreSQL)]
    
    Orchestrator -->|Inject| UIInjector[UI Component Injector]
    UIInjector -->|Render| ActionCard[Action Plan Card]
```

### 2.1 Core Components

*   **ActionReasoner**: Service responsible for analyzing user state, identifying financial gaps, invoking LLM to generate plans, and managing plan lifecycle.
*   **ConversationOrchestrator**: Triggers plan generation based on conversation context (e.g., specific intent or periodic check) and handles user "on-demand" requests.
*   **UIComponentInjector**: Formats generated plans into UI cards (`ActionPlanCard`, `ActionCard`) for the frontend.

## 3. Data Models

### 3.1 ActionPlan
Represents a high-level strategic plan.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Primary Key |
| `user_id` | Integer | Foreign Key to User |
| `title` | String | Plan title (e.g., "Family Protection Plan") |
| `category` | Enum | `wealth_protection`, `wealth_growth`, `real_estate`, `life_planning`, `debt_optimization` |
| `priority` | Enum | `high`, `medium`, `low` |
| `summary` | Text | Overview of the plan |
| `steps` | List[JSON] | Snapshot of steps (for display) |
| `status` | Enum | `draft`, `pending`, `in_progress`, `completed`, `dismissed` |

### 3.2 ActionPlanStep
Represents granular actionable steps within a plan, allowing for individual tracking.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | Integer | Primary Key |
| `plan_id` | Integer | Foreign Key to ActionPlan |
| `action` | String | Action title |
| `description` | Text | Detailed instructions |
| `status` | Enum | `pending`, `in_progress`, `completed`, `skipped` |

## 4. Core Logic

### 4.1 Gap Analysis
Before generating a plan, `ActionReasoner` performs a deterministic gap analysis:
1.  **Insurance Gap**: Checks for missing Life/Health insurance based on family structure.
2.  **Emergency Fund Gap**: Checks if cash assets cover 6 months of expenses.
3.  **Real Estate Opportunities**: Identifies potential refinancing or optimization opportunities.

### 4.2 Plan Generation (LLM-based)
1.  **Context Assembly**: Aggregates User Profile, Assets, and identified Gaps.
2.  **Knowledge Retrieval**: Queries RAG for relevant financial advice (e.g., "wealth growth strategies for conservative investors").
3.  **Prompt Engineering**: Constructs a prompt combining Context + Gaps + Knowledge.
4.  **Structured Output**: LLM generates a JSON object matching the `ActionPlan` schema.

### 4.3 Plan Lifecycle
*   **Generation**: Created as `pending`.
*   **Adoption**: User confirms "Accept Plan" -> Status becomes `in_progress`. Individual `ActionPlanStep` records are created from the snapshot.
*   **Tracking**: User marks steps as completed.
*   **Completion**: When all steps are done, Plan becomes `completed`.

## 5. UI Integration

### 5.1 ActionPlanCard
*   **Trigger**: When `ConversationOrchestrator` determines a plan is relevant (via Tool Call `ShowActionPlan`).
*   **Content**: Displays Title, Summary, Benefits, Risks, and the list of Steps.
*   **Actions**: "Accept Plan" (API: `POST /plans/{id}/adopt`), "Dismiss" (API: `POST /plans/{id}/dismiss`).

### 5.2 ActionCard
*   **Trigger**: For single, immediate recommendations (checking risk warnings).
*   **Content**: Simple Title, Description, and Priority.

## 6. Verification Plan

*   **Unit Tests**: Verify `ActionReasoner.analyze_gaps` correctly identifies missing insurance/funds.
*   **Integration Tests**: Verify the flow `Orchestrator -> ActionReasoner -> DB -> UIInjector`.
*   **Manual Verification**:
    1.  User asks "Make a financial plan for me".
    2.  System generates a `pending` plan and shows `ActionPlanCard`.
    3.  User clicks "Accept".
    4.  System updates plan to `in_progress`.
