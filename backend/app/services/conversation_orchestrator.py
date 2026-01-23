"""
Conversation Orchestrator - Main entry point for chat message processing

This module orchestrates:
1. Context loading and management
2. LLM calls through LLMProvider
3. UI component injection
4. Background task triggering

AI Coding Guidance:
- This is the "conductor" that coordinates other modules
- Don't implement business logic here; delegate to specialized services
- Background tasks should be fire-and-forget with proper error isolation
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from app.core.config import get_settings
from app.core.prompt_manager import prompt_manager
from app.models.context import ConversationContext
from app.models.knowledge import KnowledgeChunk
from app.services.context_manager import ContextManager
from app.services.llm_caller import LLMProvider
from app.services.ui_component_injector import get_ui_component_injector

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """
    Main orchestrator for conversation processing.
    
    Replaces the monolithic ChatAgent with a clean, coordinated approach.
    All heavy lifting is delegated to specialized modules.
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        context_manager: ContextManager
    ):
        """
        Initialize the orchestrator.
        
        Args:
            llm_provider: LLM provider for generating responses
            context_manager: Context manager for state management
        """
        self.llm_provider = llm_provider
        self.context_manager = context_manager
        self.ui_injector = get_ui_component_injector()
        
        logger.info("✅ ConversationOrchestrator initialized")
    
    async def process_message(
        self, 
        user_id: int, 
        message: str
    ) -> AsyncIterator[str]:
        """
        Main entry point for processing user messages.
        
        This is the method called by the WebSocket handler.
        
        Args:
            user_id: User ID
            message: User message text
            
        Yields:
            str: Response chunks for streaming
        """
        # Import here to avoid circular imports
        from app.services.chat_history_service import get_chat_history_service
        
        chat_history_service = get_chat_history_service()
        
        # Save user message immediately
        try:
            await chat_history_service.save_user_message(user_id, message)
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
        
        try:
            # Step 1: Load context
            context = await self.context_manager.get_context(user_id)
            
            # Step 2: Add message to context
            context.add_message("user", message)
            self.context_manager.update_in_memory(user_id, context)
            
            # Step 3: RAG Augmentation (if applicable)
            rag_context, rag_sources = await self._augment_with_rag(message, context)
            
            # Step 4: Build prompt and generate response
            if rag_context:
                # Use RAG-augmented system prompt
                system_prompt = rag_context
                logger.info(f"🔍 [RAG] Using augmented prompt with {len(rag_sources)} sources")
            else:
                # Use regular system prompt
                system_prompt = self._get_system_prompt(context)
            
            messages = self._build_messages(context)
            
            full_response = ""
            async for chunk in self.llm_provider.generate_stream(messages, system_prompt):
                full_response += chunk
                yield chunk
            
            # Step 5: Add AI response to context
            context.add_message("assistant", full_response)
            self.context_manager.update_in_memory(user_id, context)
            
            # Step 6: Inject UI components
            enhanced_response, ui_components = await self.ui_injector.extract_and_inject(
                full_response, context, user_id
            )
            
            if enhanced_response != full_response:
                # Yield the UI component part
                yield enhanced_response[len(full_response):]
            
            # Step 7: Save AI message
            try:
                await chat_history_service.save_ai_message(user_id, enhanced_response)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")
            
            # Step 8: Trigger background extraction (fire-and-forget)
            asyncio.create_task(
                self._background_extraction_pipeline(message, user_id, context)
            )
            
            logger.info(f"✅ Message processed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"
    
    def _get_system_prompt(self, context: ConversationContext) -> str:
        """Get system prompt based on context."""
        try:
            return prompt_manager.render(
                category="chat",
                filename="agent_system",
                key="system_instruction"
            )
        except Exception as e:
            logger.warning(f"Failed to load prompt from YAML: {e}")
            return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """Fallback system prompt."""
        return """你是AssetFlow的首席资产配置专家，一位温暖、专业、值得信赖的财务顾问。

你的核心职责：
1. 通过对话了解用户的资产状况和财务目标
2. 基于标准普尔四象限模型提供专业的资产配置建议
3. 用温暖和同理心回应用户的财务焦虑

对话原则：
- 每次只问一个问题，不要连续追问
- 先认可用户分享的信息，再引导下一步
- 用emoji增加亲和力，但不要过度使用

严格遵守：
- 不要在回复中包含<Thought>标签，这是内部思考过程
- 不要重复询问用户已经回答过的问题"""
    
    # =========================================================================
    # RAG Augmentation Methods
    # =========================================================================
    
    # Keywords that trigger RAG retrieval for policy-related questions
    RAG_TRIGGER_KEYWORDS = [
        # 购房政策
        "政策", "限购", "购房资格", "买房条件", "购房条件",
        # 公积金
        "公积金", "住房公积金", "公积金贷款", "公积金提取",
        # 贷款
        "首付", "贷款", "房贷", "利率", "还款", "月供", "商贷", "组合贷",
        # 税费
        "税费", "契税", "个税", "增值税", "印花税",
        # 其他政策
        "户口", "社保", "纳税", "限售", "摇号", "积分", "人才"
    ]
    
    def _should_use_rag(self, message: str) -> bool:
        """
        Determine if the message should trigger RAG retrieval.
        
        Only policy-related questions benefit from RAG to avoid unnecessary overhead.
        """
        settings = get_settings()
        if not settings.ENABLE_RAG_AUGMENTATION:
            return False
        
        # Check if message contains any trigger keywords
        message_lower = message.lower()
        for keyword in self.RAG_TRIGGER_KEYWORDS:
            if keyword in message_lower:
                logger.debug(f"🔍 [RAG] Triggered by keyword: {keyword}")
                return True
        
        # Also trigger for question patterns about buying/property
        question_patterns = ["怎么", "如何", "可以", "能不能", "什么", "多少", "哪些", "需要", "条件"]
        property_keywords = ["房", "买", "购", "住", "置业"]
        
        has_question = any(p in message for p in question_patterns)
        has_property = any(k in message for k in property_keywords)
        
        if has_question and has_property:
            logger.debug(f"🔍 [RAG] Triggered by property question pattern")
            return True
        
        return False
    
    async def _augment_with_rag(
        self, 
        message: str, 
        context: ConversationContext
    ) -> tuple[str | None, list[KnowledgeChunk]]:
        """
        Use RAG to augment response with knowledge base content.
        
        Returns:
            (augmented_system_prompt, sources) - Enhanced prompt if knowledge found, else (None, [])
        """
        # Check if RAG should be used for this message
        if not self._should_use_rag(message):
            logger.debug(f"🔍 [RAG] Skipped - no trigger keywords found")
            return None, []
        
        try:
            from app.services.rag_engine import get_rag_engine
            
            settings = get_settings()
            rag_engine = get_rag_engine()
            
            # Build user context from conversation context
            user_context = {}
            if context.user_profile:
                user_context["profile"] = context.user_profile
                user_context["city"] = context.user_profile.get("city", "")
            
            # Query RAG engine
            logger.info(f"🔍 [RAG] Querying knowledge base for: {message[:50]}...")
            rag_response = await rag_engine.query(
                question=message,
                user_context=user_context,
                top_k=settings.RAG_TOP_K
            )
            
            # Check confidence threshold
            if rag_response.confidence < settings.RAG_CONFIDENCE_THRESHOLD:
                logger.info(f"🔍 [RAG] Low confidence ({rag_response.confidence:.2f}), using fallback")
                return None, []
            
            # Log retrieval success
            source_count = len(rag_response.sources)
            logger.info(f"🔍 [RAG] Retrieved {source_count} sources, confidence={rag_response.confidence:.2f}")
            
            # Build augmented system prompt
            augmented_prompt = self._build_rag_augmented_prompt(
                message=message,
                knowledge_chunks=rag_response.sources,
                rules_applied=rag_response.rules_applied
            )
            
            return augmented_prompt, rag_response.sources
            
        except Exception as e:
            logger.error(f"❌ [RAG] Augmentation failed: {e}")
            return None, []
    
    def _build_rag_augmented_prompt(
        self,
        message: str,
        knowledge_chunks: list[KnowledgeChunk],
        rules_applied: list | None = None
    ) -> str:
        """
        Build RAG-augmented system prompt using knowledge chunks.
        """
        # Format knowledge context
        if knowledge_chunks:
            knowledge_parts = []
            for chunk in knowledge_chunks:
                source_info = f"(来源: {chunk.source})" if chunk.source else ""
                knowledge_parts.append(
                    f"【{chunk.category}】{chunk.title} {source_info}\n{chunk.content}"
                )
            knowledge_context = "\n\n".join(knowledge_parts)
        else:
            knowledge_context = "无相关参考知识"
        
        # Format rule constraints
        if rules_applied:
            rule_constraints = "\n".join([
                f"- {r.constraint_text}" 
                for r in rules_applied 
                if hasattr(r, 'constraint_text')
            ])
        else:
            rule_constraints = "无特殊政策约束"
        
        # Try to use prompt template
        try:
            return prompt_manager.render(
                category="rag",
                filename="knowledge_query",
                key="system_instruction",
                knowledge_context=knowledge_context,
                rule_constraints=rule_constraints,
                question=message
            )
        except Exception as e:
            logger.warning(f"Failed to render RAG prompt template: {e}")
            # Fallback prompt
            return f"""你是一位专业的购房顾问和资产配置专家。请基于以下参考知识回答用户问题。

## 参考知识
{knowledge_context}

## 政策约束
{rule_constraints}

## 用户问题
{message}

## 回答要求
1. **优先使用参考知识**中的信息，确保回答准确
2. **政策约束是硬性规定**，必须遵守
3. 如果知识不足以完整回答，请明确说明
4. 引用具体政策时标注来源
5. 语气亲切专业"""
    
    def _build_messages(self, context: ConversationContext) -> list[dict[str, str]]:
        """
        Build message list for LLM from context.
        
        Includes:
        - Recent conversation history
        - User profile summary (if available)
        - Asset summary (if available)
        """
        messages = []
        
        # Add context summary as first user message if we have data
        context_summary = self._build_context_summary(context)
        if context_summary:
            messages.append({
                "role": "user",
                "content": f"[系统信息] {context_summary}"
            })
            messages.append({
                "role": "assistant", 
                "content": "我已了解您的情况，请继续。"
            })
        
        # Add recent conversation history
        for msg in context.get_recent_messages(10):
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def _build_context_summary(self, context: ConversationContext) -> str:
        """Build a summary of known context for LLM."""
        parts = []
        
        # User profile - include ALL collected fields so LLM doesn't re-ask
        if context.user_profile:
            profile_parts = []
            if context.user_profile.get("age_range") and context.user_profile.get("age_range") != "unknown":
                profile_parts.append(f"年龄: {context.user_profile['age_range']}")
            if context.user_profile.get("family_structure") and context.user_profile.get("family_structure") != "unknown":
                profile_parts.append(f"家庭: {context.user_profile['family_structure']}")
            if context.user_profile.get("occupation"):
                profile_parts.append(f"职业: {context.user_profile['occupation']}")
            # ✅ Add income_range to context summary
            if context.user_profile.get("income_range"):
                profile_parts.append(f"收入: {context.user_profile['income_range']}")
            # ✅ Add monthly_expense to context summary (日常支出，不含房贷)
            if context.user_profile.get("monthly_expense"):
                base_expense = context.user_profile['monthly_expense']
                # Calculate total mortgage payments from real estate assets
                total_mortgage = sum(
                    re.get("monthly_payment", 0) 
                    for re in (context.real_estate_assets or [])
                )
                if total_mortgage > 0:
                    total_expense = base_expense + total_mortgage
                    profile_parts.append(f"日常支出: {base_expense:.0f}元(不含房贷)")
                    profile_parts.append(f"总月支出: {total_expense:.0f}元(含{total_mortgage:.0f}元月供)")
                else:
                    profile_parts.append(f"月支出: {base_expense:.0f}元")
            # ✅ Add risk_preference to context summary
            if context.user_profile.get("risk_preference") and context.user_profile.get("risk_preference") not in ["unknown", "UNKNOWN"]:
                risk_map = {"CONSERVATIVE": "保守型", "MODERATE": "稳健型", "AGGRESSIVE": "激进型"}
                risk_display = risk_map.get(context.user_profile['risk_preference'], context.user_profile['risk_preference'])
                profile_parts.append(f"风险偏好: {risk_display}")
            if profile_parts:
                parts.append("用户已告知信息: " + ", ".join(profile_parts))
        
        # Assets summary (generic)
        if context.extracted_assets:
            asset_summary = []
            for asset in context.extracted_assets[:5]:  # Limit to 5
                name = asset.get("name", "未知")
                value = asset.get("value", 0)
                asset_type = asset.get("type", "other")
                asset_summary.append(f"{name}({asset_type}): {value:,.0f}元")
            if asset_summary:
                parts.append("已知资产: " + "; ".join(asset_summary))
        
        # RealEstateAsset detailed summary (includes loan info)
        if context.real_estate_assets:
            re_summary = []
            for re in context.real_estate_assets[:3]:  # Limit to 3 properties
                name = re.get("name", "房产")
                city = re.get("city", "")
                area = re.get("area", 0)
                value = re.get("current_value", 0)
                loan_balance = re.get("loan_balance", 0)
                monthly_payment = re.get("monthly_payment", 0)
                
                re_info = f"{city}{name}({area}平米, 估值{value/10000:.0f}万)"
                
                # Add loan info if exists
                if loan_balance > 0:
                    re_info += f", 贷款余额{loan_balance/10000:.0f}万"
                if monthly_payment > 0:
                    re_info += f", 月供{monthly_payment:.0f}元"
                
                re_summary.append(re_info)
            
            if re_summary:
                parts.append("房产详情: " + "; ".join(re_summary))
        
        return " | ".join(parts) if parts else ""
    
    async def _background_extraction_pipeline(
        self, 
        message: str, 
        user_id: int, 
        context: ConversationContext
    ) -> None:
        """
        Background extraction pipeline (fire-and-forget).
        
        Runs asynchronously after response is sent:
        1. Information extraction (LLM-based)
        2. Context refresh (reload from DB)
        3. Insight analysis (psychological profiling)
        4. ActionReasoner plan generation (Phase 4)
        5. RealEstateAsset sync (for detailed real estate data)
        6. FamilyProfile update (from user profile data)
        """
        try:
            logger.info(f"🔄 Background extraction pipeline started for user {user_id}")
            
            # Step 1: Information extraction (now returns result for downstream use)
            extraction_result = await self._trigger_information_extraction(message, user_id, context)
            
            # Step 2: Context refresh (invalidate cache)
            await self.context_manager.invalidate(user_id)
            
            # Step 3: Insight analysis (every N turns)
            await self._trigger_insight_analysis(user_id, context)
            
            # Step 4: ActionReasoner plan generation (Phase 4)
            await self._trigger_action_plan_generation(user_id, context)
            
            # Step 5: Sync RealEstateAsset table (for detailed real estate data)
            if extraction_result:
                assets = extraction_result.get("assets", [])
                logger.info(f"🏠 [DEBUG] extraction_result has {len(assets)} assets: {[a.get('type') for a in assets]}")
                await self._trigger_real_estate_sync(user_id, extraction_result)
            
            # Step 6: Update FamilyProfile from user profile data
            if extraction_result:
                await self._trigger_family_profile_update(user_id, extraction_result)
            
            logger.info(f"🎉 Background extraction pipeline completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Background extraction pipeline failed: {e}")
    
    async def _trigger_information_extraction(
        self, 
        message: str, 
        user_id: int, 
        context: ConversationContext
    ) -> dict | None:
        """Trigger LLM-based information extraction."""
        try:
            from app.services.information_extraction import get_information_extractor, extract_information
            from app.services.asset_extraction_service import asset_extraction_service
            
            # Build conversation history for extraction
            recent_messages = context.get_recent_messages(5)
            
            # Use the async extract_information function which returns Phase 2 format
            extraction_result = await extract_information(
                user_message=message,
                current_history=recent_messages
            )
            
            # Enhanced logging for data flow monitoring
            assets_count = len(extraction_result.get("assets", []))
            has_profile = bool(extraction_result.get("risk_profile"))
            logger.info(f"📥 [EXTRACT] user={user_id} assets={assets_count} profile={has_profile}")
            
            # Store to database if we extracted anything meaningful
            if extraction_result and (
                extraction_result.get("assets") or 
                extraction_result.get("risk_profile")
            ):
                success = await asset_extraction_service.update_user_state(user_id, extraction_result)
                logger.info(f"💾 [PERSIST] user={user_id} success={success}")
                
                # Phase 4 Fix: Store important information to long-term memory (L3)
                await self._store_to_long_term_memory(user_id, extraction_result)
                
                logger.info(f"✅ Information extraction completed for user {user_id}")
                return extraction_result
            else:
                logger.debug(f"ℹ️ No new information extracted for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Information extraction failed: {e}")
            return None
    
    async def _trigger_insight_analysis(
        self, 
        user_id: int, 
        context: ConversationContext
    ) -> None:
        """Trigger cognitive insight analysis (System 2)."""
        try:
            message_count = len(context.conversation_history)
            
            # Run insight analysis more frequently:
            # - After at least 2 messages
            # - Every 2nd message (to keep it responsive)
            if message_count < 2 or message_count % 2 != 0:
                logger.debug(f"Skipping insight analysis: message_count={message_count}")
                return
            
            from app.services.insight_service import get_insight_service
            
            insight_service = get_insight_service()
            analysis_result = await insight_service.analyze_user_psychology(user_id)
            
            # Log the analysis result for debugging
            if analysis_result.get("skipped"):
                logger.info(f"ℹ️ Insight analysis skipped for user {user_id}: {analysis_result.get('reason')}")
            else:
                logger.info(f"✅ Insight analysis completed for user {user_id}")
            
            
        except Exception as e:
            logger.error(f"❌ Insight analysis failed: {e}")
    
    async def _trigger_action_plan_generation(
        self, 
        user_id: int, 
        context: ConversationContext
    ) -> None:
        """
        Phase 4: Trigger ActionReasoner to generate action plans.
        
        Only generates plans when:
        - Feature flag is enabled
        - Auto-generation is enabled
        - Sufficient context is available (at least 5 messages)
        """
        try:
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # Check feature flags
            if not settings.ENABLE_ACTION_REASONER:
                return
            
            if not getattr(settings, 'ACTION_PLAN_AUTO_GENERATE', False):
                logger.debug("ActionReasoner auto-generate disabled")
                return
            
            # Only generate after sufficient conversation
            message_count = len(context.conversation_history)
            if message_count < 5:
                return
            
            # Only trigger every 5 turns to avoid spam
            if message_count % 5 != 0:
                return
            
            from app.services.action_reasoner import get_action_reasoner
            
            action_reasoner = get_action_reasoner()
            plans = await action_reasoner.generate_plan(user_id)
            
            if plans:
                logger.info(f"🎯 [ACTION_REASONER] Generated {len(plans)} plan(s) for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ ActionReasoner failed: {e}")
    
    async def _store_to_long_term_memory(
        self, 
        user_id: int, 
        extraction_result: dict
    ) -> None:
        """
        Phase 4 Fix: Store important extracted information to long-term memory (L3).
        
        This fixes P3 - MemoryService.add_memory() was not being called.
        """
        try:
            from app.services.memory_service import get_memory_service
            from app.core.config import get_settings
            
            settings = get_settings()
            if not getattr(settings, 'ENABLE_MEMORY_STORAGE', True):
                logger.debug(f"Memory storage disabled by feature flag")
                return
            
            memory_service = get_memory_service()
            memories_added = 0
            
            # Store extracted assets to memory
            for asset in extraction_result.get("assets", []):
                asset_name = asset.get("name", "未知资产")
                asset_type = asset.get("type", "other")
                asset_amount = asset.get("amount", 0)
                
                memory_text = f"用户资产: {asset_name} ({asset_type}), 价值约 {asset_amount} 元"
                
                await memory_service.add_memory(
                    user_id=user_id,
                    text=memory_text,
                    metadata={
                        "source": "extraction",
                        "type": "asset",
                        "asset_type": asset_type,
                        "asset_name": asset_name
                    }
                )
                memories_added += 1
            
            # Store risk profile changes to memory
            risk_profile = extraction_result.get("risk_profile", {})
            if risk_profile:
                profile_parts = []
                if risk_profile.get("age_range"):
                    profile_parts.append(f"年龄段: {risk_profile['age_range']}")
                if risk_profile.get("family_structure"):
                    profile_parts.append(f"家庭结构: {risk_profile['family_structure']}")
                if risk_profile.get("tolerance"):
                    profile_parts.append(f"风险偏好: {risk_profile['tolerance']}")
                if risk_profile.get("occupation"):
                    profile_parts.append(f"职业: {risk_profile['occupation']}")
                
                if profile_parts:
                    memory_text = f"用户画像更新: {', '.join(profile_parts)}"
                    await memory_service.add_memory(
                        user_id=user_id,
                        text=memory_text,
                        metadata={
                            "source": "extraction",
                            "type": "profile_update"
                        }
                    )
                    memories_added += 1
            
            logger.info(f"🧠 [MEMORY] user={user_id} memories_added={memories_added}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store memories for user {user_id}: {e}")

    async def _trigger_real_estate_sync(
        self, 
        user_id: int, 
        extraction_result: dict
    ) -> None:
        """
        Sync extracted real estate assets to the detailed RealEstateAsset table.
        
        This table provides structured storage for detailed property data used by:
        - RealEstateEngine for property analysis
        - SwapSimulator for swap simulations
        - PropertyValuation for valuations
        """
        try:
            from app.models.real_estate import RealEstateAsset
            from app.core.database import get_db_session
            from sqlmodel import select
            from datetime import datetime
            
            assets = extraction_result.get("assets", [])
            real_estate_assets = [a for a in assets if a.get("type") == "real_estate"]
            liability_assets = [a for a in assets if a.get("type") == "liability"]
            
            # Only skip if BOTH are empty
            if not real_estate_assets and not liability_assets:
                logger.debug("No real estate or liability assets to sync")
                return
            
            logger.info(f"🏠 [SYNC] Processing {len(real_estate_assets)} real estate, {len(liability_assets)} liability assets")
            
            async for session in get_db_session():
                for asset in real_estate_assets:
                    name = asset.get("name", "未命名房产")
                    amount = asset.get("amount", 0)
                    # NOTE: location and area are at top level, not in metadata
                    location = asset.get("location", "")
                    area = asset.get("area", 0)
                    metadata = asset.get("metadata", {})
                    
                    logger.info(f"🏠 [DEBUG] Processing asset: name={name}, amount={amount}, location={location}, area={area}")
                    
                    # Parse location to extract city
                    city = "未知"
                    if location and "市" in location:
                        city = location.split("市")[0] + "市"
                    elif location:
                        city = location
                    
                    # Check if similar property exists
                    stmt = select(RealEstateAsset).where(
                        RealEstateAsset.user_id == user_id,
                        RealEstateAsset.name == name
                    )
                    result = await session.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        # Update existing property
                        if amount > 0:
                            existing.current_value = amount
                        if area and area > 0:
                            existing.area = area
                        existing.value_source = "extraction"
                        existing.value_updated_at = datetime.utcnow()
                        logger.info(f"🏠 Updated RealEstateAsset: {name} for user {user_id}")
                    else:
                        # Create new property (using string values, not Enums)
                        new_property = RealEstateAsset(
                            user_id=user_id,
                            name=name,
                            property_type="residential",  # Use string value
                            usage="self_occupied",        # Use string value
                            city=city,
                            area=area if area and area > 0 else 100,  # Default 100 sqm if not provided
                            current_value=amount if amount > 0 else 1000000,  # Default 1M if not provided
                            value_source="extraction",
                            loan_type="none",             # Use string value
                        )
                        session.add(new_property)
                        logger.info(f"🏠 Created RealEstateAsset: {name} for user {user_id}")
                
                # Process LIABILITY assets (mortgages) to update loan info
                liability_assets = [a for a in assets if a.get("type") == "liability"]
                logger.info(f"🏦 [DEBUG] Found {len(liability_assets)} LIABILITY assets: {liability_assets}")
                
                for liability in liability_assets:
                    liability_name = liability.get("name", "")
                    loan_amount = liability.get("amount", 0)
                    metadata = liability.get("metadata", {})
                    monthly_payment = metadata.get("monthly_payment", 0)
                    
                    logger.info(f"🏦 [DEBUG] Liability raw data: {liability}")
                    logger.info(f"🏦 [DEBUG] Checking mortgage keywords in '{liability_name}'")
                    
                    # Check if this is a mortgage (房贷)
                    if not any(keyword in liability_name for keyword in ["房贷", "房产", "住房贷款", "按揭", "贷款"]):
                        logger.info(f"🏦 [DEBUG] Skipping - not a mortgage: {liability_name}")
                        continue
                    
                    logger.info(f"🏦 [DEBUG] Processing mortgage: name={liability_name}, loan={loan_amount}, monthly={monthly_payment}")
                    
                    # Find the corresponding RealEstateAsset to update
                    # Try to match by city name in the liability name
                    re_stmt = select(RealEstateAsset).where(RealEstateAsset.user_id == user_id)
                    re_result = await session.execute(re_stmt)
                    user_properties = re_result.scalars().all()
                    
                    matched_property = None
                    for prop in user_properties:
                        # Match by city name in liability name
                        if prop.city and prop.city in liability_name:
                            matched_property = prop
                            break
                        # Match by property name in liability name
                        if prop.name and prop.name in liability_name:
                            matched_property = prop
                            break
                    
                    # If no match found, update the first/most recent property
                    if not matched_property and user_properties:
                        matched_property = user_properties[0]
                    
                    if matched_property:
                        if loan_amount > 0:
                            matched_property.loan_balance = loan_amount
                            matched_property.loan_type = "commercial"  # Default to commercial loan
                        if monthly_payment > 0:
                            matched_property.monthly_payment = monthly_payment
                        matched_property.value_updated_at = datetime.utcnow()
                        logger.info(f"🏦 Updated loan info for {matched_property.name}: balance={loan_amount}, monthly={monthly_payment}")
                
                await session.commit()
                break
            
            logger.info(f"🏠 [REAL_ESTATE_SYNC] user={user_id} synced={len(real_estate_assets)} properties")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync real estate assets for user {user_id}: {e}")

    async def _trigger_family_profile_update(
        self, 
        user_id: int, 
        extraction_result: dict
    ) -> None:
        """
        Update FamilyProfile from extracted user profile data.
        
        Creates family member graph and lifecycle events based on family_structure.
        Used by ActionReasoner for financial planning recommendations.
        """
        try:
            from app.services.family_profile import get_family_profile_service
            from app.core.config import get_settings
            
            settings = get_settings()
            if not settings.ENABLE_FAMILY_PROFILE:
                logger.debug("FamilyProfile disabled by feature flag")
                return
            
            risk_profile = extraction_result.get("risk_profile", {})
            family_structure = risk_profile.get("family_structure")
            
            # Only update if we have family structure info
            if not family_structure or family_structure == "unknown":
                return
            
            family_service = get_family_profile_service()
            
            # Extract family info from profile data
            family_info = await family_service.extract_family_info_from_profile(risk_profile)
            
            # Parse income_range string to float (e.g., "48万" -> 480000, "年收入50万" -> 500000)
            total_income = None
            income_str = risk_profile.get("income_range", "")
            if income_str:
                try:
                    import re
                    # Extract number and unit from strings like "48万", "年收入50万", "500000"
                    match = re.search(r'(\d+(?:\.\d+)?)\s*万?', str(income_str))
                    if match:
                        value = float(match.group(1))
                        if '万' in str(income_str):
                            value *= 10000
                        total_income = value
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse income_range: {income_str}")
                    total_income = None
            
            # monthly_expense should already be a float
            # NOTE: After expense separation, this is now "日常支出" (living expenses without mortgage)
            # Mortgage payments are stored separately in RealEstateAsset.monthly_payment
            total_expenses = risk_profile.get("monthly_expense")
            if total_expenses is not None:
                try:
                    total_expenses = float(total_expenses)
                except (ValueError, TypeError):
                    total_expenses = None
            
            # Update FamilyProfile with extracted data
            await family_service.create_or_update_profile(
                user_id=user_id,
                members=family_info.get("members"),
                lifecycle_events=family_info.get("lifecycle_events"),
                total_income=total_income,
                total_expenses=total_expenses
            )
            
            members_count = len(family_info.get("members", []))
            events_count = len(family_info.get("lifecycle_events", []))
            logger.info(f"👨‍👩‍👧 [FAMILY_PROFILE] user={user_id} members={members_count} events={events_count}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update family profile for user {user_id}: {e}")


# Singleton instance
_orchestrator: ConversationOrchestrator | None = None


def get_conversation_orchestrator() -> ConversationOrchestrator:
    """Get or create ConversationOrchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        from app.core.dependencies import get_llm_provider, get_context_manager
        
        _orchestrator = ConversationOrchestrator(
            llm_provider=get_llm_provider(),
            context_manager=get_context_manager()
        )
    return _orchestrator
