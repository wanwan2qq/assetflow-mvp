"""
FamilyProfileService for Phase 4

家庭画像服务 - 管理用户的家庭成员图谱和生命周期事件

职责:
- 创建和更新家庭画像
- 管理家庭成员
- 追踪生命周期事件
- 支持从对话中自动提取家庭信息
"""

import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.core.database import get_db_session
from app.core.config import get_settings
from app.models.family import (
    FamilyProfile,
    FamilyMember,
    LifecycleEvent,
    FamilyRelation,
    LifecycleEventType
)

logger = logging.getLogger(__name__)


class FamilyProfileService:
    """
    家庭画像服务
    
    管理用户的家庭成员图谱和生命周期规划
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def get_family_profile(self, user_id: int) -> FamilyProfile | None:
        """获取用户的家庭画像"""
        try:
            async for session in get_db_session():
                stmt = select(FamilyProfile).where(FamilyProfile.user_id == user_id)
                result = await session.execute(stmt)
                return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting family profile: {e}")
            return None
    
    async def create_or_update_profile(
        self,
        user_id: int,
        members: list[dict] | None = None,
        lifecycle_events: list[dict] | None = None,
        total_income: float | None = None,
        total_expenses: float | None = None,
        financial_goals: list[str] | None = None
    ) -> FamilyProfile | None:
        """创建或更新家庭画像"""
        if not self.settings.ENABLE_FAMILY_PROFILE:
            logger.info("FamilyProfile disabled by feature flag")
            return None
        
        try:
            async for session in get_db_session():
                # 查找现有画像
                stmt = select(FamilyProfile).where(FamilyProfile.user_id == user_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if profile:
                    # 更新现有画像
                    if members is not None:
                        profile.members = members
                    if lifecycle_events is not None:
                        profile.lifecycle_events = lifecycle_events
                    if total_income is not None:
                        profile.total_income = total_income
                    if total_expenses is not None:
                        profile.total_expenses = total_expenses
                    if financial_goals is not None:
                        profile.financial_goals = financial_goals
                    profile.updated_at = datetime.utcnow()
                else:
                    # 创建新画像
                    profile = FamilyProfile(
                        user_id=user_id,
                        members=members or [],
                        lifecycle_events=lifecycle_events or [],
                        total_income=total_income,
                        total_expenses=total_expenses,
                        financial_goals=financial_goals or []
                    )
                    session.add(profile)
                
                await session.commit()
                await session.refresh(profile)
                
                logger.info(f"✅ [FAMILY_PROFILE] Updated profile for user {user_id}")
                return profile
                
        except Exception as e:
            logger.error(f"Error creating/updating family profile: {e}")
            return None
    
    async def add_family_member(
        self,
        user_id: int,
        member: FamilyMember
    ) -> bool:
        """添加家庭成员"""
        try:
            async for session in get_db_session():
                stmt = select(FamilyProfile).where(FamilyProfile.user_id == user_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    # 创建新画像
                    profile = FamilyProfile(
                        user_id=user_id,
                        members=[member.model_dump()]
                    )
                    session.add(profile)
                else:
                    # 添加成员
                    members = profile.members or []
                    members.append(member.model_dump())
                    profile.members = members
                    profile.updated_at = datetime.utcnow()
                    
                    # 标记 JSON 字段修改
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(profile, 'members')
                
                await session.commit()
                logger.info(f"✅ Added family member {member.relation} for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding family member: {e}")
            return False
    
    async def add_lifecycle_event(
        self,
        user_id: int,
        event: LifecycleEvent
    ) -> bool:
        """添加生命周期事件"""
        try:
            async for session in get_db_session():
                stmt = select(FamilyProfile).where(FamilyProfile.user_id == user_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    profile = FamilyProfile(
                        user_id=user_id,
                        lifecycle_events=[event.model_dump()]
                    )
                    session.add(profile)
                else:
                    events = profile.lifecycle_events or []
                    events.append(event.model_dump())
                    profile.lifecycle_events = events
                    profile.updated_at = datetime.utcnow()
                    
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(profile, 'lifecycle_events')
                
                await session.commit()
                logger.info(f"✅ Added lifecycle event {event.event_type} for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding lifecycle event: {e}")
            return False
    
    async def update_financial_summary(
        self,
        user_id: int,
        total_income: float | None = None,
        total_expenses: float | None = None
    ) -> bool:
        """更新家庭财务概况"""
        try:
            async for session in get_db_session():
                stmt = select(FamilyProfile).where(FamilyProfile.user_id == user_id)
                result = await session.execute(stmt)
                profile = result.scalar_one_or_none()
                
                if not profile:
                    profile = FamilyProfile(
                        user_id=user_id,
                        total_income=total_income,
                        total_expenses=total_expenses
                    )
                    session.add(profile)
                else:
                    if total_income is not None:
                        profile.total_income = total_income
                    if total_expenses is not None:
                        profile.total_expenses = total_expenses
                    profile.updated_at = datetime.utcnow()
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating financial summary: {e}")
            return False
    
    async def get_family_summary(self, user_id: int) -> dict:
        """获取家庭概况摘要"""
        profile = await self.get_family_profile(user_id)
        
        if not profile:
            return {
                "has_profile": False,
                "member_count": 0,
                "upcoming_events": 0
            }
        
        members = profile.members or []
        events = profile.lifecycle_events or []
        
        # 统计成员
        member_summary = {}
        for m in members:
            relation = m.get("relation", "other")
            member_summary[relation] = member_summary.get(relation, 0) + 1
        
        # 统计即将到来的事件
        upcoming = [
            e for e in events 
            if e.get("expected_date") and e.get("expected_date") >= datetime.now().strftime("%Y-%m")
        ]
        
        # 计算净收入
        net_income = None
        if profile.total_income and profile.total_expenses:
            net_income = profile.total_income - profile.total_expenses
        
        return {
            "has_profile": True,
            "member_count": len(members),
            "member_summary": member_summary,
            "upcoming_events": len(upcoming),
            "total_income": profile.total_income,
            "total_expenses": profile.total_expenses,
            "net_income": net_income,
            "financial_goals": profile.financial_goals or []
        }
    
    async def extract_family_info_from_profile(
        self,
        user_profile_data: dict
    ) -> dict:
        """
        从用户画像数据中提取家庭信息
        
        用于从 information_extraction 结果中自动填充家庭画像
        """
        family_info = {
            "members": [],
            "lifecycle_events": []
        }
        
        # 根据家庭结构推断成员
        family_structure = user_profile_data.get("family_structure", "")
        
        if family_structure == "single":
            family_info["members"].append({
                "relation": FamilyRelation.SELF.value,
                "age": None,
                "occupation": user_profile_data.get("occupation")
            })
        elif family_structure == "married":
            family_info["members"].append({
                "relation": FamilyRelation.SELF.value,
                "occupation": user_profile_data.get("occupation")
            })
            family_info["members"].append({
                "relation": FamilyRelation.SPOUSE.value
            })
        elif family_structure == "married_with_kids":
            family_info["members"].append({
                "relation": FamilyRelation.SELF.value,
                "occupation": user_profile_data.get("occupation")
            })
            family_info["members"].append({
                "relation": FamilyRelation.SPOUSE.value
            })
            family_info["members"].append({
                "relation": FamilyRelation.CHILD.value
            })
            # 添加教育规划事件
            family_info["lifecycle_events"].append({
                "event_type": LifecycleEventType.EDUCATION.value,
                "priority": "high"
            })
        
        return family_info


# 单例
_family_profile_service: FamilyProfileService | None = None


def get_family_profile_service() -> FamilyProfileService:
    """获取 FamilyProfileService 实例"""
    global _family_profile_service
    if _family_profile_service is None:
        _family_profile_service = FamilyProfileService()
    return _family_profile_service
