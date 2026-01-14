"""
Phase 3: Cognitive Insight Worker (System 2)
Deep psychological profiling and adaptive advisor behavior
"""

import json
import logging
from datetime import datetime
from typing import Any

from langchain_openai import ChatOpenAI
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_db_session
from app.models.chat import ChatMessage, MessageRole
from app.models.cognition import UserCognition

logger = logging.getLogger(__name__)


class InsightService:
    """
    System 2 Thinking: Slow, deep analysis of user psychology
    Analyzes conversation patterns to generate adaptive advisor strategies
    """

    def __init__(self, openai_api_key: str | None = None):
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        
        # Check if we have a valid OpenAI API key
        self.has_real_openai_key = (
            self.openai_api_key 
            and not self.openai_api_key.startswith("sk-mock")
            and self.openai_api_key != "mock-key"
        )
        
        if not self.has_real_openai_key:
            logger.warning("No valid OpenAI API key - insight service will use mock analysis")
            self.llm = None
        else:
            # Initialize LLM for psychological analysis
            llm_kwargs = {
                "model": "deepseek-chat",
                "temperature": 0.3,  # Lower temperature for more consistent analysis
                "api_key": self.openai_api_key,
            }
            
            if settings.OPENAI_API_BASE:
                llm_kwargs["base_url"] = settings.OPENAI_API_BASE
            
            self.llm = ChatOpenAI(**llm_kwargs)

    async def analyze_user_psychology(
        self, 
        user_id: int, 
        recent_messages: list[ChatMessage] | None = None,
        trigger_threshold: int = 5
    ) -> dict[str, Any]:
        """
        Analyze user's psychological profile from conversation history
        
        Args:
            user_id: User ID to analyze
            recent_messages: Optional pre-fetched messages (for optimization)
            trigger_threshold: Minimum number of messages before analysis
            
        Returns:
            Analysis result with risk_profile, sentiment, and advisor_note
        """
        try:
            # Fetch recent conversation history if not provided
            if recent_messages is None:
                recent_messages = await self._fetch_recent_messages(user_id, limit=50)
            
            # Skip analysis if insufficient conversation data
            if len(recent_messages) < trigger_threshold:
                logger.debug(f"Insufficient messages ({len(recent_messages)}) for user {user_id} - skipping analysis")
                return {"skipped": True, "reason": "insufficient_data"}
            
            # Perform psychological analysis
            if self.has_real_openai_key and self.llm:
                analysis = await self._analyze_with_llm(recent_messages)
            else:
                analysis = self._analyze_mock(recent_messages)
            
            # Update UserCognition with insights
            await self._update_cognition_insights(user_id, analysis)
            
            # Phase 4: Extract and store key memories in L3 Vector Memory
            await self._extract_and_store_key_memories(user_id, recent_messages)
            
            logger.info(f"Completed psychological analysis for user {user_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user psychology for user {user_id}: {e}")
            return {"error": str(e)}

    async def _fetch_recent_messages(self, user_id: int, limit: int = 50) -> list[ChatMessage]:
        """Fetch recent chat messages for analysis"""
        try:
            async for session in get_db_session():
                statement = (
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user_id)
                    .order_by(ChatMessage.timestamp.desc())
                    .limit(limit)
                )
                
                result = await session.execute(statement)
                messages = result.scalars().all()
                
                # Return in chronological order (oldest first)
                return list(reversed(messages))
                
        except Exception as e:
            logger.error(f"Error fetching messages for user {user_id}: {e}")
            return []

    async def _analyze_with_llm(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Perform deep psychological analysis using LLM"""
        
        # Prepare conversation history for analysis
        conversation_text = self._format_conversation_for_analysis(messages)
        
        # System prompt for psychological profiling
        system_prompt = """你是一位资深的财务心理学专家和行为金融学顾问。你的任务是分析用户的对话内容，深入理解他们的：

1. **风险承受能力 (Risk Tolerance)**
   - conservative (保守型): 害怕损失，优先保本
   - moderate (稳健型): 平衡风险与收益
   - aggressive (激进型): 追求高收益，能承受波动

2. **决策风格 (Decision Style)**
   - analytical (分析型): 需要详细数据和逻辑推理
   - intuitive (直觉型): 依赖感觉和经验
   - cautious (谨慎型): 需要反复确认，害怕犯错
   - impulsive (冲动型): 快速决策，容易受情绪影响

3. **当前情绪状态 (Current Sentiment)**
   - anxious (焦虑): 担心、压力大
   - confident (自信): 对财务状况有信心
   - confused (困惑): 不知道该怎么办
   - optimistic (乐观): 对未来充满希望
   - stressed (压力): 财务压力明显

4. **关键心理特征 (Key Psychological Traits)**
   - 对损失的敏感度
   - 对不确定性的容忍度
   - 财务知识水平
   - 家庭责任感
   - 长期规划能力

**分析要求：**
- 仔细阅读用户的每一句话，注意语气、用词、情绪表达
- 识别隐含的担忧、恐惧、期望
- 基于具体对话内容给出判断，不要臆测
- 生成实用的顾问策略建议

**输出格式 (JSON)：**
```json
{
  "risk_profile": {
    "tolerance": "conservative|moderate|aggressive",
    "decision_style": "analytical|intuitive|cautious|impulsive",
    "confidence_level": "low|medium|high"
  },
  "current_sentiment": "anxious|confident|confused|optimistic|stressed",
  "psychological_traits": {
    "loss_aversion": "high|medium|low",
    "uncertainty_tolerance": "high|medium|low",
    "financial_literacy": "beginner|intermediate|advanced",
    "family_responsibility": "high|medium|low",
    "planning_horizon": "short|medium|long"
  },
  "advisor_note_internal": "内部策略建议：如何调整沟通方式、语气、建议类型等。这是给AI顾问看的，用户看不到。",
  "key_concerns": ["用户最关心的3-5个问题"],
  "recommended_approach": "建议的沟通策略和建议方向"
}
```

**重要提示：**
- advisor_note_internal 必须具体、可操作，例如："用户对房贷压力很大，建议避免激进投资建议，多强调稳健保本方案，语气要温和安抚"
- 如果对话内容不足以判断某个维度，使用 "unknown" 或 null
- 基于事实分析，不要过度解读
"""

        user_prompt = f"""请分析以下用户对话，生成心理画像和顾问策略：

【对话历史】
{conversation_text}

请严格按照JSON格式输出分析结果。"""

        try:
            # Call LLM for analysis
            messages_for_llm = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = await self.llm.ainvoke(messages_for_llm)
            response_text = response.content
            
            # Parse JSON response
            # Try to extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            analysis = json.loads(response_text)
            
            logger.info(f"LLM psychological analysis completed: {analysis.get('current_sentiment', 'unknown')}")
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            # Return a basic analysis as fallback
            return self._create_fallback_analysis(messages)
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return self._create_fallback_analysis(messages)

    def _format_conversation_for_analysis(self, messages: list[ChatMessage]) -> str:
        """Format conversation history for LLM analysis"""
        formatted_lines = []
        
        for msg in messages[-20:]:  # Last 20 messages for context
            role = "用户" if msg.role == MessageRole.USER else "AI顾问"
            # Remove widget tags for cleaner analysis
            content = msg.content
            if "<WIDGET:" in content:
                # Simple removal of widget tags
                import re
                content = re.sub(r'<WIDGET:[^>]+>', '', content)
            
            formatted_lines.append(f"{role}: {content.strip()}")
        
        return "\n\n".join(formatted_lines)

    def _analyze_mock(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Mock analysis for development environment"""
        
        # Simple keyword-based analysis for development
        user_messages = [msg.content.lower() for msg in messages if msg.role == MessageRole.USER]
        all_text = " ".join(user_messages)
        
        # Detect anxiety/stress keywords
        stress_keywords = ["压力", "焦虑", "担心", "害怕", "困难", "亏损", "负债", "房贷"]
        has_stress = any(keyword in all_text for keyword in stress_keywords)
        
        # Detect conservative keywords
        conservative_keywords = ["保本", "稳健", "安全", "保守", "不想冒险"]
        is_conservative = any(keyword in all_text for keyword in conservative_keywords)
        
        # Detect aggressive keywords
        aggressive_keywords = ["高收益", "股票", "激进", "冒险", "快速增长"]
        is_aggressive = any(keyword in all_text for keyword in aggressive_keywords)
        
        # Determine risk tolerance
        if is_conservative or has_stress:
            tolerance = "conservative"
            advisor_note = "用户表现出保守倾向或财务压力。建议：避免激进投资建议，多强调稳健保本方案，语气要温和安抚。重点推荐债券、银行理财等低风险产品。"
        elif is_aggressive:
            tolerance = "aggressive"
            advisor_note = "用户愿意承担风险追求高收益。建议：可以介绍成长型投资机会，但要充分提示风险。平衡激进与稳健的配置。"
        else:
            tolerance = "moderate"
            advisor_note = "用户风险偏好适中。建议：提供平衡的资产配置方案，兼顾收益与安全。标准普尔四象限模型是理想选择。"
        
        # Determine sentiment
        if has_stress:
            sentiment = "anxious"
        elif is_aggressive:
            sentiment = "optimistic"
        else:
            sentiment = "neutral"
        
        return {
            "risk_profile": {
                "tolerance": tolerance,
                "decision_style": "analytical" if len(user_messages) > 5 else "intuitive",
                "confidence_level": "low" if has_stress else "medium"
            },
            "current_sentiment": sentiment,
            "psychological_traits": {
                "loss_aversion": "high" if is_conservative else "medium",
                "uncertainty_tolerance": "low" if has_stress else "medium",
                "financial_literacy": "intermediate",
                "family_responsibility": "high" if "房贷" in all_text or "家庭" in all_text else "medium",
                "planning_horizon": "long" if "退休" in all_text or "长期" in all_text else "medium"
            },
            "advisor_note_internal": advisor_note,
            "key_concerns": self._extract_key_concerns(all_text),
            "recommended_approach": "基于用户的风险偏好和当前情绪状态，采用温和、专业的沟通方式"
        }

    def _extract_key_concerns(self, text: str) -> list[str]:
        """Extract key concerns from user messages"""
        concerns = []
        
        concern_keywords = {
            "房贷压力": ["房贷", "还贷", "月供"],
            "投资风险": ["亏损", "风险", "波动"],
            "资产配置": ["怎么投", "如何配置", "资产分配"],
            "退休规划": ["退休", "养老", "晚年"],
            "子女教育": ["教育", "孩子", "学费"]
        }
        
        for concern, keywords in concern_keywords.items():
            if any(keyword in text for keyword in keywords):
                concerns.append(concern)
        
        return concerns[:5]  # Top 5 concerns

    def _create_fallback_analysis(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Create a basic fallback analysis when LLM fails"""
        return {
            "risk_profile": {
                "tolerance": "moderate",
                "decision_style": "analytical",
                "confidence_level": "medium"
            },
            "current_sentiment": "neutral",
            "psychological_traits": {
                "loss_aversion": "medium",
                "uncertainty_tolerance": "medium",
                "financial_literacy": "intermediate",
                "family_responsibility": "medium",
                "planning_horizon": "medium"
            },
            "advisor_note_internal": "用户画像分析中。建议采用标准的专业顾问方式，平衡风险与收益。",
            "key_concerns": ["资产配置", "风险管理"],
            "recommended_approach": "专业、温和、平衡的沟通方式"
        }

    async def _update_cognition_insights(self, user_id: int, analysis: dict[str, Any]) -> None:
        """Update UserCognition table with psychological insights"""
        try:
            async for session in get_db_session():
                # Get or create UserCognition record
                statement = select(UserCognition).where(UserCognition.user_id == user_id)
                result = await session.execute(statement)
                cognition = result.scalar_one_or_none()
                
                if not cognition:
                    cognition = UserCognition(user_id=user_id)
                    session.add(cognition)
                
                # Update risk profile
                risk_profile_data = analysis.get("risk_profile", {})
                if risk_profile_data:
                    if not cognition.risk_profile:
                        cognition.risk_profile = {}
                    
                    cognition.risk_profile.update({
                        "tolerance": risk_profile_data.get("tolerance"),
                        "decision_style": risk_profile_data.get("decision_style"),
                        "confidence_level": risk_profile_data.get("confidence_level"),
                        "current_sentiment": analysis.get("current_sentiment"),
                        "last_analysis": datetime.utcnow().isoformat()
                    })
                    
                    # Merge psychological traits
                    psychological_traits = analysis.get("psychological_traits", {})
                    if psychological_traits:
                        cognition.risk_profile.update(psychological_traits)
                
                # Update advisor note (internal strategy)
                advisor_note = analysis.get("advisor_note_internal")
                if advisor_note:
                    cognition.advisor_note = advisor_note
                
                cognition.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Updated cognition insights for user {user_id}")
                break
                
        except Exception as e:
            logger.error(f"Error updating cognition insights: {e}")
            raise
    
    async def _extract_and_store_key_memories(self, user_id: int, messages: list[ChatMessage]) -> None:
        """
        Phase 4: Extract key life events and constraints from conversation
        Store them in L3 Vector Memory for long-term recall
        """
        try:
            from app.services.memory_service import get_memory_service
            
            memory_service = get_memory_service()
            
            # Analyze recent messages for key memories
            user_messages = [msg.content for msg in messages if msg.role == MessageRole.USER]
            all_text = " ".join(user_messages[-10:])  # Last 10 user messages
            
            # Detect key life events and constraints
            key_events = []
            
            # Family health issues
            if any(keyword in all_text for keyword in ["生病", "住院", "手术", "治疗", "病情"]):
                key_events.append({
                    "content": f"用户提到家人健康问题，可能需要流动性资金应对医疗支出。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "category": "health_concern",
                    "tags": ["family", "health", "liquidity"]
                })
            
            # Major life plans
            if any(keyword in all_text for keyword in ["买房", "购房", "换房", "学区房"]):
                key_events.append({
                    "content": f"用户计划购买房产，需要大额资金准备。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "category": "major_purchase",
                    "tags": ["real_estate", "planning", "liquidity"]
                })
            
            if any(keyword in all_text for keyword in ["退休", "养老", "退休金"]):
                key_events.append({
                    "content": f"用户关注退休规划，需要长期稳健投资策略。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "category": "retirement_planning",
                    "tags": ["retirement", "long_term", "conservative"]
                })
            
            if any(keyword in all_text for keyword in ["孩子", "教育", "学费", "留学"]):
                key_events.append({
                    "content": f"用户关注子女教育，需要预留教育资金。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "category": "education_planning",
                    "tags": ["education", "family", "planning"]
                })
            
            # Financial constraints
            if any(keyword in all_text for keyword in ["房贷", "负债", "还款", "压力大"]):
                key_events.append({
                    "content": f"用户有房贷或债务压力，需要保守的投资策略和充足的流动性。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                    "category": "debt_constraint",
                    "tags": ["debt", "constraint", "conservative"]
                })
            
            # Store key memories
            for event in key_events:
                await memory_service.add_memory(
                    user_id=user_id,
                    text=event["content"],
                    metadata={
                        "category": event["category"],
                        "tags": event["tags"],
                        "source": "insight_analysis",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            if key_events:
                logger.info(f"Stored {len(key_events)} key memories for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error extracting and storing key memories: {e}")

    async def get_advisor_strategy(self, user_id: int) -> str | None:
        """
        Get the current advisor strategy note for a user
        This is used by the chat agent to adjust its behavior
        """
        try:
            async for session in get_db_session():
                statement = select(UserCognition).where(UserCognition.user_id == user_id)
                result = await session.execute(statement)
                cognition = result.scalar_one_or_none()
                
                if cognition and cognition.advisor_note:
                    return cognition.advisor_note
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting advisor strategy: {e}")
            return None


# Global service instance
_insight_service: InsightService | None = None


def get_insight_service() -> InsightService:
    """Get or create insight service instance"""
    global _insight_service
    if _insight_service is None:
        _insight_service = InsightService()
    return _insight_service
