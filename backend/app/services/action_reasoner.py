"""
ActionReasoner Service for Phase 4

可执行方案推理器 - 基于用户资产、画像和知识库生成个性化行动建议

职责:
- 分析用户资产配置
- 结合用户画像生成个性化建议
- 调用 RAG 知识库增强推理
- 生成可执行的 ActionPlan
"""

import json
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, func, desc, or_

from app.core.database import get_db_session
from app.core.config import get_settings
from app.core.prompt_manager import prompt_manager
from app.models.action_plan import (
    ActionPlan, 
    ActionCategory, 
    ActionPriority
)
from app.models.user import User, UserAsset, UserProfile

logger = logging.getLogger(__name__)


class ActionReasoner:
    """
    可执行方案推理器
    
    基于用户资产、画像和知识库生成个性化行动建议
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.prompt_manager = prompt_manager  # Use singleton
    
    async def generate_plan(
        self,
        user_id: int,
        focus_area: ActionCategory | None = None,
        check_existing: bool = True
    ) -> tuple[list[ActionPlan], str]:
        """
        生成可执行方案
        
        Args:
            user_id: 用户ID
            focus_area: 可选的聚焦领域
            check_existing: 是否检查现存计划 (智能路由)
            
        Returns:
            (plans, status_code)
            status_code: "generated", "existing_active", "existing_pending"
        """
        if not self.settings.ENABLE_ACTION_REASONER:
            logger.info("ActionReasoner disabled by feature flag")
            return [], "disabled"
        
        try:
            # Smart Routing: Check for existing plans
            if check_existing and focus_area:
                existing_plan = await self.get_active_plan_by_category(user_id, focus_area)
                if existing_plan:
                    status_code = "existing_pending" if existing_plan.status == "pending" else "existing_active"
                    logger.info(f"👉 [ACTION_REASONER] Found existing plan {existing_plan.id} ({status_code})")
                    return [existing_plan], status_code

            logger.info(f"🎯 [ACTION_REASONER] Generating NEW plan for user {user_id}, focus={focus_area}")
            
            # Step 1: 加载用户上下文
            user_context = await self._load_user_context(user_id)
            if not user_context:
                logger.warning(f"No context found for user {user_id}")
                return [], "no_context"
            
            # Step 2: 分析资产配置缺口
            gaps = await self.analyze_gaps(user_id)
            
            # Step 3: 检索相关知识
            knowledge_context = await self._retrieve_relevant_knowledge(
                user_context, 
                focus_area
            )
            
            # Step 4: 使用 LLM 生成方案
            plan_data = await self._generate_plan_with_llm(
                user_context,
                gaps,
                knowledge_context,
                focus_area
            )
            
            if plan_data:
                # Step 5: 存储方案
                saved_plan = await self._save_plan(user_id, plan_data, focus_area)
                if saved_plan:
                    logger.info(f"✅ [ACTION_REASONER] Generated plan: {saved_plan.title}")
                    return [saved_plan], "generated"
            
            return [], "failed"
            
        except Exception as e:
            logger.error(f"❌ [ACTION_REASONER] Error generating plan: {e}")
            return [], "error"

    async def get_active_plan_by_category(
        self,
        user_id: int,
        category: ActionCategory
    ) -> ActionPlan | None:
        """获取指定类别下的活跃计划 (pending 或 in_progress)"""
        try:
            async for session in get_db_session():
                # 定义"活跃"状态
                active_statuses = ["pending", "in_progress"]
                
                stmt = select(ActionPlan).where(
                    ActionPlan.user_id == user_id,
                    ActionPlan.category == category.value,
                    ActionPlan.status.in_(active_statuses)
                ).order_by(ActionPlan.created_at.desc())
                
                result = await session.execute(stmt)
                plan = result.scalars().first()
                
                if plan:
                    # 7-day rule: If pending plan is older than 7 days, ignore it (allow new generation)
                    # In-progress plans always block/warn.
                    from datetime import datetime, timedelta
                    stale_days = getattr(self.settings, 'ACTION_PLAN_STALE_DAYS', 7)
                    seven_days_ago = datetime.utcnow() - timedelta(days=stale_days)
                    
                    if plan.status == "pending" and plan.created_at < seven_days_ago:
                        logger.info(f"Ignoring stale pending plan {plan.id} (created {plan.created_at})")
                        return None
                        
                    return plan
                    
                return None
        except Exception as e:
            logger.error(f"Error getting active plan: {e}")
            return None

    async def adopt_plan(self, plan_id: int) -> ActionPlan | None:
        """采纳计划：状态变更 -> 生成步骤记录"""
        try:
            from app.models.action_plan import ActionPlanStep
            from datetime import datetime

            async for session in get_db_session():
                # 1. 获取计划
                stmt = select(ActionPlan).where(ActionPlan.id == plan_id).options(selectinload(ActionPlan.steps_list))
                result = await session.execute(stmt)
                plan = result.scalar_one_or_none()
                
                if not plan:
                    return None
                
                # 2. 更新状态
                if plan.status == "pending":
                    plan.status = "in_progress"
                    plan.adopted_at = datetime.utcnow()
                    
                    # 3. 生成步骤记录
                    # 从 original_steps_snapshot 解析并创建 ActionPlanStep
                    steps_data = plan.original_steps_snapshot or []
                    for idx, step in enumerate(steps_data):
                        # 兼容不同格式的 step 数据
                        step_action = step.get("action", step.get("title", f"步骤{idx+1}"))
                        
                        db_step = ActionPlanStep(
                            plan_id=plan.id,
                            step_number=step.get("step_number", idx + 1),
                            action=step_action,
                            description=step.get("description", ""),
                            expected_outcome=step.get("expected_outcome", ""),
                            timeline=step.get("timeline", ""),
                            status="pending"
                        )
                        session.add(db_step)
                    
                    session.add(plan)
                    await session.commit()
                    await session.commit()
                    
                    # Re-fetch with eager loading to ensure steps_list is present for serialization after commit
                    # (commit expires the instance, and we need steps_list loaded before session closes)
                    stmt = select(ActionPlan).where(ActionPlan.id == plan_id).options(selectinload(ActionPlan.steps_list))
                    result = await session.execute(stmt)
                    plan = result.scalar_one()
                    
                    return plan
                
                return plan # Already adopted or other status
                
        except Exception as e:
            logger.error(f"Error adopting plan: {e}")
            return None

    async def dismiss_plan(self, plan_id: int, reason: Optional[str] = None) -> bool:
        """忽略/归档计划"""
        try:
            from app.models.action_plan import ActionPlan
            # ActionStatus is imported at module level or inside if needed, assuming string literal is fine or import
            
            async for session in get_db_session():
                stmt = select(ActionPlan).where(ActionPlan.id == plan_id)
                result = await session.execute(stmt)
                plan = result.scalar_one_or_none()
                
                if plan and plan.status == "pending":
                    plan.status = "dismissed"
                    plan.dismiss_reason = reason
                    session.add(plan)
                    await session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error dismissing plan: {e}")
            return False

    async def update_step_status(
        self,
        step_id: int,
        status: str,
        notes: str | None = None
    ) -> bool:
        """更新步骤状态"""
        try:
            from app.models.action_plan import ActionPlanStep
            from datetime import datetime
            
            async for session in get_db_session():
                stmt = select(ActionPlanStep).where(ActionPlanStep.id == step_id)
                result = await session.execute(stmt)
                step = result.scalar_one_or_none()
                
                if step:
                    step.status = status
                    if status == "completed" and step.status != "completed":
                        step.completed_at = datetime.utcnow()
                    if notes:
                        step.user_notes = notes
                        
                    session.add(step)
                    await session.commit()
                    
                    # 检查是否所有步骤都已完成，若是则更新计划状态
                    await self._check_plan_completion(session, step.plan_id)
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating step status: {e}")
            return False

    async def refine_plan(
        self,
        plan_id: int,
        feedback: str
    ) -> ActionPlan | None:
        """根据用户反馈调整计划"""
        try:
            from datetime import datetime
            async for session in get_db_session():
                # 1. 获取原计划
                stmt = select(ActionPlan).where(ActionPlan.id == plan_id)
                result = await session.execute(stmt)
                plan = result.scalar_one_or_none()
                
                if not plan or plan.status != "pending":
                    logger.warning(f"Plan {plan_id} not found or not pending")
                    return None
                
                # 2. 调用 LLM 调整
                new_plan_data = await self._refine_plan_with_llm(plan, feedback)
                
                if new_plan_data:
                    # 3. 更新现有计划
                    plan.summary = new_plan_data.get("summary", plan.summary)
                    plan.original_steps_snapshot = new_plan_data.get("steps", plan.original_steps_snapshot)
                    plan.expected_benefits = new_plan_data.get("expected_benefits", plan.expected_benefits)
                    plan.potential_risks = new_plan_data.get("potential_risks", plan.potential_risks)
                    plan.updated_at = datetime.utcnow()
                    
                    session.add(plan)
                    await session.commit()
                    await session.refresh(plan)
                    
                    logger.info(f"✅ [ACTION_REASONER] Refined plan {plan_id}")
                    return plan
                    
            return None
            
        except Exception as e:
            logger.error(f"Error refining plan: {e}")
            return None

    async def _refine_plan_with_llm(self, plan: ActionPlan, feedback: str) -> dict | None:
        """调用 LLM 根据反馈修改计划 JSON"""
        try:
            from app.core.dependencies import get_llm_provider
            llm_provider = get_llm_provider()
            
            current_json = {
                "title": plan.title,
                "summary": plan.summary,
                "steps": plan.original_steps_snapshot,
                "expected_benefits": plan.expected_benefits,
                "potential_risks": plan.potential_risks
            }
            
            prompt = f"""你是一位专业的财务顾问。用户希望调整以下行动方案。

