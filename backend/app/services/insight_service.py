"""
Phase 3: Cognitive Insight Worker (System 2)
Deep psychological profiling and adaptive advisor behavior
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlmodel import select

from app.core.config import settings
from app.core.database import get_db_session
from app.core.dependencies import get_llm_provider
from app.core.prompt_manager import prompt_manager
from app.services.llm_caller import LLMProvider
from app.models.chat import ChatMessage, MessageRole
from app.models.cognition import UserCognition

logger = logging.getLogger(__name__)


class InsightService:
    """
    System 2 Thinking: Slow, deep analysis of user psychology
    Analyzes conversation patterns to generate adaptive advisor strategies
    """

    def __init__(self, openai_api_key: str | None = None):
        self.llm = get_llm_provider()
        logger.info(f"InsightService initialized with LLM provider: {type(self.llm).__name__}")

    async def analyze_user_psychology(
        self, 
        user_id: int, 
        recent_messages: list[ChatMessage] | None = None,
        trigger_threshold: int = 5
    ) -> dict[str, Any]:
        """
        Analyze user's psychological profile from conversation history
        
        ✅ FIXED: Now uses incremental analysis to prevent duplicate memory extraction
        
        Args:
            user_id: User ID to analyze
            recent_messages: Optional pre-fetched messages (for optimization)
            trigger_threshold: Minimum number of messages before analysis
            
        Returns:
            Analysis result with risk_profile, sentiment, and advisor_note
        """
        try:
            logger.info(f"Starting psychology analysis for user {user_id}")
            
            # ✅ Step 1: Get the last analyzed message ID
            last_analyzed_id = await self._get_last_analyzed_message_id(user_id)
            
            # ✅ Step 2: Fetch ONLY NEW messages (not analyzed before)
            if recent_messages is None:
                recent_messages = await self._fetch_new_messages(
                    user_id, 
                    after_message_id=last_analyzed_id,
                    limit=50
                )
            
            # ✅ Step 3: Skip if no new messages
            if not recent_messages:
                logger.debug(f"No new messages for user {user_id} - skipping analysis")
                return {"skipped": True, "reason": "no_new_messages"}
            
            # ✅ Step 4: Skip if insufficient new messages
            # Note: We log this clearly so the user knows why LLM isn't called
            if len(recent_messages) < 3: 
                logger.debug(
                    f"Insufficient new messages ({len(recent_messages)}) for user {user_id} "
                    f"- skipping analysis (threshold=3)"
                )
                return {"skipped": True, "reason": "insufficient_new_messages"}
            
            # Perform psychological analysis using LLM interface
            logger.info(f"analyzing {len(recent_messages)} messages with {type(self.llm).__name__}")
            analysis = await self._analyze_with_llm(recent_messages)
            
            # Update UserCognition with insights
            await self._update_cognition_insights(user_id, analysis)
            
            # ✅ Step 5: Extract memories from NEW messages only
            await self._extract_and_store_key_memories(user_id, recent_messages)
            
            # ✅ Step 6: Update the last analyzed message ID
            if recent_messages:
                last_message_id = recent_messages[-1].id
                await self._update_last_analyzed_message_id(user_id, last_message_id)
            
            logger.info(
                f"✅ Completed incremental analysis for user {user_id}: "
                f"analyzed {len(recent_messages)} new messages"
            )
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user psychology for user {user_id}: {e}", exc_info=True)
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

    async def _get_last_analyzed_message_id(self, user_id: int) -> int | None:
        """Get the ID of the last analyzed message for this user"""
        try:
            async for session in get_db_session():
                statement = select(UserCognition).where(UserCognition.user_id == user_id)
                result = await session.execute(statement)
                cognition = result.scalar_one_or_none()
                
                if cognition:
                    return cognition.last_analyzed_message_id
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting last analyzed message ID: {e}")
            return None

    async def _fetch_new_messages(
        self, 
        user_id: int, 
        after_message_id: int | None = None,
        limit: int = 50
    ) -> list[ChatMessage]:
        """
        Fetch only NEW messages after the last analyzed message
        This is the KEY to preventing duplicate memory extraction
        """
        try:
            async for session in get_db_session():
                statement = (
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user_id)
                )
                
                # ✅ CRITICAL: Only fetch messages AFTER the last analyzed one
                if after_message_id is not None:
                    statement = statement.where(ChatMessage.id > after_message_id)
                    logger.info(f"Fetching messages after ID {after_message_id} for user {user_id}")
                else:
                    logger.info(f"Fetching all messages for user {user_id} (first analysis)")
                
                statement = (
                    statement
                    .order_by(ChatMessage.timestamp.desc())
                    .limit(limit)
                )
                
                result = await session.execute(statement)
                messages = result.scalars().all()
                
                # Return in chronological order (oldest first)
                new_messages = list(reversed(messages))
                logger.info(f"Fetched {len(new_messages)} new messages for user {user_id}")
                
                return new_messages
                
        except Exception as e:
            logger.error(f"Error fetching new messages for user {user_id}: {e}")
            return []

    async def _update_last_analyzed_message_id(self, user_id: int, message_id: int) -> None:
        """Update the last analyzed message ID after successful extraction"""
        try:
            async for session in get_db_session():
                statement = select(UserCognition).where(UserCognition.user_id == user_id)
                result = await session.execute(statement)
                cognition = result.scalar_one_or_none()
                
                if not cognition:
                    cognition = UserCognition(user_id=user_id)
                    session.add(cognition)
                
                cognition.last_analyzed_message_id = message_id
                cognition.last_memory_extraction_at = datetime.utcnow()
                cognition.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"✅ Updated last analyzed message ID to {message_id} for user {user_id}")
                
                break
                
        except Exception as e:
            logger.error(f"Error updating last analyzed message ID: {e}")

    async def _analyze_with_llm(self, messages: list[ChatMessage]) -> dict[str, Any]:
        """Perform deep psychological analysis using LLM"""
        
        # Prepare conversation history for analysis
        conversation_text = self._format_conversation_for_analysis(messages)
        
        # Load prompts from YAML configuration
        system_prompt = prompt_manager.render(
            category="insight",
            filename="psychology_analysis",
            key="system_instruction"
        )
        
        user_prompt = prompt_manager.render(
            category="insight",
            filename="psychology_analysis",
            key="user_instruction",
            conversation_text=conversation_text
        )

        try:
            # Call LLM for analysis
            response_text = await self.llm.generate(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Enhanced JSON parsing - handle new flattened structure
            analysis = self._parse_psychology_response(response_text)
            
            logger.info(f"LLM psychological analysis completed: {analysis.get('sentiment', 'unknown')}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return self._create_fallback_analysis(messages)

    def _parse_psychology_response(self, response_text: str) -> dict[str, Any]:
        """Enhanced JSON parsing for new flattened structure"""
        try:
            # Clean response text - remove markdown code blocks
            cleaned_json = response_text.strip()
            if "```json" in cleaned_json:
                json_start = cleaned_json.find("```json") + 7
                json_end = cleaned_json.find("```", json_start)
                cleaned_json = cleaned_json[json_start:json_end].strip()
            elif "```" in cleaned_json:
                json_start = cleaned_json.find("```") + 3
                json_end = cleaned_json.find("```", json_start)
                cleaned_json = cleaned_json[json_start:json_end].strip()
            
            analysis = json.loads(cleaned_json)
            
            # Validate required fields for new structure
            required_fields = ["risk_tolerance", "sentiment", "advisor_note"]
            for field in required_fields:
                if field not in analysis:
                    logger.warning(f"Missing required field: {field}")
                    
            # Ensure confidence_score is present
            if "confidence_score" not in analysis:
                analysis["confidence_score"] = 0.5
                
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response text: {response_text}")
            return self._create_fallback_analysis()
        except Exception as e:
            logger.error(f"Error parsing psychology response: {e}")
            return self._create_fallback_analysis()

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
        """Mock analysis for development environment - updated for new structure"""
        
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
        
        # Detect liquidity anxiety
        liquidity_keywords = ["手头紧", "没钱花", "转不开", "现金流压力", "资金周转"]
        has_liquidity_anxiety = any(keyword in all_text for keyword in liquidity_keywords)
        
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
            sentiment = "confident"
        else:
            sentiment = "neutral"
        
        # Determine liquidity anxiety
        if has_liquidity_anxiety:
            liquidity_anxiety = "high"
        elif has_stress:
            liquidity_anxiety = "medium"
        else:
            liquidity_anxiety = "low"
        
        return {
            "risk_tolerance": tolerance,
            "decision_style": "data_driven" if len(user_messages) > 5 else "intuitive",
            "sentiment": sentiment,
            "liquidity_anxiety": liquidity_anxiety,
            "confidence_score": 0.3 if has_stress else 0.7,
            "loss_aversion": "high" if is_conservative else "medium",
            "financial_literacy": "intermediate",
            "family_responsibility": "high" if "房贷" in all_text or "家庭" in all_text else "medium",
            "planning_horizon": "long" if "退休" in all_text or "长期" in all_text else "medium",
            "advisor_note": advisor_note,
            "key_concerns": self._extract_key_concerns(all_text)
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

    def _create_fallback_analysis(self, messages: list[ChatMessage] | None = None) -> dict[str, Any]:
        """Create a basic fallback analysis when LLM fails - updated for new structure"""
        return {
            "risk_tolerance": "moderate",
            "decision_style": "data_driven",
            "sentiment": "neutral",
            "liquidity_anxiety": "medium",
            "confidence_score": 0.5,
            "loss_aversion": "medium",
            "financial_literacy": "intermediate",
            "family_responsibility": "medium",
            "planning_horizon": "medium",
            "advisor_note": "用户画像分析中。建议采用标准的专业顾问方式，平衡风险与收益。",
            "key_concerns": ["资产配置", "风险管理"]
        }

    async def _update_cognition_insights(self, user_id: int, analysis: dict[str, Any]) -> None:
        """Update UserCognition table with psychological insights - updated for new structure"""
        try:
            async for session in get_db_session():
                # Get or create UserCognition record
                statement = select(UserCognition).where(UserCognition.user_id == user_id)
                result = await session.execute(statement)
                cognition = result.scalar_one_or_none()
                
                if not cognition:
                    cognition = UserCognition(user_id=user_id)
                    session.add(cognition)
                
                # Update risk profile with new flattened structure
                if not cognition.risk_profile:
                    cognition.risk_profile = {}
                
                # Store all psychological traits in risk_profile
                updated_fields = {
                    "tolerance": analysis.get("risk_tolerance"),
                    "decision_style": analysis.get("decision_style"),
                    "sentiment": analysis.get("sentiment"),
                    "liquidity_anxiety": analysis.get("liquidity_anxiety"),
                    "confidence_score": analysis.get("confidence_score", 0.5),
                    "loss_aversion": analysis.get("loss_aversion"),
                    "financial_literacy": analysis.get("financial_literacy"),
                    "family_responsibility": analysis.get("family_responsibility"),
                    "planning_horizon": analysis.get("planning_horizon"),
                    "last_analysis": datetime.utcnow().isoformat()
                }
                
                cognition.risk_profile.update(updated_fields)
                
                # ✅ CRITICAL: Flag JSON field as modified for SQLAlchemy to detect the change
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(cognition, 'risk_profile')
                
                # Update advisor note (direct mapping from new structure)
                advisor_note = analysis.get("advisor_note")
                if advisor_note:
                    cognition.advisor_note = advisor_note
                
                cognition.updated_at = datetime.utcnow()
                
                # Force flush to ensure changes are written
                session.add(cognition)
                await session.flush()
                await session.commit()
                
                # ✅ Enhanced logging to track complete update
                logger.info(f"✅ INSIGHT_UPDATE: Updated complete risk_profile for user {user_id}")
                logger.info(f"✅ INSIGHT_UPDATE: Fields updated: {list(updated_fields.keys())}")
                logger.info(f"✅ INSIGHT_UPDATE: Values: tolerance={updated_fields.get('tolerance')}, "
                           f"sentiment={updated_fields.get('sentiment')}, "
                           f"liquidity_anxiety={updated_fields.get('liquidity_anxiety')}")
                break
                
        except Exception as e:
            logger.error(f"Error updating cognition insights: {e}")
            raise
    
    async def _extract_and_store_key_memories(self, user_id: int, messages: list[ChatMessage]) -> None:
        """
        Phase 4: Extract key life events using LLM Semantic Analysis
        Store them in L3 Vector Memory for long-term recall
        """
        try:
            from app.services.memory_service import get_memory_service
            
            memory_service = get_memory_service()
            
            # Prepare conversation context
            user_messages = [msg.content for msg in messages if msg.role == MessageRole.USER]
            if not user_messages:
                return
            
            conversation_text = "\n".join(user_messages[-10:])  # Analyze last 10 messages
            
            # Use LLM for semantic extraction
            # We always use the LLM now, assuming configuration is correct
            logger.info(f"Extracting memories using {type(self.llm).__name__}")
            memories = await self._extract_memories_with_llm(conversation_text)
            
            # Store extracted memories with new fields
            for mem in memories:
                await memory_service.add_memory(
                    user_id=user_id,
                    text=mem["content"],
                    metadata={
                        "category": mem.get("category", "general"),
                        "tags": mem.get("tags", []),
                        "timeline": mem.get("timeline"),  # New field
                        "importance": mem.get("importance", "medium"),  # New field
                        "source": "llm_insight_extraction",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            
            if memories:
                logger.info(f"Extracted and stored {len(memories)} memories for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error extracting and storing key memories: {e}", exc_info=True)
    
    async def _extract_memories_with_llm(self, conversation_text: str) -> list[dict[str, Any]]:
        """Extract key memories using LLM semantic analysis - updated for new structure"""
        
        # Load prompts from YAML configuration
        system_prompt = prompt_manager.render(
            category="insight",
            filename="memory_extraction",
            key="system_instruction"
        )
        
        user_prompt = prompt_manager.render(
            category="insight",
            filename="memory_extraction",
            key="user_instruction",
            conversation_text=conversation_text
        )

        try:
            # Call LLM for memory extraction
            response_text = await self.llm.generate(
                messages=[{"role": "user", "content": user_prompt}],
                system_prompt=system_prompt,
                temperature=0.3
            )
            
            # Parse JSON response - handle markdown code blocks
            cleaned_json = response_text.strip()
            if "```json" in cleaned_json:
                json_start = cleaned_json.find("```json") + 7
                json_end = cleaned_json.find("```", json_start)
                cleaned_json = cleaned_json[json_start:json_end].strip()
            elif "```" in cleaned_json:
                json_start = cleaned_json.find("```") + 3
                json_end = cleaned_json.find("```", json_start)
                cleaned_json = cleaned_json[json_start:json_end].strip()
            
            memories = json.loads(cleaned_json)
            
            # Validate structure
            if not isinstance(memories, list):
                logger.warning(f"LLM returned non-list response: {type(memories)}")
                return []
            
            # Validate each memory has required fields and add defaults for new fields
            valid_memories = []
            for mem in memories:
                if isinstance(mem, dict) and "content" in mem:
                    valid_memories.append({
                        "content": mem["content"],
                        "category": mem.get("category", "general"),
                        "timeline": mem.get("timeline"),  # New field
                        "importance": mem.get("importance", "medium"),  # New field
                        "tags": mem.get("tags", [])
                    })
            
            logger.info(f"LLM extracted {len(valid_memories)} valid memories")
            return valid_memories
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM memory extraction response: {e}")
            logger.error(f"Response text: {response_text}")
            return []
        except Exception as e:
            logger.error(f"Error in LLM memory extraction: {e}")
            return []
    
    def _extract_memories_fallback(self, conversation_text: str) -> list[dict[str, Any]]:
        """Fallback keyword-based memory extraction for development/testing - updated with new fields"""
        
        memories = []
        text_lower = conversation_text.lower()
        
        # Family health issues
        if any(keyword in text_lower for keyword in ["生病", "住院", "手术", "治疗", "病情"]):
            memories.append({
                "content": f"用户提到家人健康问题，可能需要流动性资金应对医疗支出。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                "category": "health_concern",
                "timeline": None,
                "importance": "high",
                "tags": ["family", "health", "liquidity"]
            })
        
        # Major life plans
        if any(keyword in text_lower for keyword in ["买房", "购房", "换房", "学区房"]):
            memories.append({
                "content": f"用户计划购买房产，需要大额资金准备。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                "category": "major_purchase",
                "timeline": None,
                "importance": "high",
                "tags": ["real_estate", "planning", "liquidity"]
            })
        
        if any(keyword in text_lower for keyword in ["退休", "养老", "退休金"]):
            memories.append({
                "content": f"用户关注退休规划，需要长期稳健投资策略。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                "category": "retirement_planning",
                "timeline": None,
                "importance": "medium",
                "tags": ["retirement", "long_term", "conservative"]
            })
        
        if any(keyword in text_lower for keyword in ["孩子", "教育", "学费", "留学"]):
            memories.append({
                "content": f"用户关注子女教育，需要预留教育资金。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                "category": "education_planning",
                "timeline": None,
                "importance": "medium",
                "tags": ["education", "family", "planning"]
            })
        
        # Financial constraints
        if any(keyword in text_lower for keyword in ["房贷", "负债", "还款", "压力大"]):
            memories.append({
                "content": f"用户有房贷或债务压力，需要保守的投资策略和充足的流动性。时间: {datetime.utcnow().strftime('%Y-%m-%d')}",
                "category": "debt_constraint",
                "timeline": None,
                "importance": "high",
                "tags": ["debt", "constraint", "conservative"]
            })
        
        return memories

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
