# 长期记忆去重流程图

## 📊 当前流程（存在重复问题）

```
用户发送消息: "我有房贷压力"
    ↓
chat_agent.process_message()
    ↓
_trigger_insight_analysis()
    ↓
insight_service.analyze_user_psychology()
    ↓
_extract_and_store_key_memories()
    ↓
提取记忆: "用户有房贷压力，需要保守策略"
    ↓
memory_service.add_memory()  ⚠️ 无去重检查
    ↓
直接创建 VectorMemory 记录 #1
    ↓
存储到数据库 ✅

---

用户再次提到: "房贷每月还款压力大"
    ↓
chat_agent.process_message()
    ↓
_trigger_insight_analysis()
    ↓
insight_service.analyze_user_psychology()
    ↓
_extract_and_store_key_memories()
    ↓
提取记忆: "用户有房贷压力，需要保守策略"
    ↓
memory_service.add_memory()  ⚠️ 无去重检查
    ↓
直接创建 VectorMemory 记录 #2  ❌ 重复！
    ↓
存储到数据库 ✅

结果: 数据库中有2条几乎相同的记忆
```

---

## ✅ 修复后流程（带去重）

```
用户发送消息: "我有房贷压力"
    ↓
chat_agent.process_message()
    ↓
_trigger_insight_analysis()
    ↓
insight_service.analyze_user_psychology()
    ↓
_extract_and_store_key_memories()
    ↓
提取记忆: "用户有房贷压力，需要保守策略"
    ↓
memory_service.add_memory_with_time_window()  ✅ 带去重检查
    ↓
检查: 24小时内是否有 category="debt_constraint" 的记忆？
    ├─ 否 → 创建新记忆 → 存储到数据库 ✅
    └─ 是 → 跳过创建，返回现有记忆 ✅

---

用户再次提到: "房贷每月还款压力大"
    ↓
chat_agent.process_message()
    ↓
_trigger_insight_analysis()
    ↓
insight_service.analyze_user_psychology()
    ↓
_extract_and_store_key_memories()
    ↓
提取记忆: "用户有房贷压力，需要保守策略"
    ↓
memory_service.add_memory_with_time_window()  ✅ 带去重检查
    ↓
检查: 24小时内是否有 category="debt_constraint" 的记忆？
    ├─ 是 → 找到记录 #1 (创建于2小时前)
    └─ 跳过创建，返回现有记忆 #1 ✅ 避免重复！

结果: 数据库中只有1条记忆，避免了重复
```

---

## 🔄 去重检查详细流程

### 方案1: 时间窗口去重（快速修复）

```
add_memory_with_time_window(user_id, text, metadata)
    ↓
提取 category = metadata["category"]
    ↓
查询数据库:
    SELECT * FROM vector_memory
    WHERE user_id = ?
      AND metadata->>'category' = ?
      AND created_at >= NOW() - INTERVAL '24 hours'
    ORDER BY created_at DESC
    LIMIT 1
    ↓
    ├─ 找到记录 → 返回现有记忆 (跳过创建)
    └─ 未找到 → 调用 add_memory() 创建新记忆
```

### 方案2: 相似度去重（精确方案）

```
add_memory_with_dedup(user_id, text, metadata)
    ↓
生成 text 的 embedding 向量
    ↓
查询数据库（向量相似度搜索）:
    SELECT *, 
           1 - (embedding <=> query_embedding) as similarity
    FROM vector_memory
    WHERE user_id = ?
      AND 1 - (embedding <=> query_embedding) >= 0.92
    ORDER BY similarity DESC
    LIMIT 1
    ↓
    ├─ 找到高相似度记忆 (similarity >= 0.92)
    │   ↓
    │   更新现有记忆的 created_at 和 metadata
    │   ↓
    │   返回更新后的记忆
    │
    └─ 未找到相似记忆
        ↓
        调用 add_memory() 创建新记忆
```

### 方案3: 混合策略（最佳方案）

```
add_memory_smart(user_id, text, metadata)
    ↓
【第一层: 快速时间窗口检查】
    ↓
查询: 24小时内是否有相同 category 的记忆？
    ↓
    ├─ 否 → 跳到创建新记忆
    │
    └─ 是 → 找到候选记忆
        ↓
        【第二层: 精确相似度验证】
        ↓
        计算 similarity = cosine_similarity(text, 候选记忆.content)
        ↓
        ├─ similarity >= 0.92 → 确认重复
        │   ↓
        │   更新现有记忆
        │   ↓
        │   返回更新后的记忆 ✅
        │
        └─ similarity < 0.92 → 不是重复
            ↓
            创建新记忆 ✅
```

---

## 📈 数据流对比

### 当前实现（无去重）

```
时间线:
T0: 用户提到 "房贷压力"
    → 创建记忆 #1: "用户有房贷压力..."

T1: 用户再提 "房贷压力大"  
    → 创建记忆 #2: "用户有房贷压力..." ❌ 重复

T2: 用户又提 "还贷压力"
    → 创建记忆 #3: "用户有房贷压力..." ❌ 重复

数据库状态:
┌────┬─────────┬──────────────────────────┬────────────────┐
│ ID │ User ID │ Content                  │ Category       │
├────┼─────────┼──────────────────────────┼────────────────┤
│ 1  │ 123     │ 用户有房贷压力...        │ debt_constraint│
│ 2  │ 123     │ 用户有房贷压力...        │ debt_constraint│ ❌
│ 3  │ 123     │ 用户有房贷压力...        │ debt_constraint│ ❌
└────┴─────────┴──────────────────────────┴────────────────┘

重复率: 66% (2/3条重复)
```