当前方案 (JSON):
{json.dumps(current_json, ensure_ascii=False, indent=2)}

用户反馈: "{feedback}"

请根据反馈修改方案。保持 JSON 结构不变（title, summary, steps, expected_benefits, potential_risks）。
仅返回修改后的 JSON。"""

            messages = [{"role": "user", "content": prompt}]
            
            response = ""
            async for chunk in llm_provider.generate_stream(messages, "您是一个JSON生成助手。"):
                response += chunk
                
            # 解析 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
            return None
            
        except Exception as e:
            logger.error(f"Error refining plan with LLM: {e}")
            return None

    async def _check_plan_completion(self, session, plan_id: int):
        """检查计划是否完成"""
        from app.models.action_plan import ActionPlanStep
        from datetime import datetime
        
        # 统计未完成的步骤数
        stmt = select(ActionPlanStep).where(
            ActionPlanStep.plan_id == plan_id,
            ActionPlanStep.status.not_in(["completed", "skipped"])
        )
        result = await session.execute(stmt)
        incomplete_steps = result.scalars().all()
        
        if not incomplete_steps:
            # 所有步骤已完成
            plan_stmt = select(ActionPlan).where(ActionPlan.id == plan_id)
            plan_result = await session.execute(plan_stmt)
            plan = plan_result.scalar_one_or_none()
            if plan and plan.status == "in_progress":
                plan.status = "completed"
                plan.completed_at = datetime.utcnow()
                session.add(plan)
                await session.commit()
                logger.info(f"🎉 Plan {plan_id} completed!")

    async def analyze_gaps(self, user_id: int) -> dict:
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
        gaps = {
            "insurance_gap": [],
            "emergency_fund_gap": None,
            "investment_suggestions": [],
            "debt_optimization": [],
            "real_estate_opportunities": []
        }
        
        try:
            async for session in get_db_session():
                # 加载用户资产
                assets_stmt = select(UserAsset).where(UserAsset.user_id == user_id)
                result = await session.execute(assets_stmt)
                assets = result.scalars().all()
                
                # 加载用户画像
                profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                profile_result = await session.execute(profile_stmt)
                profile = profile_result.scalar_one_or_none()
                
                # 分析保险缺口
                has_life_insurance = any(
                    a.asset_type.value == "insurance" and "life" in (a.name or "").lower() 
                    for a in assets
                )
                has_health_insurance = any(
                    a.asset_type.value == "insurance" and "health" in (a.name or "").lower() 
                    for a in assets
                )
                
                if not has_life_insurance:
                    gaps["insurance_gap"].append({
                        "type": "life_insurance",
                        "urgency": "high" if profile and profile.family_structure == "married_with_kids" else "medium",
                        "reason": "家庭支柱需要人寿保险保障"
                    })
                
                if not has_health_insurance:
                    gaps["insurance_gap"].append({
                        "type": "health_insurance",
                        "urgency": "high",
                        "reason": "医疗保障是基础需求"
                    })
                
                # 分析应急金缺口
                cash_assets = sum(
                    a.value or 0 
                    for a in assets 
                    if a.asset_type.value in ["cash", "deposit"]
                )
                monthly_expense = profile.monthly_expense if profile else 10000
                recommended_emergency = monthly_expense * 6  # 6个月开支
                
                if cash_assets < recommended_emergency:
                    gaps["emergency_fund_gap"] = {
                        "current": cash_assets,
                        "recommended": recommended_emergency,
                        "shortfall": recommended_emergency - cash_assets,
                        "reason": "应急金应覆盖6个月生活开支"
                    }
                
                # 分析房产机会
                real_estate = [
                    a for a in assets 
                    if a.asset_type.value == "real_estate"
                ]
                if real_estate:
                    for prop in real_estate:
                        # 检查是否有杠杆优化空间
                        extra_data = prop.extra_data or {}
                        mortgage = extra_data.get("mortgage_balance", 0)
                        value = prop.value or 0
                        
                        if mortgage > 0 and value > mortgage * 2:
                            gaps["real_estate_opportunities"].append({
                                "asset_id": prop.id,
                                "type": "refinance",
                                "reason": f"当前抵押率较低 ({mortgage/value*100:.1f}%)，可考虑优化杠杆"
                            })
                
                logger.info(f"📊 [ACTION_REASONER] Gap analysis for user {user_id}: {len(gaps['insurance_gap'])} insurance gaps")
                return gaps
                
        except Exception as e:
            logger.error(f"Error analyzing gaps: {e}")
            return gaps
    
    async def prioritize_actions(
        self,
        plans: list[ActionPlan]
    ) -> list[ActionPlan]:
        """根据紧迫性和影响度排序"""
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(
            plans, 
            key=lambda p: (priority_order.get(p.priority, 2), -p.confidence)
        )
    
    async def get_user_plans(
        self,
        user_id: int,
        status: str | None = None
    ) -> list[ActionPlan]:
        """获取用户的行动计划"""
        try:
            async for session in get_db_session():
                stmt = select(ActionPlan).where(ActionPlan.user_id == user_id)
                if status:
                    stmt = stmt.where(ActionPlan.status == status)
                stmt = stmt.order_by(ActionPlan.created_at.desc())
                
                result = await session.execute(stmt)
                return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting user plans: {e}")
            return []
    
    async def update_plan_status(
        self,
        plan_id: int,
        status: str,
        completed_steps: list[int] | None = None
    ) -> bool:
        """更新计划状态"""
        try:
            async for session in get_db_session():
                stmt = select(ActionPlan).where(ActionPlan.id == plan_id)
                result = await session.execute(stmt)
                plan = result.scalar_one_or_none()
                
                if plan:
                    plan.status = status
                    if completed_steps is not None:
                        plan.completed_steps = completed_steps
                    await session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating plan status: {e}")
            return False
    
    async def _load_user_context(self, user_id: int) -> dict | None:
        """加载用户上下文"""
        try:
            async for session in get_db_session():
                # 加载用户
                user_stmt = select(User).where(User.id == user_id)
                user_result = await session.execute(user_stmt)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    return None
                
                # 加载画像
                profile_stmt = select(UserProfile).where(UserProfile.user_id == user_id)
                profile_result = await session.execute(profile_stmt)
                profile = profile_result.scalar_one_or_none()
                
                # 加载资产
                assets_stmt = select(UserAsset).where(UserAsset.user_id == user_id)
                assets_result = await session.execute(assets_stmt)
                assets = list(assets_result.scalars().all())
                
                # 构建上下文
                context = {
                    "user_id": user_id,
                    "profile": {
                        "age_range": profile.age_range if profile else "unknown",
                        "family_structure": profile.family_structure if profile else "unknown",
                        "risk_preference": profile.risk_preference if profile else "unknown",
                        "occupation": profile.occupation if profile else None,
                        "income_range": profile.income_range if profile else None,
                        "monthly_expense": profile.monthly_expense if profile else None
                    } if profile else {},
                    "assets": [
                        {
                            "id": a.id,
                            "name": a.name,
                            "type": a.asset_type.value,
                            "value": a.value
                        }
                        for a in assets
                    ],
                    "total_assets": sum(a.value or 0 for a in assets)
                }
                
                return context
                
        except Exception as e:
            logger.error(f"Error loading user context: {e}")
            return None
    
    async def _retrieve_relevant_knowledge(
        self,
        user_context: dict,
        focus_area: ActionCategory | None
    ) -> str:
        """检索相关知识"""
        try:
            from app.services.rag_engine import get_rag_engine
            
            rag_engine = get_rag_engine()
            
            # 构建查询
            query_parts = []
            if focus_area:
                query_parts.append(f"关于{focus_area.value}的建议")
            
            profile = user_context.get("profile", {})
            if profile.get("family_structure") == "married_with_kids":
                query_parts.append("家庭财务规划")
            if profile.get("risk_preference") == "conservative":
                query_parts.append("稳健型理财")
            
            if not query_parts:
                query_parts.append("资产配置建议")
            
            query = " ".join(query_parts)
            
            # 检索知识
            result = await rag_engine.query(query, user_context)
            return result.answer if result else ""
            
        except Exception as e:
            logger.warning(f"Error retrieving knowledge: {e}")
            return ""
    
    async def _generate_plan_with_llm(
        self,
        user_context: dict,
        gaps: dict,
        knowledge_context: str,
        focus_area: ActionCategory | None
    ) -> dict | None:
        """使用 LLM 生成方案"""
        try:
            from app.core.dependencies import get_llm_provider
            
            llm_provider = get_llm_provider()
            
            # 构建资产摘要
            asset_summary = self._build_asset_summary(user_context, gaps)
            
            # 构建用户画像摘要
            profile_summary = self._build_profile_summary(user_context.get("profile", {}))
            
            # 加载并渲染 prompt - 使用 render() 方法
            try:
                system_prompt = self.prompt_manager.render(
                    category="action",
                    filename="action_plan_generator",
                    key="system_instruction",
                    asset_summary=asset_summary,
                    user_profile=profile_summary,
                    knowledge_context=knowledge_context or "暂无相关知识参考",
                    focus_area=focus_area.value if focus_area else "综合资产配置"
                )
            except Exception as e:
                logger.warning(f"Failed to load prompt template: {e}, using fallback")
                # Fallback prompt
                system_prompt = f"""你是一位专业的家庭财务规划师。请基于以下信息生成可执行的行动方案。

