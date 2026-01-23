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
from typing import Any

from sqlmodel import Session, select

from app.core.database import get_db_session
from app.core.config import get_settings
from app.core.prompt_manager import prompt_manager
from app.models.action_plan import (
    ActionPlan, 
    ActionCategory, 
    ActionPriority, 
    ActionStep
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
        
        Args:
            user_id: 用户ID
            focus_area: 可选的聚焦领域
            
        Returns:
            生成的 ActionPlan 列表
        """
        if not self.settings.ENABLE_ACTION_REASONER:
            logger.info("ActionReasoner disabled by feature flag")
            return []
        
        try:
            logger.info(f"🎯 [ACTION_REASONER] Generating plan for user {user_id}, focus={focus_area}")
            
            # Step 1: 加载用户上下文
            user_context = await self._load_user_context(user_id)
            if not user_context:
                logger.warning(f"No context found for user {user_id}")
                return []
            
            # Step 2: 分析资产配置缺口
            gaps = await self.analyze_gaps(user_id)
            
            # Step 3: 检索相关知识
            knowledge_context = await self._retrieve_relevant_knowledge(
                user_context, 
                focus_area
            )
            
            # Step 4: 使用 LLM 生成方案
            plan = await self._generate_plan_with_llm(
                user_context,
                gaps,
                knowledge_context,
                focus_area
            )
            
            if plan:
                # Step 5: 存储方案
                saved_plan = await self._save_plan(user_id, plan)
                logger.info(f"✅ [ACTION_REASONER] Generated plan: {saved_plan.title}")
                return [saved_plan] if saved_plan else []
            
            return []
            
        except Exception as e:
            logger.error(f"❌ [ACTION_REASONER] Error generating plan: {e}")
            return []
    
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
            
            response = ""
            async for chunk in llm_provider.generate_stream(messages, system_prompt):
                response += chunk
            
            # 解析 JSON
            try:
                # 提取 JSON
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                    return plan_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
            
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
    
    async def _save_plan(self, user_id: int, plan_data: dict) -> ActionPlan | None:
        """保存方案到数据库"""
        try:
            async for session in get_db_session():
                plan = ActionPlan(
                    user_id=user_id,
                    title=plan_data.get("title", "行动计划"),
                    category=plan_data.get("category", "asset_allocation"),
                    priority=plan_data.get("priority", "medium"),
                    summary=plan_data.get("summary", ""),
                    steps=plan_data.get("steps", []),
                    expected_benefits=plan_data.get("expected_benefits", []),
                    potential_risks=plan_data.get("potential_risks", []),
                    confidence=plan_data.get("confidence", 0.5)
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
