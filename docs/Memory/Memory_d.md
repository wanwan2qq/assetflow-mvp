sequenceDiagram
    participant User as 👤 用户
    participant ChatAgent as 🤖 System 1 (ChatAgent)
    participant Extractor as 📝 提取服务 (L1/L2)
    participant DB as 💾 数据库 (PostgreSQL)
    participant LLM as 🧠 大模型 (DeepSeek)
    participant Insight as 🕵️ System 2 (InsightWorker)

    Note over User, LLM: 🔴 Phase 1: 同步感知 (System 1) - 阻塞且快速
    User->>ChatAgent: "我有500万现金，想给孩子存留学基金"
    
    rect rgb(230, 240, 255)
        ChatAgent->>Extractor: 1. 立即调用提取 (Extract)
        Extractor->>DB: 2. 写入 L1 (UserAsset: Cash=500w)<br/>写入 L2 (Goals: Education, Status: Cash=True)
        DB-->>ChatAgent: 3. 返回最新数据 (Fact Sheet)
    end
    
    ChatAgent->>ChatAgent: 4. 更新内存上下文 (Refresh Context)
    ChatAgent->>LLM: 5. 发送 Prompt (包含最新 Fact Sheet)
    LLM-->>ChatAgent: 6. 生成回复 (基于已有500万的事实)
    ChatAgent->>User: "收到，500万现金流动性很好。关于留学基金..."

    Note over ChatAgent, Insight: 🔵 Phase 2: 异步反思 (System 2) - 后台慢处理
    rect rgb(240, 255, 240)
        ChatAgent-)Insight: 7. 触发异步任务 (Fire & Forget)
        Insight->>DB: 读取最近对话 (L0)
        Insight->>Insight: 8. 分析心理 & 检索历史
        Insight->>DB: 9. 写入 L3 (AdvisorNote: 用户重视教育，风险偏好中等)<br/>写入 L4 (Vector: "留学计划")
    end