用户资产: {asset_summary}
用户画像: {profile_summary}
关注方向: {focus_area.value if focus_area else "综合资产配置"}

请返回 JSON 格式的方案，包含 title, category, priority, summary, steps, expected_benefits, potential_risks, confidence 字段。"""
            
            # 调用 LLM
            messages = [{"role": "user", "content": "请根据我的情况生成一个可执行的行动方案。"}]
            
            logger.info("🤖 [ACTION_REASONER] Starting LLM stream generation...")
            response = ""
            chunk_count = 0
            async for chunk in llm_provider.generate_stream(messages, system_prompt):
                if chunk_count == 0:
                    logger.info("🤖 [ACTION_REASONER] Received first chunk")
                response += chunk
                chunk_count += 1
            logger.info(f"🤖 [ACTION_REASONER] LLM stream finished. Total chunks: {chunk_count}, Length: {len(response)}")
            
            # 解析 JSON
            try:
                # Remove markdown code blocks if present
                clean_response = response
                if "```json" in clean_response:
                    clean_response = clean_response.split("```json")[1].split("```")[0]
                elif "```" in clean_response:
                    clean_response = clean_response.split("```")[0] # Simplistic fallback
                
                clean_response = clean_response.strip()
                
                # Robust JSON extraction using regex to find the outermost valid JSON object
                import re
                # Match the first '{' to the last '}'
                # This is better than {.*} with DOTALL which is greedy and might fail if there is text after
                # But for now, let's use a non-greedy approach or just clean content
                
                json_match = re.search(r'(\{[\s\S]*\})', clean_response)
                
                if json_match:
                    json_str = json_match.group(1)
                    # Try to parse
                    plan_data = json.loads(json_str)
                    return plan_data
                
                # Fallback: try parsing the whole cleaned response
                plan_data = json.loads(clean_response)
                return plan_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                # TODO: Implement repair logic or retry
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating plan with LLM: {e}")
            return None
    
    def _build_asset_summary(self, user_context: dict, gaps: dict) -> str:
        """构建资产摘要"""
        parts = []
        
        total = user_context.get("total_assets", 0)
        parts.append(f"总资产: {total/10000:.1f}万元")
        
        assets = user_context.get("assets", [])
        if assets:
            by_type = {}
            for a in assets:
                t = a.get("type", "other")
                by_type[t] = by_type.get(t, 0) + (a.get("value") or 0)
            
            for t, v in by_type.items():
                parts.append(f"  - {t}: {v/10000:.1f}万元")
        
        # 添加缺口信息
        if gaps.get("emergency_fund_gap"):
            gap = gaps["emergency_fund_gap"]
            parts.append(f"应急金缺口: {gap['shortfall']/10000:.1f}万元")
        
        if gaps.get("insurance_gap"):
            parts.append(f"保险缺口: {len(gaps['insurance_gap'])}项")
        
        return "\n".join(parts)
    
    def _build_profile_summary(self, profile: dict) -> str:
        """构建画像摘要"""
        parts = []
        
        if profile.get("age_range"):
            parts.append(f"年龄段: {profile['age_range']}")
        if profile.get("family_structure"):
            parts.append(f"家庭结构: {profile['family_structure']}")
        if profile.get("risk_preference"):
            parts.append(f"风险偏好: {profile['risk_preference']}")
        if profile.get("occupation"):
            parts.append(f"职业: {profile['occupation']}")
        if profile.get("monthly_expense"):
            parts.append(f"月支出: {profile['monthly_expense']}元")
        
        return ", ".join(parts) if parts else "暂无画像信息"
    
    async def _save_plan(
        self, 
        user_id: int, 
        plan_data: dict,
        focus_area: ActionCategory | None = None
    ) -> ActionPlan | None:
        """保存方案到数据库"""
        try:
            async for session in get_db_session():
                # 处理 Category: 确保是有效的枚举值
                category_val = plan_data.get("category")
                
                # Check validity
                is_valid = any(category_val == item.value for item in ActionCategory)
                
                if not is_valid:
                    # Fallback priority: 
                    # 1. focus_area (the intent that triggered this)
                    # 2. WEALTH_GROWTH (default)
                    if focus_area:
                        category_val = focus_area.value
                    else:
                        category_val = ActionCategory.WEALTH_GROWTH.value

                plan = ActionPlan(
                    user_id=user_id,
                    title=plan_data.get("title", "行动计划"),
                    category=category_val,
                    priority=plan_data.get("priority", "medium"),
                    summary=plan_data.get("summary", ""),
                    original_steps_snapshot=plan_data.get("steps", []),
                    expected_benefits=plan_data.get("expected_benefits", []),
                    potential_risks=plan_data.get("potential_risks", []),
                    confidence=plan_data.get("confidence", 0.5),
                    status="pending"
                )
                
                session.add(plan)
                await session.commit()
                await session.refresh(plan)
                
                return plan
                
        except Exception as e:
            logger.error(f"Error saving plan: {e}")
            return None


# 单例
_action_reasoner: ActionReasoner | None = None


def get_action_reasoner() -> ActionReasoner:
    """获取 ActionReasoner 实例"""
    global _action_reasoner
    if _action_reasoner is None:
        _action_reasoner = ActionReasoner()
    return _action_reasoner