### 修复后（带去重）

```
时间线:
T0: 用户提到 "房贷压力"
    → 创建记忆 #1: "用户有房贷压力..."

T1: 用户再提 "房贷压力大"
    → 检查: 找到记忆 #1 (2小时前)
    → 跳过创建 ✅

T2: 用户又提 "还贷压力"
    → 检查: 找到记忆 #1 (4小时前)
    → 跳过创建 ✅

数据库状态:
┌────┬─────────┬──────────────────────────┬────────────────┐
│ ID │ User ID │ Content                  │ Category       │
├────┼─────────┼──────────────────────────┼────────────────┤
│ 1  │ 123     │ 用户有房贷压力...        │ debt_constraint│
└────┴─────────┴──────────────────────────┴────────────────┘

重复率: 0% (无重复)
存储节省: 66%
```

---

## 🎯 关键决策点

### 决策1: 何时触发去重检查？

```
选项A: 每次 add_memory() 都检查
    优点: 最彻底的去重
    缺点: 性能开销大
    
选项B: 只在 insight_service 调用时检查 ✅ 推荐
    优点: 性能开销小，针对性强
    缺点: 其他调用点可能仍有重复
    
选项C: 异步后台去重
    优点: 不影响主流程性能
    缺点: 实现复杂，可能有延迟
```

### 决策2: 去重粒度

```
选项A: 基于 category ✅ 推荐
    优点: 简单高效，符合业务逻辑
    缺点: 同类别不同内容可能被误判
    
选项B: 基于 embedding 相似度
    优点: 最精确
    缺点: 计算开销大
    
选项C: 混合策略 🏆 最佳
    优点: 兼顾性能和准确性
    缺点: 实现稍复杂
```

### 决策3: 时间窗口大小

```
选项A: 6小时
    优点: 严格去重
    缺点: 可能丢失用户关注点变化
    
选项B: 24小时 ✅ 推荐
    优点: 平衡去重和信息保留
    缺点: 一天内的变化可能被忽略
    
选项C: 7天
    优点: 长期去重
    缺点: 可能丢失重要的状态变化
```

---

## 🔍 检索流程对比

### 当前检索（有重复记忆）

```
用户问: "我的财务状况如何？"
    ↓
memory_service.retrieve_relevant(query="财务状况", limit=3)
    ↓
向量相似度搜索
    ↓
返回结果:
1. "用户有房贷压力..." (similarity=0.85) ← 重复
2. "用户有房贷压力..." (similarity=0.84) ← 重复
3. "用户有房贷压力..." (similarity=0.83) ← 重复

问题: 3条结果都是相同信息，浪费了context window
```

### 修复后检索（无重复）

```
用户问: "我的财务状况如何？"
    ↓
memory_service.retrieve_relevant(query="财务状况", limit=3)
    ↓
向量相似度搜索
    ↓
返回结果:
1. "用户有房贷压力..." (similarity=0.85) ✅
2. "用户计划3年内购房..." (similarity=0.78) ✅
3. "用户关注子女教育..." (similarity=0.72) ✅

优势: 3条结果涵盖不同维度，信息密度高
```

---

## 📊 性能对比

### 存储性能

```
场景: 用户30轮对话，触发6次insight分析

当前实现:
    提取记忆: 6次 × 2条 = 12条
    实际独特: ~6条
    重复率: 50%
    存储: 12 × 4.3KB = 51.6KB

修复后:
    提取记忆: 6次 × 2条 = 12次尝试
    去重后: 6条
    重复率: 0%
    存储: 6 × 4.3KB = 25.8KB
    
节省: 50% 存储空间
```

### 检索性能

```
场景: 检索相关记忆

当前实现:
    数据库记录: 12条
    向量搜索: O(12)
    检索时间: ~15ms

修复后:
    数据库记录: 6条
    向量搜索: O(6)
    检索时间: ~8ms
    
提升: 47% 检索速度
```

---

## 🛠️ 实施路径

### 阶段1: 快速修复（1-2天）

```
1. 实现 add_memory_with_time_window()
   ↓
2. 修改 insight_service 调用点
   ↓
3. 测试验证
   ↓
4. 部署到测试环境
   ↓
5. 观察24小时
   ↓
6. 部署到生产环境

预期效果: 减少80%重复记录
```

### 阶段2: 完善优化（3-5天）

```
1. 实现 add_memory_with_dedup() (相似度检查)
   ↓
2. 实现 _update_memory() (记忆更新)
   ↓
3. 实现混合策略 add_memory_smart()
   ↓
4. 添加监控指标
   ↓
5. 性能测试
   ↓
6. 灰度发布

预期效果: 减少95%重复记录
```

### 阶段3: 数据清理（1天）

```
1. 备份现有数据
   ↓
2. 分析重复情况
   ↓
3. 执行去重SQL
   ↓
4. 验证数据完整性
   ↓
5. 更新统计信息

预期效果: 清理历史重复数据
```

---

## 📝 总结

### 问题根源

```
设计理念: "宁可重复，不可遗漏"
    ↓
实现缺失: 无去重机制
    ↓
触发频繁: 每次分析都存储
    ↓
结果: 30-50%重复率
```

### 解决方案

```
时间窗口去重 (快速)
    +
相似度验证 (精确)
    =
混合策略 (最佳)
```

### 预期收益

```
存储成本: ↓ 30-50%
检索效率: ↑ 20-30%
用户体验: 显著改善
系统可维护性: 大幅提升
```

---

**图表生成时间**: 2026-01-16  
**版本**: v1.0
