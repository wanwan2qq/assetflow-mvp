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
from app.models.user import UserAsset, UserProfile
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

        # Define the system prompt
        system_prompt = """你是AssetFlow的AI资产配置顾问，专门为中国家庭提供基于标准普尔四象限模型的专业资产配置建议。

你的主要职责：
1. 通过自然对话引导用户完成资产盘点
2. 使用搜索工具获取房产估值
3. 基于标准普尔四象限模型提供配置建议
4. 生成结构化的UI组件标签

标准普尔四象限模型详解：
**要花的钱（10%）**：日常开销和应急资金，建议6个月生活费，存放在高流动性账户
**保命的钱（20%）**：保险保障，包括重疾险、意外险、寿险等，保障家庭风险
**生钱的钱（30%）**：高风险高收益投资，如股票、股票基金、房地产投资等
**保本升值的钱（40%）**：稳健投资，如债券、银行理财、定期存款等

配置比例会根据用户画像动态调整：
- 年轻用户：生钱的钱可增至40%，保本升值的钱减至30%
- 年长用户：生钱的钱减至20%，保本升值的钱增至50%
- 有孩子家庭：要花的钱增至15%，保命的钱增至25%
- 保守型用户：生钱的钱减至15%，保本升值的钱增至45%
- 激进型用户：生钱的钱增至45%，保本升值的钱减至32%

对话流程控制：
- 初始阶段：主动询问用户的房产情况（位置、面积、购买时间等）
- 房产收集阶段：使用property_search工具获取估值，确认房产价值
- 资产收集阶段：系统性询问其他资产类别（现金、投资、负债、保险）
- 用户画像阶段：了解年龄、家庭结构、风险偏好、月支出等
- 分析阶段：基于四象限模型进行资产配置分析

具体引导策略：
1. 当用户首次对话时，友好地询问："您好！我是您的AI资产配置顾问，将基于标准普尔四象限模型为您提供专业建议。为了开始分析，我想先了解一下您的房产情况。请问您目前有房产吗？在哪个城市？"

2. 当获得房产信息后，使用property_search工具查询市场价格，然后说："根据市场数据，我估算您的房产价值约为X万元。这个估值是否合理？"

3. 当房产信息确认后，继续询问："除了房产，我还需要了解您的其他资产情况。请问您目前有多少现金储蓄？"

4. 依次询问投资、负债、保险等信息，每次只问一个类别。

5. 当资产信息收集完整后，询问用户画像："为了给您更精准的四象限配置建议，请问您的年龄段和家庭情况？"

6. 信息收集完整后，进行分析："基于您提供的信息，我来为您分析一下标准普尔四象限资产配置情况..."

UI组件生成规则：
- 当确认房产估值时，生成：<WIDGET:VALUATION_CARD data="{{price: 价格, area: 面积, location: '位置'}}">
- 当发现风险问题时，生成：<WIDGET:ACTION_CARD data="{{type: '类型', title: '标题', description: '描述', priority: '优先级'}}">
- 当进行资产分析时，生成：<WIDGET:PORTFOLIO_CHART data="{{assets: [资产数组]}}">

重要原则：
- 保持对话自然、专业且友好，避免机械化问答
- 逐步引导，每次只询问一个主题，避免信息过载
- 对房产估值应用0.95的保守系数
- 严格按照标准普尔四象限模型进行分析和建议
- 根据用户画像动态调整四象限配置比例
- 在适当时机自动插入UI组件标签
- 当用户提供不完整信息时，礼貌地要求补充
- 始终以用户的财务安全和长期利益为出发点
- 明确说明每个象限的作用和建议配置比例
"""

        # Create agent using the new API
        agent = create_agent(
            model=self.llm, tools=[self.search_tool], system_prompt=system_prompt
        )

        return agent

    async def process_message(
        self, message: str, user_id: int, user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """Process user message and return streaming response"""

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
            await self._extract_and_store_information(context, message, user_id)

            # Prepare input for agent with context
            agent_input = {
                "messages": [
                    {
                        "role": "user",
                        "content": self._prepare_contextual_input(message, context),
                    }
                ]
            }

            # Stream response from agent
            response_chunks = []
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
                            yield chunk_text

            # Store AI response in history
            full_response = "".join(response_chunks)
            context.conversation_history.append(
                {
                    "role": "assistant",
                    "content": full_response,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Generate and inject UI components based on context
            ui_enhanced_response = await self._enhance_response_with_ui_components(
                full_response, context, user_id
            )

            if ui_enhanced_response != full_response:
                yield ui_enhanced_response[
                    len(full_response) :
                ]  # Only yield the new UI parts

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    async def _process_message_mock(
        self, message: str, user_id: int, user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """Mock message processing for development environment"""
        
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
            await self._extract_and_store_information(context, message, user_id)

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

        except Exception as e:
            logger.error(f"Error processing mock message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    def _generate_mock_response(self, message: str, context: ChatContext) -> str:
        """Generate mock AI response based on message content and context"""
        
        message_lower = message.lower()
        
        # Greeting responses
        if any(greeting in message_lower for greeting in ["你好", "hello", "hi", "您好"]):
            if context.current_stage == "initial":
                return "您好！我是您的AI资产配置顾问，将基于标准普尔四象限模型为您提供专业建议。为了开始分析，我想先了解一下您的房产情况。请问您目前有房产吗？在哪个城市？"
            else:
                return "您好！很高兴继续为您服务。请告诉我您还想了解什么？"
        
        # Property-related responses
        if any(word in message_lower for word in ["房", "房产", "房子", "小区", "楼盘"]):
            if context.current_stage == "initial":
                # Try to extract property info and provide valuation
                if "北京" in message or "上海" in message or "深圳" in message or "广州" in message:
                    return "好的，我了解到您在一线城市有房产。能告诉我具体的小区名称和房屋面积吗？这样我可以为您提供更准确的估值。"
                else:
                    return "感谢您提供房产信息。为了给您准确的估值，请告诉我：1）房产所在的具体城市和小区名称；2）房屋面积（平方米）；3）大概的购买时间。"
            else:
                return "关于您的房产配置，根据标准普尔四象限模型，房产通常属于'生钱的钱'象限。我建议您的房产占总资产比例不要超过60%，以保持资产配置的平衡。"
        
        # Asset-related responses
        if any(word in message_lower for word in ["资产", "投资", "理财", "存款", "股票", "基金"]):
            return "很好！除了房产，了解您的其他资产情况对制定配置方案很重要。请告诉我您目前的：1）现金储蓄；2）投资产品（股票、基金等）；3）保险情况；4）其他负债。我会根据标准普尔四象限模型为您分析。"
        
        # Analysis requests
        if any(word in message_lower for word in ["分析", "建议", "配置", "怎么办", "如何"]):
            if len(context.extracted_assets) >= 1:
                return "基于您提供的信息，我来为您分析标准普尔四象限资产配置：\n\n**要花的钱（10%）**：日常开销和应急资金\n**保命的钱（20%）**：保险保障\n**生钱的钱（30%）**：高风险高收益投资\n**保本升值的钱（40%）**：稳健投资\n\n根据您的情况，我建议优先完善应急资金储备和保险保障。"
            else:
                return "要为您提供准确的配置建议，我需要先了解您的资产情况。请先告诉我您的房产、现金储蓄、投资和负债情况，然后我会基于标准普尔四象限模型为您制定个性化方案。"
        
        # Numbers or financial amounts
        if any(char.isdigit() for char in message):
            if "万" in message or "元" in message:
                return "感谢您提供具体的金额信息。这对我制定精准的配置建议很有帮助。请继续告诉我其他资产类别的情况，这样我就能为您进行全面的四象限分析了。"
            else:
                return "我注意到您提到了一些数字。如果这是关于资产金额的，请告诉我具体是哪类资产，金额是多少，这样我能更好地为您分析。"
        
        # Default response based on conversation stage
        if context.current_stage == "initial":
            return "我是您的AI资产配置顾问。为了给您最合适的建议，让我们从了解您的房产情况开始吧。请问您目前有房产吗？"
        elif context.current_stage == "property_collection":
            return "很好，我们已经收集了一些房产信息。现在请告诉我您的其他资产情况，比如现金储蓄、投资产品等。"
        elif context.current_stage == "asset_collection":
            return "资产信息收集得差不多了。为了给您更精准的建议，请告诉我您的年龄段、家庭情况和风险偏好。"
        else:
            return "基于您提供的信息，我建议按照标准普尔四象限模型进行资产配置。您还有什么具体问题想了解吗？"

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

        except Exception as e:
            logger.error(f"Error extracting and storing information: {e}")

    def _prepare_contextual_input(self, message: str, context: ChatContext) -> str:
        """Prepare input with conversation context for better AI responses"""
        contextual_parts = [message]

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

        # Add user profile summary
        if context.user_profile:
            profile_fields = [
                k for k, v in context.user_profile.items() if v is not None
            ]
            profile_summary = f"\n[用户画像: {', '.join(profile_fields)}]"
            contextual_parts.append(profile_summary)

        return "".join(contextual_parts)

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
                if analysis_summary:
                    enhanced_response += f"\n\n{analysis_summary}"

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
