"""
LangChain-based chat agent for AssetFlow
"""

import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.models.user import AssetType, UserAsset, UserProfile
from app.models.cognition import UserCognition
from app.services.asset_extraction_service import asset_extraction_service
from app.services.information_extraction import extract_information_from_conversation
from app.services.portfolio_analyzer import portfolio_analyzer
from app.services.recommendation_service import get_recommendation_service
from app.services.search_tools import create_search_tool
from app.services.ui_component_service import get_ui_component_service

logger = logging.getLogger(__name__)


class UIComponent(BaseModel):
    """Represents a UI component to be rendered"""

    type: str  # VALUATION_CARD, ACTION_CARD, PORTFOLIO_CHART
    data: dict[str, Any]
    position: int  # Position in the response text


class ChatContext(BaseModel):
    """Context for chat conversation"""

    user_id: int
    session_id: str | None = None
    conversation_history: list[dict[str, str]] = []
    extracted_assets: list[dict[str, Any]] = []
    user_profile: dict[str, Any] | None = None
    current_stage: str = (
        "initial"  # initial, property_collection, asset_collection, analysis
    )
    portfolio_analysis: dict[str, Any] | None = None


class ChatAgent:
    """LangChain-based chat agent for asset consultation"""

    def __init__(
        self, openai_api_key: str | None = None, tavily_api_key: str | None = None
    ):
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self.tavily_api_key = tavily_api_key or settings.TAVILY_API_KEY

        # Check if we have a valid OpenAI API key (not mock)
        self.has_real_openai_key = (
            self.openai_api_key 
            and not self.openai_api_key.startswith("sk-mock")
            and self.openai_api_key != "mock-key"
        )

        if not self.has_real_openai_key:
            logger.warning(
                "No valid OpenAI API key provided - using mock agent for development"
            )

        # Initialize LLM only if we have a real API key
        llm_kwargs = {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "api_key": self.openai_api_key,
            "streaming": True,
        }
        
        # Add base_url if configured for DeepSeek
        if settings.OPENAI_API_BASE:
            llm_kwargs["base_url"] = settings.OPENAI_API_BASE
            
        self.llm = (
            ChatOpenAI(**llm_kwargs)
            if self.has_real_openai_key
            else None
        )

        # Initialize search tool
        self.search_tool = create_search_tool(
            use_mock=settings.USE_MOCK_SEARCH, tavily_api_key=self.tavily_api_key
        )

        # Initialize agent (create mock agent if no real LLM)
        self.agent = self._create_agent() if self.llm else "mock_agent"

        # Initialize services
        self.ui_service = get_ui_component_service()
        self.recommendation_service = get_recommendation_service()

        # Conversation contexts (in production, this would be stored in Redis/DB)
        self.contexts: dict[int, ChatContext] = {}

    def _create_agent(self):
        """Create LangChain agent with tools"""

        # Load system prompt from YAML configuration
        from app.core.prompt_manager import prompt_manager
        
        system_prompt = prompt_manager.render(
            category="chat",
            filename="agent_system",
            key="system_instruction"
        )

        # Create agent using the new API
        agent = create_agent(
            model=self.llm, tools=[self.search_tool], system_prompt=system_prompt
        )

        return agent

    async def process_message(
        self, message: str, user_id: int, user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """Process user message and return streaming response"""

        # Import here to avoid circular imports
        from app.services.chat_history_service import get_chat_history_service
        
        chat_history_service = get_chat_history_service()

        # Save user message immediately
        try:
            await chat_history_service.save_user_message(user_id, message)
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")

        # Handle mock agent case (development environment)
        if not self.has_real_openai_key:
            async for chunk in self._process_message_mock(message, user_id, user_profile):
                yield chunk
            return

        if not self.agent:
            yield "抱歉，AI服务暂时不可用。请稍后再试。"
            return

        try:
            # Get or create conversation context
            context = self.contexts.get(user_id, ChatContext(user_id=user_id))
            self.contexts[user_id] = context

            # Add user message to history
            context.conversation_history.append(
                {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Extract and store information from user message
            # NOTE: Disabled old extraction method in favor of Phase 2 LLM-based extraction
            # await self._extract_and_store_information(context, message, user_id)

            # Prepare input for agent with context
            agent_input = {
                "messages": [
                    {
                        "role": "user",
                        "content": await self._prepare_contextual_input(message, context, user_id),
                    }
                ]
            }

            # Stream response from agent
            response_chunks = []
            thought_content = []  # Store thought content for logging
            in_thought_block = False
            
            async for chunk in self.agent.astream(agent_input):
                # Handle different chunk structures from LangGraph
                messages = None
                if "messages" in chunk:
                    messages = chunk["messages"]
                elif "model" in chunk and "messages" in chunk["model"]:
                    messages = chunk["model"]["messages"]
                
                if messages:
                    for msg in messages:
                        if hasattr(msg, "content") and msg.content:
                            chunk_text = msg.content
                            response_chunks.append(chunk_text)
                            # Don't yield yet - we'll filter thought blocks first

            # Combine all chunks and filter out <Thought> blocks
            full_response = "".join(response_chunks)
            filtered_response, thought_text = self._filter_thought_blocks(full_response)
            
            # Log thought content to console for debugging
            if thought_text:
                logger.info(f"🧠 CHAIN OF THOUGHT (User {user_id}):\n{thought_text}")
            
            # Yield the filtered response (without <Thought> blocks)
            if filtered_response:
                yield filtered_response
            
            # Store AI response in history (use filtered response without <Thought> blocks)
            context.conversation_history.append(
                {
                    "role": "assistant",
                    "content": filtered_response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Generate and inject UI components based on context
            ui_enhanced_response = await self._enhance_response_with_ui_components(
                filtered_response, context, user_id
            )

            if ui_enhanced_response != filtered_response:
                yield ui_enhanced_response[
                    len(filtered_response) :
                ]  # Only yield the new UI parts

            # Save AI message to database (after generation is complete)
            try:
                await chat_history_service.save_ai_message(user_id, ui_enhanced_response)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")

            # ✅ OPTIMIZATION: Pure Async Extraction (Plan E)
            # LLM can understand user info from conversation history (last 10 messages)
            # No need for temporary extraction - just run full extraction in background
            # This saves 1.1-3.3 seconds of user-perceived latency
            
            import asyncio
            
            # Create background task for extraction pipeline (does not block response)
            asyncio.create_task(
                self._background_extraction_pipeline(message, user_id, context)
            )
            
            logger.info(f"✅ Started background extraction pipeline for user {user_id}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    async def _process_message_mock(
        self, message: str, user_id: int, user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """Mock message processing for development environment"""
        
        # Import here to avoid circular imports
        from app.services.chat_history_service import get_chat_history_service
        
        chat_history_service = get_chat_history_service()

        # Save user message immediately
        try:
            await chat_history_service.save_user_message(user_id, message)
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
        
        try:
            # Get or create conversation context
            context = self.contexts.get(user_id, ChatContext(user_id=user_id))
            self.contexts[user_id] = context

            # Add user message to history
            context.conversation_history.append(
                {
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Extract and store information from user message
            # NOTE: Disabled old extraction method in favor of Phase 2 LLM-based extraction
            # await self._extract_and_store_information(context, message, user_id)

            # Generate mock response based on conversation stage and message content
            response = self._generate_mock_response(message, context)
            
            # Simulate streaming by yielding chunks
            import asyncio
            words = response.split()
            for i in range(0, len(words), 3):  # Yield 3 words at a time
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.1)  # Small delay to simulate streaming

            # Store AI response in history
            context.conversation_history.append(
                {
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Generate and inject UI components based on context
            ui_enhanced_response = await self._enhance_response_with_ui_components(
                response, context, user_id
            )

            if ui_enhanced_response != response:
                yield ui_enhanced_response[len(response):]  # Only yield the new UI parts

            # Save AI message to database (after generation is complete)
            try:
                await chat_history_service.save_ai_message(user_id, ui_enhanced_response)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")

            # ✅ OPTIMIZATION: Pure Async Extraction (Plan E)
            # LLM can understand user info from conversation history (last 10 messages)
            # No need for temporary extraction - just run full extraction in background
            # This saves 1.1-3.3 seconds of user-perceived latency
            
            import asyncio
            
            # Create background task for extraction pipeline (does not block response)
            asyncio.create_task(
                self._background_extraction_pipeline(message, user_id, context)
            )
            
            logger.info(f"✅ Started background extraction pipeline for user {user_id}")

        except Exception as e:
            logger.error(f"Error processing mock message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    def _safe_emoji_text(self, text: str) -> str:
        """
        Ensure emoji characters are safely encoded for WebSocket transmission
        """
        try:
            # Test if the text can be safely encoded/decoded
            text.encode('utf-8').decode('utf-8')
            return text
        except UnicodeEncodeError:
            # If there are encoding issues, replace problematic characters
            logger.warning(f"Emoji encoding issue detected, cleaning text: {text[:100]}...")
            return text.encode('utf-8', errors='replace').decode('utf-8')
        except Exception as e:
            logger.error(f"Unexpected error in emoji text processing: {e}")
            # Fallback: remove all non-ASCII characters
            return ''.join(char for char in text if ord(char) < 128)

    def _generate_mock_response(self, message: str, context: ChatContext) -> str:
        """Generate mock AI response based on message content and context"""
        
        def safe_return(text: str) -> str:
            """Safely return text with emoji encoding validation"""
            return self._safe_emoji_text(text)
        
        message_lower = message.lower()
        
        # Check for emotional keywords that need empathy
        stress_keywords = ["压力", "焦虑", "担心", "困难", "亏损", "负债", "房贷"]
        has_stress = any(keyword in message_lower for keyword in stress_keywords)
        
        # Check for completion signals
        completion_signals = ["就这些", "没了", "没有了", "暂时这样", "就这样", "没有其他", "想不到了"]
        is_completion = any(signal in message_lower for signal in completion_signals)
        
        # Handle completion signals - accept and move forward
        if is_completion:
            return safe_return("好的，我明白了 🤝 基于您目前提供的资产情况，让我为您做一个初步分析...\n\n根据标准普尔四象限模型，我会帮您评估现有资产的配置情况，并给出优化建议。如果之后想到其他资产信息，随时可以补充给我 💡")
        
        # Greeting responses with warm persona
        if any(greeting in message_lower for greeting in ["你好", "hello", "hi", "您好"]):
            if context.current_stage == "initial":
                return safe_return("您好！🤝 我是AssetFlow的首席资产配置专家，很高兴为您服务！我不只是提供数据分析，更希望能给您带来财务安全感。\n\n有什么财务问题想要探讨吗？或者我们可以从了解您的资产情况开始 💡")
            else:
                return safe_return("您好！很高兴继续为您服务 🤝 有什么新的财务问题想要探讨吗？")
        
        # Property-related responses with appreciation
        if any(word in message_lower for word in ["房", "房产", "房子", "小区", "楼盘"]):
            if has_stress and "房贷" in message_lower:
                return "我理解高房贷确实会带来压力 🤝，这种担心很正常。让我们一起看看如何优化您的资产配置来缓解这种压力...\n\n首先，拥有房产本身就是很好的资产积累！💡 能告诉我房产的具体位置和大概面积吗？这样我可以帮您评估现在的市场价值。"
            elif context.current_stage == "initial":
                if "北京" in message or "上海" in message or "深圳" in message or "广州" in message:
                    return "哇，在一线城市拥有房产非常棒！💡 这是很好的资产基础。让我帮您看看现在的市场参考价 📈\n\n能告诉我具体的小区名称和房屋面积吗？稍等，我来查询一下最新的市场数据..."
                else:
                    return "很好！房产是重要的资产组成部分 🏠 为了给您准确的估值和配置建议，我需要了解：\n\n1）房产所在的具体城市和小区名称\n2）房屋面积（平方米）\n3）大概的购买时间\n\n这些信息能帮我更好地评估您的资产结构。"
            else:
                return "关于您的房产配置 🏠，根据标准普尔四象限模型，房产通常属于'生钱的钱'象限。我建议房产占总资产比例控制在合理范围内，这样能更好地平衡风险和收益。"
        
        # Direct investment questions - provide immediate value
        if any(word in message_lower for word in ["50万", "100万", "怎么投", "如何投资"]):
            amount_match = None
            if "50万" in message_lower:
                amount_match = "50万"
            elif "100万" in message_lower:
                amount_match = "100万"
            
            if amount_match:
                return f"很好的问题！💡 对于{amount_match}的投资，我先给您一个基于标准普尔四象限的初步建议：\n\n🔹 **要花的钱（10%）**：{int(amount_match[:-1]) * 0.1}万 - 应急资金\n🔹 **保命的钱（20%）**：{int(amount_match[:-1]) * 0.2}万 - 保险保障\n🔹 **生钱的钱（30%）**：{int(amount_match[:-1]) * 0.3}万 - 股票基金等\n🔹 **保本升值（40%）**：{int(amount_match[:-1]) * 0.4}万 - 稳健理财\n\n当然，如果您能告诉我更多情况（比如年龄、风险偏好、现有资产），我可以给出更精准的个性化建议 🤝"
        
        # Asset-related responses with guidance
        if any(word in message_lower for word in ["资产", "投资", "理财", "存款", "股票", "基金"]):
            if has_stress:
                return "我理解投资有时会让人感到压力 🤝 这很正常。让我们一起看看您的资产情况，找到让您更安心的配置方案。\n\n您方便的话，可以跟我聊聊目前的资产情况。不用一次性说完，我们可以慢慢聊 💡"
            else:
                return "很好！💡 了解资产情况能帮我为您制定更合适的配置方案。\n\n您可以跟我聊聊目前的资产情况，比如房产、现金储蓄、投资产品等。不用担心信息不全，我们可以边聊边完善 🤝"
        
        # Analysis requests with empathy
        if any(word in message_lower for word in ["分析", "建议", "配置", "怎么办", "如何"]):
            if len(context.extracted_assets) >= 1:
                return "基于您提供的信息，让我为您分析标准普尔四象限资产配置 📊\n\n**四象限配置逻辑：**\n🔹 **要花的钱（10%）**：应急资金，6个月生活费\n🔹 **保命的钱（20%）**：保险保障，守护家庭\n🔹 **生钱的钱（30%）**：高收益投资，财富增长\n🔹 **保本升值（40%）**：稳健投资，保值增值\n\n根据您的情况，我建议优先完善应急资金储备和保险保障 💡 这样能给您更多安全感。如果您还有其他资产信息想补充，随时告诉我。"
            else:
                return "我很乐意为您提供配置建议！💡 不过为了给出最适合您的方案，我想先了解一下您的资产情况。\n\n您可以跟我聊聊目前的资产，比如房产、现金储蓄、投资等。有多少说多少，我会基于现有信息给您初步建议 🤝"
        
        # Numbers or financial amounts with encouragement
        if any(char.isdigit() for char in message):
            if "万" in message or "元" in message:
                return "感谢您提供具体的金额信息！💡 这对制定精准的配置建议很有帮助。\n\n让我们继续完善其他资产类别的情况，这样我就能为您进行全面的四象限分析了。您还有其他投资或储蓄想要一起考虑的吗？"
            else:
                return "我注意到您提到了一些数字 🤔 如果这是关于资产金额的，请告诉我具体是哪类资产，金额是多少，这样我能更好地为您分析配置方案。"
        
        # Default responses based on conversation stage with warm tone
        response = ""
        if context.current_stage == "initial":
            response = "我是您的首席资产配置专家 🤝 有什么财务问题想要探讨吗？\n\n如果您想了解资产配置建议，我们可以从您的资产情况聊起。您方便的话，可以跟我说说目前的资产情况 💡"
        elif context.current_stage == "property_collection":
            response = "很好，我对您的房产情况有了基本了解 🏠 \n\n如果您还有其他资产想一起考虑（比如现金储蓄、投资等），可以告诉我。这样我能给您更全面的配置建议 💡"
        elif context.current_stage == "asset_collection":
            response = "资产信息收集得不错！💡 如果您方便的话，可以跟我聊聊您的个人情况，比如年龄段、家庭结构，以及对投资风险的接受程度。这能帮我给出更精准的四象限配置建议 🤝"
        else:
            response = "基于您提供的信息，我建议按照标准普尔四象限模型进行资产配置 📊 您还有什么具体问题想了解吗？我很乐意为您详细解答 🤝"
        
        return self._safe_emoji_text(response)

    def _update_conversation_stage(
        self, context: ChatContext, validation: dict[str, Any]
    ):
        """Update conversation stage based on extracted information"""
        completeness_score = validation.get("completeness_score", 0.0)

        if completeness_score < 0.3:
            context.current_stage = "initial"
        elif completeness_score < 0.6:
            context.current_stage = "property_collection"
        elif completeness_score < 0.8:
            context.current_stage = "asset_collection"
        else:
            context.current_stage = "analysis"

    def _filter_thought_blocks(self, text: str) -> tuple[str, str]:
        """
        Filter out <Thought> blocks from AI response.
        
        Returns:
            tuple: (filtered_text, thought_content)
                - filtered_text: Response without <Thought> blocks (shown to user)
                - thought_content: Extracted thought content (logged to console)
        """
        import re
        
        # Pattern to match <Thought>...</Thought> blocks (case-insensitive, multiline)
        thought_pattern = r'<Thought>(.*?)</Thought>'
        
        # Extract all thought blocks
        thought_matches = re.findall(thought_pattern, text, re.IGNORECASE | re.DOTALL)
        thought_content = "\n---\n".join(thought_matches) if thought_matches else ""
        
        # Remove thought blocks from response
        filtered_text = re.sub(thought_pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Clean up extra whitespace
        filtered_text = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_text).strip()
        
        return filtered_text, thought_content

    async def _update_cognition_state(self, user_id: int, assets: list, profile: dict | None = None):
        """
        Update UserCognition collection status when new information is extracted
        
        ✅ FIX: Removed risk_profile update logic - this should be handled exclusively
        by InsightService to maintain single responsibility and avoid data conflicts.
        """
        try:
            from sqlmodel import select
            from app.core.database import get_db_session
            
            async for session in get_db_session():
                # Get or create UserCognition record
                cognition_statement = select(UserCognition).where(UserCognition.user_id == user_id)
                cognition_result = await session.execute(cognition_statement)
                cognition = cognition_result.scalar_one_or_none()
                
                if not cognition:
                    cognition = UserCognition(user_id=user_id)
                    session.add(cognition)
                
                # Update collection status based on extracted assets
                for asset in assets:
                    asset_type = asset.asset_type
                    cognition.set_collection_status(asset_type, True)
                
                # ✅ FIX: Removed risk_profile update logic
                # Risk profile (including tolerance, sentiment, decision_style, etc.)
                # should be updated exclusively by InsightService._update_cognition_insights()
                # This maintains single responsibility and prevents partial updates
                
                await session.commit()
                logger.info(f"🔄 COGNITION_UPDATE: Updated collection_status for user {user_id}")
                break
                
        except Exception as e:
            logger.error(f"Error updating cognition state: {e}")

    async def _extract_and_store_information(
        self, context: ChatContext, user_message: str, user_id: int
    ):
        """Extract information from user message and store to database"""
        try:
            # Extract structured information
            assets, profile, validation = extract_information_from_conversation(
                user_message
            )

            # Store extracted assets to database
            if assets:
                stored_assets = await asset_extraction_service.store_extracted_assets(
                    user_id, assets
                )
                logger.info(f"Stored {len(stored_assets)} assets for user {user_id}")

                # Update context with stored assets
                for asset in assets:
                    existing_asset = None
                    for existing in context.extracted_assets:
                        if (
                            existing.get("asset_type") == asset.asset_type
                            and existing.get("name") == asset.name
                        ):
                            existing_asset = existing
                            break

                    if existing_asset:
                        if asset.confidence > existing_asset.get("confidence", 0):
                            existing_asset.update(asset.model_dump())
                    else:
                        context.extracted_assets.append(asset.model_dump())

            # Store extracted profile to database
            if profile:
                stored_profile = await asset_extraction_service.store_extracted_profile(
                    user_id, profile
                )
                if stored_profile:
                    logger.info(f"Updated profile for user {user_id}")

                # Update context
                if not context.user_profile:
                    context.user_profile = {}

                profile_dict = profile.model_dump()
                for key, value in profile_dict.items():
                    if value is not None and key not in ["extracted_from", "timestamp"]:
                        context.user_profile[key] = value

            # Update conversation stage
            self._update_conversation_stage(context, validation)
            
            # Update cognition state with extracted information
            if assets or profile:
                await self._update_cognition_state(user_id, assets or [], profile)

        except Exception as e:
            logger.error(f"Error extracting and storing information: {e}")

    async def _refresh_context_from_db(self, user_id: int, context: ChatContext) -> None:
        """
        PHASE 1 FIX: Context Refresh (System 1 - Immediate Consistency)
        
        Force reload user state from DB after extraction to ensure the AI sees
        the latest data in the next turn. This prevents "stale context" issues
        where the AI doesn't know information the user just provided.
        
        This is the CRITICAL missing piece that causes the "I am 35 years old"
        -> "How old are you?" bug.
        """
        try:
            from sqlmodel import select
            from app.core.database import get_db_session
            
            logger.info(f"🔄 CONTEXT_REFRESH: Starting context refresh for user {user_id}")
            
            async for session in get_db_session():
                # Reload UserProfile (L1) - age, family, occupation, income, etc.
                profile_statement = select(UserProfile).where(UserProfile.user_id == user_id)
                profile_result = await session.execute(profile_statement)
                profile = profile_result.scalar_one_or_none()
                
                if profile:
                    # Update context.user_profile with fresh data
                    context.user_profile = {
                        "age_range": profile.age_range,
                        "family_structure": profile.family_structure,
                        "monthly_expense": profile.monthly_expense,
                        "risk_preference": profile.risk_preference.value if hasattr(profile.risk_preference, 'value') else profile.risk_preference,
                        "occupation": profile.occupation,
                        "income_range": profile.income_range,
                    }
                    logger.info(f"🔄 CONTEXT_REFRESH: Updated user_profile in context: {context.user_profile}")
                else:
                    logger.info(f"🔄 CONTEXT_REFRESH: No UserProfile found for user {user_id}")
                
                # Reload UserAssets (L1) - all confirmed and extracted assets
                assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
                assets_result = await session.execute(assets_statement)
                assets = assets_result.scalars().all()
                
                # Update context.extracted_assets with fresh data
                context.extracted_assets = []
                for asset in assets:
                    asset_dict = {
                        "asset_type": asset.asset_type.value,
                        "name": asset.name,
                        "value": asset.value,
                        "is_confirmed": asset.is_confirmed,
                        "confidence": 0.9 if asset.is_confirmed else 0.7,
                    }
                    
                    # Add extra data if available
                    if asset.extra_data:
                        if "location" in asset.extra_data:
                            asset_dict["location"] = asset.extra_data["location"]
                        if "area" in asset.extra_data:
                            asset_dict["area"] = asset.extra_data["area"]
                    
                    context.extracted_assets.append(asset_dict)
                
                logger.info(f"🔄 CONTEXT_REFRESH: Updated {len(context.extracted_assets)} assets in context")
                
                # Reload UserCognition (L2) - collection status, goals, psychological profile
                cognition_statement = select(UserCognition).where(UserCognition.user_id == user_id)
                cognition_result = await session.execute(cognition_statement)
                cognition = cognition_result.scalar_one_or_none()
                
                if cognition:
                    # Update conversation stage based on collection status
                    if cognition.collection_status:
                        collected_count = sum(1 for v in cognition.collection_status.values() if v)
                        if collected_count == 0:
                            context.current_stage = "initial"
                        elif collected_count <= 2:
                            context.current_stage = "property_collection"
                        elif collected_count <= 4:
                            context.current_stage = "asset_collection"
                        else:
                            context.current_stage = "analysis"
                        
                        logger.info(f"🔄 CONTEXT_REFRESH: Updated stage to {context.current_stage} (collected: {collected_count})")
                    
                    # Add financial goals to context if available
                    if cognition.financial_goals:
                        if not context.user_profile:
                            context.user_profile = {}
                        context.user_profile["financial_goals"] = cognition.financial_goals
                        logger.info(f"🔄 CONTEXT_REFRESH: Added financial goals: {cognition.financial_goals}")
                
                logger.info(f"🔄 CONTEXT_REFRESH: ✅ Context refresh complete for user {user_id}")
                break  # Exit the async generator
                
        except Exception as e:
            logger.error(f"🔄 CONTEXT_REFRESH: ❌ Error refreshing context for user {user_id}: {e}")
            import traceback
            logger.error(f"🔄 CONTEXT_REFRESH: Traceback: {traceback.format_exc()}")

    async def _background_extraction_pipeline(
        self, 
        message: str, 
        user_id: int, 
        context: ChatContext
    ) -> None:
        """
        ✅ PLAN E: Background extraction pipeline with error isolation and fallback
        
        This runs asynchronously after the AI response is sent to the user.
        LLM can already understand user info from conversation history (last 10 messages),
        so this extraction is for database persistence and next-turn Fact Sheet.
        
        Pipeline:
        1. Information extraction (LLM-based)
        2. Context refresh (reload from DB)
        3. Insight analysis (psychological profiling)
        
        All steps have error isolation and fallback strategies.
        """
        try:
            logger.info(f"🔄 Background extraction pipeline started for user {user_id}")
            
            # Step 1: Information extraction
            try:
                await self._trigger_information_extraction(message, user_id, context)
                logger.info(f"✅ Information extraction completed for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Information extraction failed for user {user_id}: {e}")
                # Fallback: Use regex-based extraction
                try:
                    await self._fallback_extraction(message, user_id, context)
                    logger.info(f"✅ Fallback extraction completed for user {user_id}")
                except Exception as fallback_error:
                    logger.error(f"❌ Fallback extraction also failed: {fallback_error}")
            
            # Step 2: Context refresh (reload from DB)
            try:
                await self._refresh_context_from_db(user_id, context)
                logger.info(f"✅ Context refresh completed for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Context refresh failed for user {user_id}: {e}")
            
            # Step 3: Insight analysis (can run independently)
            try:
                await self._trigger_insight_analysis(user_id, context)
                logger.info(f"✅ Insight analysis completed for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Insight analysis failed for user {user_id}: {e}")
            
            logger.info(f"🎉 Background extraction pipeline completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Background extraction pipeline failed for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _fallback_extraction(
        self, 
        message: str, 
        user_id: int, 
        context: ChatContext
    ) -> None:
        """
        Fallback extraction using regex patterns when LLM extraction fails.
        This ensures we don't lose user data even if the LLM API is down.
        """
        try:
            logger.info(f"🔄 Running fallback extraction for user {user_id}")
            
            from app.services.information_extraction import InformationExtractor
            
            extractor = InformationExtractor()
            assets, profile, validation = await extractor._fallback_extraction(message)
            
            # Save to database if we extracted anything
            if assets or profile:
                from app.services.asset_extraction_service import asset_extraction_service
                
                extraction_result = {
                    "assets": [asset.model_dump() for asset in assets] if assets else [],
                    "risk_profile": profile.model_dump() if profile else {}
                }
                
                success = await asset_extraction_service.update_user_state(user_id, extraction_result)
                
                if success:
                    logger.info(f"✅ Fallback extraction saved to DB for user {user_id}")
                else:
                    logger.error(f"❌ Failed to save fallback extraction for user {user_id}")
            else:
                logger.info(f"ℹ️ No data extracted in fallback for user {user_id}")
                
        except Exception as e:
            logger.error(f"❌ Fallback extraction failed for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def _trigger_insight_analysis(self, user_id: int, context: ChatContext) -> None:
        """
        Phase 3: Trigger cognitive insight analysis (System 2)
        Analyzes conversation history to generate psychological profile and advisor strategy
        
        ✅ FIXED: Now with proper interval control to reduce analysis frequency
        """
        try:
            message_count = len(context.conversation_history)
            
            # Skip if too few messages (need at least 3 for meaningful analysis)
            if message_count < 3:  # ✅ LOWERED from 5 to 3 messages
                logger.debug(f"Skipping insight analysis for user {user_id} - only {message_count} messages")
                return
            
            # ✅ MODIFIED: Trigger every 3 turns instead of 5 for better responsiveness
            if message_count % 3 != 0:
                logger.debug(
                    f"Skipping insight analysis for user {user_id} "
                    f"- not at trigger interval (count={message_count}, interval=3)"
                )
                return
            
            from app.services.insight_service import get_insight_service
            
            insight_service = get_insight_service()
            
            # Run analysis (now incremental, won't re-analyze old messages)
            logger.info(f"🔍 Triggering incremental insight analysis for user {user_id} at turn {message_count}")
            analysis_result = await insight_service.analyze_user_psychology(user_id)
            
            if analysis_result.get("skipped"):
                logger.debug(f"Insight analysis skipped: {analysis_result.get('reason')}")
            elif analysis_result.get("error"):
                logger.error(f"Insight analysis error: {analysis_result.get('error')}")
            else:
                logger.info(
                    f"✅ Incremental insight analysis completed for user {user_id}: "
                    f"sentiment={analysis_result.get('current_sentiment')}"
                )
            
        except Exception as e:
            logger.error(f"Error triggering insight analysis for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

    async def _trigger_information_extraction(self, user_message: str, user_id: int, context: ChatContext):
        """
        Phase 2: Trigger information extraction and state synchronization after AI response.
        This ensures the database is updated for the next turn of conversation.
        """
        try:
            logger.info(f"Starting information extraction for user {user_id}")
            
            # Import here to avoid circular imports
            from app.services.information_extraction import extract_information
            
            # Prepare conversation history for LLM context
            conversation_history = []
            for msg in context.conversation_history[-10:]:  # Last 10 messages
                conversation_history.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
            
            # Extract information using LLM-based extraction
            extraction_result = await extract_information(user_message, conversation_history)
            logger.info(f"Extraction result: {extraction_result}")
            
            # Update user state if extraction found anything
            if (extraction_result.get("assets") or 
                extraction_result.get("goals") or 
                extraction_result.get("risk_profile") or 
                extraction_result.get("completeness_update")):
                
                logger.info(f"🚀 EXTRACTION_TRIGGER: Found extractable data, calling update_user_state for user {user_id}")
                logger.info(f"🚀 EXTRACTION_TRIGGER: Data to update: assets={len(extraction_result.get('assets', []))}, "
                           f"goals={len(extraction_result.get('goals', []))}, "
                           f"risk_profile={bool(extraction_result.get('risk_profile'))}, "
                           f"completeness={extraction_result.get('completeness_update', {})}")
                
                success = await asset_extraction_service.update_user_state(user_id, extraction_result)
                
                if success:
                    logger.info(f"✅ EXTRACTION_TRIGGER: Successfully updated user state for user {user_id}")
                    
                    # Update context for immediate use
                    await self._update_context_from_extraction(context, extraction_result)
                else:
                    logger.error(f"❌ EXTRACTION_TRIGGER: Failed to update user state for user {user_id}")
                    # ✅ FIX: Add more detailed error information
                    logger.error(f"❌ EXTRACTION_TRIGGER: This may indicate database issues or user validation problems")
                    logger.error(f"❌ EXTRACTION_TRIGGER: Check if user {user_id} exists in the User table")
            else:
                logger.debug(f"No extractable information found in message from user {user_id}")
                
        except Exception as e:
            logger.error(f"Error in information extraction trigger for user {user_id}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    async def _update_context_from_extraction(self, context: ChatContext, extraction_result: dict):
        """Update conversation context with extraction results for immediate use"""
        try:
            # Update extracted assets in context
            assets_data = extraction_result.get("assets", [])
            for asset_data in assets_data:
                # Add to context.extracted_assets if not already present
                asset_exists = False
                for existing in context.extracted_assets:
                    if (existing.get("asset_type") == asset_data.get("type") and 
                        existing.get("name") == asset_data.get("name")):
                        # Update existing
                        existing.update({
                            "value": asset_data.get("amount", 0),
                            "location": asset_data.get("location"),
                            "area": asset_data.get("area"),
                            "confidence": 0.8  # High confidence from LLM extraction
                        })
                        asset_exists = True
                        break
                
                if not asset_exists:
                    context.extracted_assets.append({
                        "asset_type": asset_data.get("type"),
                        "name": asset_data.get("name", f"{asset_data.get('type')}资产"),
                        "value": asset_data.get("amount", 0),
                        "location": asset_data.get("location"),
                        "area": asset_data.get("area"),
                        "confidence": 0.8
                    })
            
            # Update user profile in context
            risk_profile = extraction_result.get("risk_profile", {})
            if risk_profile:
                if not context.user_profile:
                    context.user_profile = {}
                
                for key, value in risk_profile.items():
                    if value:
                        context.user_profile[key] = value
            
            logger.debug(f"Updated context with extraction results")
            
        except Exception as e:
            logger.error(f"Error updating context from extraction: {e}")

    async def _get_advisor_strategy_note(self, user_id: int) -> str | None:
        """
        Phase 3: Get advisor strategy note from cognitive insights
        This provides the AI with psychological profiling to adjust its behavior
        """
        try:
            from app.services.insight_service import get_insight_service
            
            insight_service = get_insight_service()
            advisor_note = await insight_service.get_advisor_strategy(user_id)
            
            return advisor_note
            
        except Exception as e:
            logger.error(f"Error getting advisor strategy note: {e}")
            return None

    async def _generate_fact_sheet(self, user_id: int) -> str:
        """
        Generate detailed Fact Sheet of confirmed assets and user profile to prevent AI hallucination.
        This replaces the simple checklist with a structured summary of actual data.
        
        FIXED: Now includes complete UserProfile information (age, family, occupation, income)
        """
        try:
            from sqlmodel import select
            from app.core.database import get_db_session
            
            fact_lines = ["【当前系统已确信的用户信息 (Fact Sheet)】"]
            
            async for session in get_db_session():
                # FIXED: Get UserProfile (L1) for complete user information
                profile_statement = select(UserProfile).where(UserProfile.user_id == user_id)
                profile_result = await session.execute(profile_statement)
                profile = profile_result.scalar_one_or_none()
                
                # Get all user assets from DB
                assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
                assets_result = await session.execute(assets_statement)
                assets = assets_result.scalars().all()
                
                # Check UserCognition (L2) for collection status and psychological insights
                cognition_statement = select(UserCognition).where(UserCognition.user_id == user_id)
                cognition_result = await session.execute(cognition_statement)
                cognition = cognition_result.scalar_one_or_none()
                
                # FIXED: Add complete user profile information at the top
                if profile:
                    fact_lines.append("\n【用户基本画像】")
                    
                    # Age range
                    if profile.age_range:
                        fact_lines.append(f"• 年龄段: {profile.age_range}岁")
                    
                    # Family structure
                    if profile.family_structure:
                        family_map = {
                            "single": "单身",
                            "married": "已婚",
                            "married_with_kids": "已婚有子女",
                            "divorced": "离异",
                            "widowed": "丧偶"
                        }
                        family_str = family_map.get(profile.family_structure, profile.family_structure)
                        fact_lines.append(f"• 家庭结构: {family_str}")
                    
                    # Occupation
                    if profile.occupation:
                        fact_lines.append(f"• 职业: {profile.occupation}")
                    
                    # Income range
                    if profile.income_range:
                        fact_lines.append(f"• 收入范围: {profile.income_range}")
                    
                    # Monthly expense
                    if profile.monthly_expense:
                        expense_str = f"{profile.monthly_expense/10000:.1f}万" if profile.monthly_expense >= 10000 else f"{profile.monthly_expense:.0f}元"
                        fact_lines.append(f"• 月支出: {expense_str}")
                    
                    # Risk preference
                    if profile.risk_preference:
                        risk_map = {
                            "conservative": "保守型",
                            "moderate": "稳健型",
                            "aggressive": "激进型"
                        }
                        risk_str = risk_map.get(profile.risk_preference.value if hasattr(profile.risk_preference, 'value') else profile.risk_preference, "未知")
                        fact_lines.append(f"• 风险偏好: {risk_str}")
                else:
                    fact_lines.append("\n【用户基本画像】")
                    fact_lines.append("(暂无用户画像信息)")
                
                # Add financial goals if available
                if cognition and cognition.financial_goals:
                    goal_map = {
                        "retirement": "退休规划",
                        "buy_house": "购房",
                        "education": "子女教育",
                        "wealth_growth": "财富增长"
                    }
                    goals_str = ", ".join([goal_map.get(g, g) for g in cognition.financial_goals])
                    fact_lines.append(f"• 财务目标: {goals_str}")
                
                # Assets section
                fact_lines.append("\n【资产清单】")
                
                if not assets:
                    fact_lines.append("(暂无已确认资产)")
                else:
                    # Group assets by type for better organization
                    assets_by_type = {}
                    for asset in assets:
                        asset_type = asset.asset_type.value
                        if asset_type not in assets_by_type:
                            assets_by_type[asset_type] = []
                        assets_by_type[asset_type].append(asset)
                    
                    # Generate detailed fact sheet entries
                    asset_index = 1
                    for asset_type, asset_list in assets_by_type.items():
                        for asset in asset_list:
                            # Format value
                            value_str = f"{asset.value/10000:.0f}万" if asset.value >= 10000 else f"{asset.value:.0f}元"
                            
                            # Build fact line based on asset type
                            if asset_type == "real_estate":
                                # Real estate: show location, value, area
                                location = asset.extra_data.get("location", "未知位置") if asset.extra_data else "未知位置"
                                area = asset.extra_data.get("area") if asset.extra_data else None
                                area_str = f" | 面积: {area}平米" if area else " | 面积: 未知"
                                confirmation = " (用户已确认)" if asset.is_confirmed else " (系统推测)"
                                fact_lines.append(
                                    f"{asset_index}. [房产] {asset.name} | 估值: {value_str}{area_str} | 位置: {location}{confirmation}"
                                )
                            elif asset_type == "cash":
                                confirmation = " (用户已确认)" if asset.is_confirmed else " (系统推测)"
                                fact_lines.append(
                                    f"{asset_index}. [现金] {value_str}{confirmation}"
                                )
                            elif asset_type == "investment":
                                # UPGRADED: Include subtype and risk_level for SP Quadrant classification
                                metadata = asset.extra_data or {}
                                subtype = metadata.get("subtype", "未知类型")
                                risk_level = metadata.get("risk_level", "未知风险")
                                
                                # Map subtype to Chinese
                                subtype_map = {
                                    "stock": "股票",
                                    "bond": "债券",
                                    "fund": "基金",
                                    "crypto": "加密货币",
                                    "property_fund": "房地产基金",
                                    "fixed_deposit": "定期存款",
                                    "money_fund": "货币基金",
                                    "bank_product": "银行理财",
                                    "equity_fund": "股票型基金"
                                }
                                subtype_cn = subtype_map.get(subtype, subtype)
                                
                                # Map risk_level to Chinese
                                risk_map = {
                                    "low": "低风险",
                                    "medium": "中风险",
                                    "high": "高风险"
                                }
                                risk_cn = risk_map.get(risk_level, risk_level)
                                
                                confirmation = " (用户已确认)" if asset.is_confirmed else " (系统推测)"
                                fact_lines.append(
                                    f"{asset_index}. [投资] {asset.name} (子类型: {subtype_cn}, 风险: {risk_cn}) | 价值: {value_str}{confirmation}"
                                )
                            elif asset_type == "insurance":
                                confirmation = " (用户已确认)" if asset.is_confirmed else " (系统推测)"
                                fact_lines.append(
                                    f"{asset_index}. [保险] {asset.name} | 保额: {value_str}{confirmation}"
                                )
                            elif asset_type == "liability":
                                # UPGRADED: Include monthly_payment for debt burden analysis
                                metadata = asset.extra_data or {}
                                monthly_payment = metadata.get("monthly_payment")
                                monthly_str = f" | 月供: {monthly_payment}元" if monthly_payment else ""
                                
                                confirmation = " (用户已确认)" if asset.is_confirmed else " (系统推测)"
                                fact_lines.append(
                                    f"{asset_index}. [负债] {asset.name} | 金额: {value_str}{monthly_str}{confirmation}"
                                )
                            
                            asset_index += 1
                
                # Add missing asset types as hints
                fact_lines.append("\n【缺失信息提示】")
                asset_types_present = {asset.asset_type.value for asset in assets}
                missing_types = []
                
                if "real_estate" not in asset_types_present:
                    missing_types.append("房产")
                if "cash" not in asset_types_present:
                    missing_types.append("现金储蓄")
                if "investment" not in asset_types_present:
                    missing_types.append("投资产品")
                if "insurance" not in asset_types_present:
                    missing_types.append("保险保障")
                
                if missing_types:
                    fact_lines.append(f"尚未了解: {', '.join(missing_types)}")
                else:
                    fact_lines.append("资产类型信息较完整")
                
                fact_lines.append("\n[重要提示] 请基于以上已确认的用户信息和资产数据回答问题，严禁编造或假设未提供的数据。")
                
                break  # Exit the async generator
            
            return "\n".join(fact_lines)
            
        except Exception as e:
            logger.error(f"Error generating fact sheet: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "【当前系统已确信的用户信息】\n(数据加载失败)"

    async def _prepare_contextual_input(self, message: str, context: ChatContext, user_id: int) -> str:
        """
        Prepare input with conversation context and Fact Sheet for better AI responses
        
        CRITICAL FIX: Now includes L0 Sliding Window History to prevent context discontinuity
        """
        contextual_parts = []
        
        # Add Fact Sheet at the beginning (most important context to prevent hallucination)
        fact_sheet = await self._generate_fact_sheet(user_id)
        contextual_parts.append(fact_sheet)
        
        # Phase 4: Add relevant memories from L3 Vector Memory (RAG)
        relevant_memories = await self._retrieve_relevant_memories(user_id, message)
        if relevant_memories:
            memory_context = "\n\n🧠 【RELEVANT MEMORIES】\n"
            for i, memory in enumerate(relevant_memories, 1):
                memory_context += f"{i}. {memory['content']} (相关度: {memory['similarity']:.2f})\n"
            memory_context += "[重要提示: 这些是用户之前提到的关键信息，请在回复中考虑这些背景。]"
            contextual_parts.append(memory_context)
        
        # Phase 3: Add advisor strategy note from cognitive insights (System 2)
        # ENHANCED: Dynamic Tone Refinement based on advisor note
        advisor_note = await self._get_advisor_strategy_note(user_id)
        if advisor_note:
            contextual_parts.append(
                f"\n\n💡 【ADVISOR STRATEGY NOTE】\n{advisor_note}\n"
                f"[Tone Instruction]: Based on the Advisor Note above, adopt this persona strictly. "
                f"Adjust your empathy level, risk tolerance guidance, and communication style accordingly. "
                f"The user cannot see this note - it's for your internal guidance only."
            )
        
        # FIX #1: Inject L0 Sliding Window History (6-10 recent messages)
        # This prevents "context discontinuity" where AI forgets what user just said
        if context.conversation_history:
            # Get last 6-10 messages (sliding window)
            recent_messages = context.conversation_history[-10:]  # Last 10 messages
            
            if len(recent_messages) > 0:
                history_block = "\n\n【近期对话回顾 (Recent Conversation History)】\n"
                history_block += "[重要提示: 以下是最近的对话历史，请仔细阅读以理解上下文和用户的引用（如'那个'、'之前的'等）]\n\n"
                
                for msg in recent_messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    
                    # Format role name
                    role_name = "用户" if role == "user" else "助手"
                    
                    # Truncate very long messages to save tokens
                    if len(content) > 300:
                        content = content[:300] + "..."
                    
                    history_block += f"{role_name}: {content}\n\n"
                
                history_block += "[重要提示: 上述对话历史帮助你理解当前消息的上下文。请基于历史对话回答用户的问题。]\n"
                contextual_parts.append(history_block)
        
        # Add the user's actual message (with clear marker)
        contextual_parts.append(f"\n【当前用户消息 (Current User Message)】\n{message}")

        # Add context about current stage
        if context.current_stage == "initial":
            contextual_parts.append("\n[系统提示: 用户刚开始对话，需要了解房产情况]")
        elif context.current_stage == "property_collection":
            contextual_parts.append(
                "\n[系统提示: 已收集部分房产信息，继续完善或询问其他资产]"
            )
        elif context.current_stage == "asset_collection":
            contextual_parts.append(
                "\n[系统提示: 房产信息较完整，需要收集其他资产和用户画像]"
            )
        elif context.current_stage == "analysis":
            contextual_parts.append("\n[系统提示: 信息收集完整，可以进行分析和建议]")

        # Add extracted assets summary
        if context.extracted_assets:
            asset_summary = f"\n[已提取资产: {len(context.extracted_assets)}项]"
            contextual_parts.append(asset_summary)

        # Add dynamic tone instructions based on user profile
        if context.user_profile:
            profile_fields = [
                k for k, v in context.user_profile.items() if v is not None
            ]
            profile_summary = f"\n[用户画像: {', '.join(profile_fields)}]"
            contextual_parts.append(profile_summary)
            
            # Dynamic tone hints based on risk profile
            risk_profile = context.user_profile.get("risk_profile")
            if risk_profile == "conservative":
                contextual_parts.append("\n[Tone Hint: Be extra cautious and focus on capital preservation]")
            elif risk_profile == "aggressive":
                contextual_parts.append("\n[Tone Hint: Focus on growth opportunities but remind about risks]")
            
            # Age-based tone hints
            age = context.user_profile.get("age")
            if age and age > 50:
                contextual_parts.append("\n[Tone Hint: Focus on retirement planning and liquidity]")
            
            # Debt-related empathy hints
            monthly_expenses = context.user_profile.get("monthly_expenses")
            if monthly_expenses and monthly_expenses > 20000:  # High expenses might indicate stress
                contextual_parts.append("\n[Tone Hint: Show empathy for financial pressure and focus on practical solutions]")

        return "".join(contextual_parts)
    
    async def _retrieve_relevant_memories(self, user_id: int, query_text: str) -> list[dict]:
        """
        Phase 4: Retrieve relevant memories from L3 Vector Memory
        Uses semantic search to find contextually relevant past information
        """
        try:
            from app.services.memory_service import get_memory_service
            
            memory_service = get_memory_service()
            
            # Retrieve top 3 most relevant memories
            memories = await memory_service.retrieve_relevant(
                user_id=user_id,
                query_text=query_text,
                limit=3,
                similarity_threshold=0.7  # Only include highly relevant memories
            )
            
            return memories
            
        except Exception as e:
            logger.error(f"Error retrieving relevant memories: {e}")
            return []

    async def _enhance_response_with_ui_components(
        self, response: str, context: ChatContext, user_id: int
    ) -> str:
        """Enhance AI response with appropriate UI components"""
        enhanced_response = response
        ui_components = []

        try:
            # Check if we should add valuation card
            if self.ui_service.should_generate_valuation_card(
                response, context.extracted_assets
            ):
                valuation_card = await self._generate_valuation_card(context)
                if valuation_card:
                    ui_components.append(valuation_card)

            # Check if we should add portfolio analysis and chart
            if (
                context.current_stage == "analysis"
                and len(context.extracted_assets) >= 2
            ):
                analysis_summary = await self._generate_portfolio_analysis(
                    context, user_id
                )
                # REMOVED: Double-response bug fix - Let AI persona control the conversation flow
                # The analysis_summary text was causing duplicate portfolio summaries
                # if analysis_summary:
                #     enhanced_response += f"\n\n{analysis_summary}"

                # Add portfolio chart if appropriate
                if self.ui_service.should_generate_portfolio_chart(
                    response, context.extracted_assets, context.current_stage
                ):
                    portfolio_chart = await self._generate_portfolio_chart(context)
                    if portfolio_chart:
                        ui_components.append(portfolio_chart)

            # Generate action cards based on portfolio analysis
            if context.portfolio_analysis and context.current_stage == "analysis":
                action_cards = await self.recommendation_service.generate_action_cards_for_portfolio(
                    context.portfolio_analysis
                )
                ui_components.extend(action_cards)

                # Track action card generation for analytics
                try:
                    risk_warnings = context.portfolio_analysis.get("risk_warnings", [])
                    for warning in risk_warnings[:3]:  # Track top 3 risks
                        await self.recommendation_service.track_user_interaction(
                            user_id=user_id,
                            product_id=0,  # Use 0 for system-generated recommendations
                            interaction_type="view",
                            metadata={
                                "risk_type": warning.get("type", ""),
                                "severity": warning.get("severity", ""),
                                "context": "portfolio_analysis",
                            },
                            session_id=context.session_id,
                        )
                except Exception as e:
                    logger.warning(f"Failed to track action card generation: {e}")

            elif self.ui_service.should_generate_action_cards(
                response, context.current_stage
            ):
                # Fallback to response-based action card generation
                action_cards = await self._generate_fallback_action_cards(response)
                ui_components.extend(action_cards)

            # Enhance response with all UI components
            enhanced_response = self.ui_service.enhance_response_with_components(
                enhanced_response, ui_components
            )

        except Exception as e:
            logger.error(f"Error enhancing response with UI components: {e}")

        return enhanced_response

        """Generate action card UI components based on context"""
        cards = []

        try:
            # Use portfolio analysis results if available
            if context.portfolio_analysis and context.current_stage == "analysis":
                risk_warnings = context.portfolio_analysis.get("risk_warnings", [])
                recommendations = context.portfolio_analysis.get("recommendations", [])

                # Generate cards from risk warnings
                for warning in risk_warnings[:2]:  # Limit to top 2 warnings
                    card_type = warning.get("type", "general")
                    priority = warning.get("severity", "medium")
                    if priority == "high":
                        priority = "high"
                    elif priority == "medium":
                        priority = "medium"
                    else:
                        priority = "low"

                    cards.append(
                        f'<WIDGET:ACTION_CARD data="{{'
                        f'"type": "{card_type}", '
                        f'"title": "{warning.get("title", "")}", '
                        f'"description": "{warning.get("recommendation", "")}", '
                        f'"priority": "{priority}"'
                        f'}}">'
                    )

                # Generate cards from recommendations
                for rec in recommendations[:2]:  # Limit to top 2 recommendations
                    cards.append(
                        f'<WIDGET:ACTION_CARD data="{{'
                        f'"type": "{rec.get("type", "general")}", '
                        f'"title": "{rec.get("title", "")}", '
                        f'"description": "{rec.get("description", "")}", '
                        f'"priority": "{rec.get("priority", "medium")}"'
                        f'}}">'
                    )

            # Fallback to response-based generation if no analysis available
            elif context.current_stage == "analysis":
                if "房产占比" in response and "过高" in response:
                    cards.append(
                        '<WIDGET:ACTION_CARD data="{'
                        '"type": "diversification", '
                        '"title": "资产多元化建议", '
                        '"description": "考虑增加其他投资类别以降低房产集中度风险", '
                        '"priority": "high"'
                        '}">'
                    )

                if "流动性" in response and ("不足" in response or "偏低" in response):
                    cards.append(
                        '<WIDGET:ACTION_CARD data="{'
                        '"type": "liquidity", '
                        '"title": "增加流动性储备", '
                        '"description": "建议增加现金储备至6个月生活费用", '
                        '"priority": "medium"'
                        '}">'
                    )

                if "保险" in response and ("缺乏" in response or "不足" in response):
                    cards.append(
                        '<WIDGET:ACTION_CARD data="{'
                        '"type": "insurance", '
                        '"title": "完善保险保障", '
                        '"description": "建议配置重疾险和意外险以降低风险", '
                        '"priority": "high"'
                        '}">'
                    )

        except Exception as e:
            logger.error(f"Error generating action cards: {e}")

        return cards

    async def _generate_valuation_card(self, context: ChatContext) -> str | None:
        """Generate valuation card UI component"""
        try:
            # Find the most recent real estate asset
            real_estate_assets = [
                asset
                for asset in context.extracted_assets
                if asset.get("asset_type") == "real_estate"
            ]

            if not real_estate_assets:
                return None

            asset = real_estate_assets[-1]  # Most recent

            return self.ui_service.generate_valuation_card(
                price=asset.get("value", 0),
                area=asset.get("area", 0),
                location=asset.get("location", "未知位置"),
                confidence=asset.get("confidence", 0.8),
            )

        except Exception as e:
            logger.error(f"Error generating valuation card: {e}")
            return None

    async def _generate_fallback_action_cards(self, response: str) -> list[str]:
        """Generate fallback action cards based on response content"""
        cards = []

        try:
            if "房产占比" in response and "过高" in response:
                cards.append(
                    self.ui_service.generate_action_card(
                        action_type="diversification",
                        title="资产多元化建议",
                        description="考虑增加其他投资类别以降低房产集中度风险",
                        priority="high",
                    )
                )

            if "流动性" in response and ("不足" in response or "偏低" in response):
                cards.append(
                    self.ui_service.generate_action_card(
                        action_type="liquidity",
                        title="增加流动性储备",
                        description="建议增加现金储备至6个月生活费用",
                        priority="medium",
                    )
                )

            if "保险" in response and ("缺乏" in response or "不足" in response):
                cards.append(
                    self.ui_service.generate_action_card(
                        action_type="insurance",
                        title="完善保险保障",
                        description="建议配置重疾险和意外险以降低风险",
                        priority="high",
                    )
                )

        except Exception as e:
            logger.error(f"Error generating fallback action cards: {e}")

        return cards

    async def _generate_portfolio_chart(self, context: ChatContext) -> str | None:
        """Generate portfolio chart UI component"""
        try:
            if not context.extracted_assets:
                return None

            # Convert extracted assets to UserAsset-like objects for the UI service
            from app.models.user import AssetType

            mock_assets = []
            for asset_data in context.extracted_assets:
                if asset_data.get("value", 0) > 0:
                    # Create a mock UserAsset object
                    class MockAsset:
                        def __init__(self, asset_type, name, value):
                            self.asset_type = AssetType(asset_type)
                            self.name = name
                            self.value = value

                    mock_asset = MockAsset(
                        asset_type=asset_data.get("asset_type", "cash"),
                        name=asset_data.get("name", "未知资产"),
                        value=asset_data.get("value", 0),
                    )
                    mock_assets.append(mock_asset)

            if not mock_assets:
                return None

            return self.ui_service.generate_portfolio_chart(mock_assets)

        except Exception as e:
            logger.error(f"Error generating portfolio chart: {e}")
            return None

    async def _generate_portfolio_chart(self, context: ChatContext) -> str | None:
        """Generate portfolio chart UI component"""
        try:
            if not context.extracted_assets:
                return None

            # Convert extracted assets to UserAsset-like objects for the UI service
            from app.models.user import AssetType

            mock_assets = []
            for asset_data in context.extracted_assets:
                if asset_data.get("value", 0) > 0:
                    # Create a mock UserAsset object
                    class MockAsset:
                        def __init__(self, asset_type, name, value):
                            self.asset_type = AssetType(asset_type)
                            self.name = name
                            self.value = value

                    mock_asset = MockAsset(
                        asset_type=asset_data.get("asset_type", "cash"),
                        name=asset_data.get("name", "未知资产"),
                        value=asset_data.get("value", 0),
                    )
                    mock_assets.append(mock_asset)

            if not mock_assets:
                return None

            return self.ui_service.generate_portfolio_chart(mock_assets)

        except Exception as e:
            logger.error(f"Error generating portfolio chart: {e}")
            return None

    async def _generate_portfolio_analysis(
        self, context: ChatContext, user_id: int
    ) -> str | None:
        """Generate portfolio analysis summary"""
        try:
            from sqlmodel import select

            from app.core.database import get_db_session

            # Get user assets from database
            async for session in get_db_session():
                assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
                assets_result = await session.execute(assets_statement)
                assets = assets_result.scalars().all()

                profile_statement = select(UserProfile).where(
                    UserProfile.user_id == user_id
                )
                profile_result = await session.execute(profile_statement)
                profile = profile_result.scalar_one_or_none()

            if not assets:
                return None

            # Perform portfolio analysis
            analysis = portfolio_analyzer.analyze_portfolio(assets, profile)

            # Generate summary text
            summary = portfolio_analyzer.generate_analysis_summary(analysis)

            # Store analysis results in context for action card generation
            context.portfolio_analysis = {
                "net_worth": analysis.net_worth,
                "real_estate_ratio": analysis.real_estate_ratio,
                "liquidity_ratio": analysis.liquidity_ratio,
                "risk_warnings": analysis.risk_warnings,
                "recommendations": analysis.recommendations,
                "overall_risk_level": analysis.overall_risk_level.value,
                # Standard & Poor's Four Quadrant Analysis
                "quadrant_analysis": analysis.quadrant_analysis,
                "quadrant_allocations": {
                    k.value: v for k, v in analysis.quadrant_allocations.items()
                },
                "ideal_allocations": {
                    k.value: v for k, v in analysis.ideal_allocations.items()
                },
                "allocation_gaps": {
                    k.value: v for k, v in analysis.allocation_gaps.items()
                },
            }

            return f"\n📊 **资产配置分析**\n{summary}"

        except Exception as e:
            logger.error(f"Error generating portfolio analysis: {e}")
            return None

    def extract_ui_components(self, response: str) -> list[UIComponent]:
        """Extract UI component tags from AI response"""
        return self.ui_service.extract_ui_components(response)

    def get_conversation_context(self, user_id: int) -> ChatContext | None:
        """Get conversation context for a user"""
        return self.contexts.get(user_id)

    def clear_conversation_context(self, user_id: int):
        """Clear conversation context for a user"""
        if user_id in self.contexts:
            del self.contexts[user_id]


# Global agent instance
chat_agent: ChatAgent | None = None


def get_chat_agent() -> ChatAgent:
    """Get or create chat agent instance"""
    global chat_agent
    if chat_agent is None:
        chat_agent = ChatAgent()
    return chat_agent
