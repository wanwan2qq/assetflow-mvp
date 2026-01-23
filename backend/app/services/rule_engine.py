"""
Rule Engine - Policy Constraint Evaluation

This service evaluates policy rules against user profiles:
- Purchase restrictions (限购政策)
- Loan policies (贷款政策)
- Provident fund policies (公积金政策)

AI Coding Guidance:
- Rules are evaluated against PolicyKnowledge conditions
- Higher priority rules take precedence
- Use prompt_manager for constraint text generation
"""

import logging
from typing import Any

from sqlmodel import select
from sqlalchemy import and_

from app.core.database import get_db_session
from app.core.prompt_manager import prompt_manager
from app.models.knowledge import (
    KnowledgeCategory,
    KnowledgeStatus,
    LoanPolicy,
    PolicyKnowledge,
    PurchaseRestriction,
    RuleResult,
)

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    规则引擎
    
    基于政策知识库评估用户是否满足特定规则条件
    """
    
    # 默认城市政策 (当知识库无数据时使用)
    DEFAULT_POLICIES = {
        "purchase_limit": {
            "北京": {"local": 2, "non_local": 1, "social_security_months": 60},
            "上海": {"local": 2, "non_local": 1, "social_security_months": 60},
            "深圳": {"local": 2, "non_local": 1, "social_security_months": 60},
            "广州": {"local": 2, "non_local": 1, "social_security_months": 12},
        },
        "loan_policy": {
            "first_home": {"down_payment": 0.3, "rate": 0.038},
            "second_home": {"down_payment": 0.4, "rate": 0.042},
        }
    }
    
    async def evaluate(
        self,
        user_profile: dict,
        city: str
    ) -> list[RuleResult]:
        """
        评估用户适用的政策规则
        
        Args:
            user_profile: 用户画像 (hukou, properties_owned, etc.)
            city: 目标城市
            
        Returns:
            匹配的规则列表
        """
        results: list[RuleResult] = []
        
        async for session in get_db_session():
            # 查询该城市的有效政策规则
            stmt = select(PolicyKnowledge).where(
                and_(
                    PolicyKnowledge.status == KnowledgeStatus.ACTIVE,
                    PolicyKnowledge.conditions.isnot(None)
                )
            ).where(
                # city 为 None 表示全国适用，或者匹配指定城市
                (PolicyKnowledge.city.is_(None)) | (PolicyKnowledge.city == city)
            ).order_by(PolicyKnowledge.priority.desc())
            
            policies = (await session.execute(stmt)).scalars().all()
            
            for policy in policies:
                is_matched = self._evaluate_conditions(
                    policy.conditions,
                    user_profile
                )
                
                # 生成约束描述文本
                constraint_text = self._generate_constraint_text(
                    policy, 
                    city,
                    is_matched
                )
                
                results.append(RuleResult(
                    rule_id=policy.id,
                    rule_name=policy.title,
                    is_matched=is_matched,
                    constraint_text=constraint_text,
                    priority=policy.priority,
                    city=policy.city
                ))
        
        return results
    
    def get_purchase_restrictions(
        self,
        city: str,
        hukou: str,
        properties_owned: int
    ) -> PurchaseRestriction:
        """
        获取限购政策
        
        Args:
            city: 城市
            hukou: 户籍类型 (local/non_local)
            properties_owned: 已拥有房产数量
            
        Returns:
            PurchaseRestriction 限购政策结果
        """
        # 获取城市政策
        city_policy = self.DEFAULT_POLICIES["purchase_limit"].get(city, {})
        
        is_local = hukou == "local"
        
        if is_local:
            max_properties = city_policy.get("local", 2)
            requirements = ["本地户籍"]
            restrictions = []
        else:
            max_properties = city_policy.get("non_local", 1)
            ss_months = city_policy.get("social_security_months", 60)
            requirements = [f"连续{ss_months}个月社保或纳税"]
            restrictions = ["非本地户籍限购"]
        
        can_purchase = properties_owned < max_properties
        
        if not can_purchase:
            restrictions.append(f"已达到限购上限({max_properties}套)")
        
        return PurchaseRestriction(
            city=city,
            can_purchase=can_purchase,
            max_properties=max_properties,
            requirements=requirements,
            restrictions=restrictions
        )
    
    def get_loan_policy(
        self,
        city: str,
        is_first_home: bool,
        loan_type: str = "commercial"
    ) -> LoanPolicy:
        """
        获取贷款政策
        
        Args:
            city: 城市
            is_first_home: 是否首套房
            loan_type: 贷款类型 (commercial/provident_fund)
            
        Returns:
            LoanPolicy 贷款政策结果
        """
        policy_key = "first_home" if is_first_home else "second_home"
        policy = self.DEFAULT_POLICIES["loan_policy"].get(policy_key, {})
        
        down_payment = policy.get("down_payment", 0.3)
        rate = policy.get("rate", 0.038)
        
        # 公积金贷款利率更低
        if loan_type == "provident_fund":
            rate = 0.031 if is_first_home else 0.0325
            down_payment = max(0.2, down_payment - 0.1)  # 公积金首付更低
        
        notes = []
        if is_first_home:
            notes.append("首套房优惠政策适用")
        else:
            notes.append("二套房政策适用，首付比例更高")
        
        if loan_type == "provident_fund":
            notes.append("公积金贷款利率优惠")
        
        return LoanPolicy(
            city=city,
            max_ltv=1 - down_payment,
            min_down_payment=down_payment,
            base_rate=rate,
            notes=notes
        )
    
    def _evaluate_conditions(
        self,
        conditions: dict,
        user_profile: dict
    ) -> bool:
        """
        评估条件是否匹配
        
        支持的条件操作符:
        - eq: 等于
        - ne: 不等于
        - lt: 小于
        - le: 小于等于
        - gt: 大于
        - ge: 大于等于
        - in: 在列表中
        """
        if not conditions:
            return True
        
        for field, condition in conditions.items():
            user_value = user_profile.get(field)
            
            if user_value is None:
                continue  # 用户未提供该字段，跳过
            
            if isinstance(condition, dict):
                # 复杂条件
                for op, expected in condition.items():
                    if not self._check_operator(op, user_value, expected):
                        return False
            else:
                # 简单等于条件
                if user_value != condition:
                    return False
        
        return True
    
    def _check_operator(self, op: str, value: Any, expected: Any) -> bool:
        """检查单个操作符"""
        ops = {
            "eq": lambda v, e: v == e,
            "ne": lambda v, e: v != e,
            "lt": lambda v, e: v < e,
            "le": lambda v, e: v <= e,
            "gt": lambda v, e: v > e,
            "ge": lambda v, e: v >= e,
            "in": lambda v, e: v in e,
        }
        
        op_func = ops.get(op)
        if op_func:
            try:
                return op_func(value, expected)
            except (TypeError, ValueError):
                return False
        
        return False
    
    def _generate_constraint_text(
        self,
        policy: PolicyKnowledge,
        city: str,
        is_matched: bool
    ) -> str:
        """生成规则约束描述文本"""
        try:
            return prompt_manager.render(
                category="rule",
                filename="policy_constraint",
                key="constraint_template",
                city=city or "全国",
                constraint_text=policy.summary or policy.title
            )
        except Exception as e:
            logger.warning(f"Failed to render constraint text: {e}")
            return f"【{policy.title}】{policy.summary or ''}"


# ============================================================================
# Singleton Factory
# ============================================================================

_rule_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    """获取 RuleEngine 单例"""
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
