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

        # Define the system prompt with Senior Private Banker persona
        system_prompt = """你不仅仅是AI，你是AssetFlow的首席资产配置专家（Chief Asset Allocation Expert）。你的目标是不仅提供数据，更提供"财务安全感"。

**核心人设 (Persona)：**
* **专业而温暖**：像一位相识多年的老友，专业但不说教。请适度使用emoji (如 🤝, 💡, 📈) 来活跃气氛，但不要滥用。
* **结果导向**：不要为了收集信息而收集信息。如果用户直接问"我有50万怎么投"，请直接给出基于假设的初步建议，然后再温和地补充询问细节。
* **拒绝机械**：严禁使用"Step 1: xxx"这种机器人的说话方式。将流程内化于对话中。
* **共情能力**：当用户表达焦虑（如房贷压力、股市亏损）时，先给予情感上的回应和安抚。

**CRITICAL: 信息状态检查规则 (Information State Rules)：**
* **严格遵循状态检查**：每次回复前，必须查看【当前信息采集状态】部分
* **禁止重复询问**：对于标记为 [✅] 的项目，绝对不要再次询问相同信息
* **聚焦缺失信息**：只询问标记为 [❌] 的项目，优先处理最重要的缺失信息
* **智能过渡策略**：如果 [✅] 房产已知但 [❌] 现金缺失，说："我看到您的房产信息了。为了平衡您的投资组合，请问您目前的现金储备大概有多少？"
* **避免清单式询问**：不要一次性问多个缺失项目，每次只专注一个核心问题

**标准普尔四象限逻辑 (The Logic)：**
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

**交互策略 (Interaction Strategy)：**
1. **房产估值**：当用户提到房产时，先赞赏其资产积累，再自然地调取 `property_search` 工具。
   * *Bad*: "系统检测到房产，正在查询估值..."
   * *Good*: "哇，在那个地段拥有房产非常棒！💡 让我帮您看看现在的市场参考价，稍等..."

2. **资产盘点**：不要像查户口一样连续追问。每次只问一个核心问题，并解释"为什么我要问这个问题"。
   * *Example*: "为了帮您平衡风险，我还想了解一下您手头的流动资金（现金/活期）大概能覆盖几个月的开销？"

3. **共情回应**：当用户表达财务压力时，先安抚情绪。
   * *Example*: "我理解高房贷确实会带来压力 🤝，这种担心很正常。让我们一起看看如何优化您的资产配置来缓解这种压力..."

4. **动态建议**：根据用户具体问题直接给建议，不要总是要求完整信息。
   * *Example*: 用户问"50万怎么投" → 直接给出基于假设的配置建议，然后说"当然，如果您能告诉我更多情况，我可以给出更精准的建议"

**UI组件触发规则 (Critical)：**
- 当确认房产估值时，生成：<WIDGET:VALUATION_CARD data="{{price: 价格, area: 面积, location: '位置'}}">
- 当发现风险问题时，生成：<WIDGET:ACTION_CARD data="{{type: '类型', title: '标题', description: '描述', priority: '优先级'}}">
- 当进行资产分析时，生成：<WIDGET:PORTFOLIO_CHART data="{{assets: [资产数组]}}">

**安全原则：**
- 严禁编造任何财务数据或市场信息
- 所有房产估值必须通过property_search工具获取
- 严格遵循标准普尔四象限模型逻辑
- 始终以用户的财务安全和长期利益为出发点
- 当信息不足时，基于合理假设给出建议，但要明确说明假设条件
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

            # Save AI message to database (after generation is complete)
            try:
                await chat_history_service.save_ai_message(user_id, ui_enhanced_response)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")

            # Phase 2: Trigger information extraction and state sync after AI response
            try:
                await self._trigger_information_extraction(message, user_id, context)
            except Exception as e:
                logger.error(f"Failed to trigger information extraction: {e}")
            
            # Phase 3: Trigger cognitive insight analysis (System 2) as background task
            # This runs asynchronously to avoid blocking the response
            try:
                await self._trigger_insight_analysis(user_id, context)
            except Exception as e:
                logger.error(f"Failed to trigger insight analysis: {e}")

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

            # Phase 2: Trigger information extraction and state sync after AI response
            try:
                await self._trigger_information_extraction(message, user_id, context)
            except Exception as e:
                logger.error(f"Failed to trigger information extraction: {e}")
            
            # Phase 3: Trigger cognitive insight analysis (System 2) as background task
            try:
                await self._trigger_insight_analysis(user_id, context)
            except Exception as e:
                logger.error(f"Failed to trigger insight analysis: {e}")

        except Exception as e:
            logger.error(f"Error processing mock message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    def _generate_mock_response(self, message: str, context: ChatContext) -> str:
        """Generate mock AI response based on message content and context"""
        
        message_lower = message.lower()
        
        # Check for emotional keywords that need empathy
        stress_keywords = ["压力", "焦虑", "担心", "困难", "亏损", "负债", "房贷"]
        has_stress = any(keyword in message_lower for keyword in stress_keywords)
        
        # Greeting responses with warm persona
        if any(greeting in message_lower for greeting in ["你好", "hello", "hi", "您好"]):
            if context.current_stage == "initial":
                return "您好！🤝 我是AssetFlow的首席资产配置专家，很高兴为您服务！我不只是提供数据分析，更希望能给您带来财务安全感。\n\n让我们从了解您的资产情况开始吧 💡 - 请问您目前有房产吗？不用担心信息不全，我们可以边聊边完善。"
            else:
                return "您好！很高兴继续为您服务 🤝 有什么新的财务问题想要探讨吗？"
        
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
                return "我理解投资有时会让人感到压力 🤝 这很正常，让我们一起梳理一下您的资产情况，找到最适合的配置方案。\n\n除了房产，请告诉我您目前的：\n💰 现金储蓄大概有多少？\n📈 投资产品（股票、基金等）情况如何？\n🛡️ 保险配置是否完善？\n\n我会根据标准普尔四象限模型为您分析，帮您找到平衡点。"
            else:
                return "很好！💡 全面了解资产情况是制定配置方案的基础。让我们按四象限来梳理：\n\n🔹 **流动资金**：现金储蓄有多少？\n🔹 **投资产品**：股票、基金等情况？\n🔹 **保险保障**：重疾险、意外险是否配置？\n🔹 **负债情况**：房贷或其他负债？\n\n不用一次性全部说完，我们可以一项项来聊 🤝"
        
        # Analysis requests with empathy
        if any(word in message_lower for word in ["分析", "建议", "配置", "怎么办", "如何"]):
            if len(context.extracted_assets) >= 1:
                return "基于您提供的信息，让我为您分析标准普尔四象限资产配置 📊\n\n**四象限配置逻辑：**\n🔹 **要花的钱（10%）**：应急资金，6个月生活费\n🔹 **保命的钱（20%）**：保险保障，守护家庭\n🔹 **生钱的钱（30%）**：高收益投资，财富增长\n🔹 **保本升值（40%）**：稳健投资，保值增值\n\n根据您的情况，我建议优先完善应急资金储备和保险保障 💡 这样能给您更多安全感。"
            else:
                return "我很乐意为您提供配置建议！💡 不过为了给出最适合您的方案，我需要先了解您的资产情况。\n\n我们可以从最重要的开始：\n🏠 房产情况（位置、价值）\n💰 现金储蓄\n📈 现有投资\n\n有了这些信息，我就能基于标准普尔四象限模型为您制定个性化方案了 🤝"
        
        # Numbers or financial amounts with encouragement
        if any(char.isdigit() for char in message):
            if "万" in message or "元" in message:
                return "感谢您提供具体的金额信息！💡 这对制定精准的配置建议很有帮助。\n\n让我们继续完善其他资产类别的情况，这样我就能为您进行全面的四象限分析了。您还有其他投资或储蓄想要一起考虑的吗？"
            else:
                return "我注意到您提到了一些数字 🤔 如果这是关于资产金额的，请告诉我具体是哪类资产，金额是多少，这样我能更好地为您分析配置方案。"
        
        # Default responses based on conversation stage with warm tone
        if context.current_stage == "initial":
            return "我是您的首席资产配置专家 🤝 让我们从了解您的房产情况开始吧！这是很多家庭最重要的资产。请问您目前有房产吗？在哪个城市呢？"
        elif context.current_stage == "property_collection":
            return "很好，房产信息我们已经有了基础了解 🏠 现在让我们看看其他资产情况。比如您手头的现金储蓄大概有多少？这对应四象限中的'要花的钱'部分。"
        elif context.current_stage == "asset_collection":
            return "资产信息收集得不错！💡 为了给您更精准的四象限配置建议，我还想了解一下您的个人情况：年龄段、家庭结构，以及您对投资风险的接受程度如何？"
        else:
            return "基于您提供的信息，我建议按照标准普尔四象限模型进行资产配置 📊 您还有什么具体问题想了解吗？我很乐意为您详细解答 🤝"

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

    async def _update_cognition_state(self, user_id: int, assets: list, profile: dict | None = None):
        """Update UserCognition collection status when new information is extracted"""
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
                
                # Update risk profile if provided
                if profile and hasattr(profile, 'risk_preference'):
                    if not cognition.risk_profile:
                        cognition.risk_profile = {}
                    cognition.risk_profile['tolerance'] = profile.risk_preference
                    cognition.updated_at = datetime.utcnow()
                
                await session.commit()
                logger.info(f"Updated cognition state for user {user_id}")
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

    async def _trigger_insight_analysis(self, user_id: int, context: ChatContext) -> None:
        """
        Phase 3: Trigger cognitive insight analysis (System 2)
        Analyzes conversation history to generate psychological profile and advisor strategy
        
        Optimization: Only trigger every N turns to save tokens
        """
        try:
            # Optimization: Only analyze every 3-5 turns to save API costs
            # For MVP, we analyze every turn for demonstration
            message_count = len(context.conversation_history)
            
            # Skip if too few messages (need at least 5 for meaningful analysis)
            if message_count < 5:
                logger.debug(f"Skipping insight analysis for user {user_id} - only {message_count} messages")
                return
            
            # Optional: Only trigger every N turns (uncomment for production optimization)
            # if message_count % 5 != 0:
            #     logger.debug(f"Skipping insight analysis for user {user_id} - not at trigger interval")
            #     return
            
            from app.services.insight_service import get_insight_service
            
            insight_service = get_insight_service()
            
            # Run analysis (this is fire-and-forget, doesn't block response)
            logger.info(f"Triggering insight analysis for user {user_id}")
            analysis_result = await insight_service.analyze_user_psychology(user_id)
            
            if analysis_result.get("skipped"):
                logger.debug(f"Insight analysis skipped: {analysis_result.get('reason')}")
            elif analysis_result.get("error"):
                logger.error(f"Insight analysis error: {analysis_result.get('error')}")
            else:
                logger.info(f"Insight analysis completed for user {user_id}: sentiment={analysis_result.get('current_sentiment')}")
            
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
                
                logger.info(f"Found extractable data, calling update_user_state for user {user_id}")
                success = await asset_extraction_service.update_user_state(user_id, extraction_result)
                
                if success:
                    logger.info(f"Successfully updated user state for user {user_id}")
                    
                    # Update context for immediate use
                    await self._update_context_from_extraction(context, extraction_result)
                else:
                    logger.warning(f"Failed to update user state for user {user_id}")
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

    async def _generate_state_checklist(self, user_id: int) -> str:
        """
        Generate information collection state checklist for LLM context.
        This prevents repetitive questioning by showing what's already known.
        """
        try:
            from sqlmodel import select
            from app.core.database import get_db_session
            
            checklist_lines = ["【当前信息采集状态 (Information State)】"]
            
            async for session in get_db_session():
                # Check UserAsset (L1) for asset types
                assets_statement = select(UserAsset).where(UserAsset.user_id == user_id)
                assets_result = await session.execute(assets_statement)
                assets = assets_result.scalars().all()
                
                # Check UserCognition (L2) for collection status
                cognition_statement = select(UserCognition).where(UserCognition.user_id == user_id)
                cognition_result = await session.execute(cognition_statement)
                cognition = cognition_result.scalar_one_or_none()
                
                # Asset type status mapping
                asset_types = {
                    "real_estate": "房产 (Real Estate)",
                    "cash": "现金 (Cash)", 
                    "investment": "投资 (Investment)",
                    "insurance": "保险 (Insurance)",
                    "liability": "负债 (Debt)"
                }
                
                # Track what assets exist in DB
                existing_assets = {}
                for asset in assets:
                    asset_type = asset.asset_type.value
                    if asset_type not in existing_assets:
                        existing_assets[asset_type] = []
                    existing_assets[asset_type].append({
                        "name": asset.name,
                        "value": asset.value
                    })
                
                # Generate checklist for each asset type
                for asset_key, asset_label in asset_types.items():
                    if asset_key in existing_assets:
                        # Asset exists - show as collected
                        asset_info = existing_assets[asset_key][0]  # Show first asset
                        if asset_key == "real_estate":
                            value_str = f"{asset_info['value']/10000:.0f}万" if asset_info['value'] >= 10000 else f"{asset_info['value']:.0f}元"
                            checklist_lines.append(f"[✅] {asset_label}: 已知 ({asset_info['name']}, {value_str})")
                        else:
                            value_str = f"{asset_info['value']/10000:.0f}万" if asset_info['value'] >= 10000 else f"{asset_info['value']:.0f}元"
                            checklist_lines.append(f"[✅] {asset_label}: 已知 ({value_str})")
                    else:
                        # Asset missing
                        checklist_lines.append(f"[❌] {asset_label}: 未知 (Missing)")
                
                # Check cognition profile status
                if cognition and cognition.risk_profile:
                    risk_info = cognition.risk_profile.get("tolerance", "未知")
                    checklist_lines.append(f"[✅] 认知画像 (Profile): 风险偏好 {risk_info}")
                else:
                    checklist_lines.append(f"[⚠️] 认知画像 (Profile): 缺少风险偏好")
                
                break  # Exit the async generator
            
            return "\n".join(checklist_lines)
            
        except Exception as e:
            logger.error(f"Error generating state checklist: {e}")
            return "【当前信息采集状态】\n[⚠️] 状态检查失败"

    async def _prepare_contextual_input(self, message: str, context: ChatContext, user_id: int) -> str:
        """Prepare input with conversation context and state checklist for better AI responses"""
        contextual_parts = []
        
        # Add state checklist at the beginning (most important context)
        state_checklist = await self._generate_state_checklist(user_id)
        contextual_parts.append(state_checklist)
        
        # Phase 4: Add relevant memories from L3 Vector Memory (RAG)
        relevant_memories = await self._retrieve_relevant_memories(user_id, message)
        if relevant_memories:
            memory_context = "\n\n🧠 【RELEVANT MEMORIES】\n"
            for i, memory in enumerate(relevant_memories, 1):
                memory_context += f"{i}. {memory['content']} (相关度: {memory['similarity']:.2f})\n"
            memory_context += "[重要提示: 这些是用户之前提到的关键信息，请在回复中考虑这些背景。]"
            contextual_parts.append(memory_context)
        
        # Phase 3: Add advisor strategy note from cognitive insights (System 2)
        advisor_note = await self._get_advisor_strategy_note(user_id)
        if advisor_note:
            contextual_parts.append(f"\n\n💡 【ADVISOR STRATEGY NOTE】\n{advisor_note}\n[重要提示: 根据上述策略调整你的语气和建议方向。用户看不到这条笔记。]")
        
        # Add the user's actual message
        contextual_parts.append(f"\n【用户消息】\n{message}")

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
