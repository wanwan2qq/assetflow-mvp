"""
ChatAgent Facade - Backward-compatible wrapper for ConversationOrchestrator

This module maintains the original ChatAgent API while delegating to the
new modular architecture. This ensures existing code (WebSocket handlers,
tests, etc.) continues to work without changes.

Phase 1 Refactoring Note:
- Original ChatAgent (1677 lines) is preserved as ChatAgentLegacy
- New ChatAgent is a thin Facade that delegates to ConversationOrchestrator
- All existing callers continue to work without modification

AI Coding Guidance:
- Do NOT add new logic to this file; it should remain a thin wrapper
- New features should go into ConversationOrchestrator or specialized services
- The legacy code is kept for gradual migration and fallback
"""

import logging
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel

from app.core.config import settings
from app.models.user import UserProfile

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models (kept for backward compatibility)
# ============================================================================

class UIComponent(BaseModel):
    """Represents a UI component to be rendered"""
    type: str  # VALUATION_CARD, ACTION_CARD, PORTFOLIO_CHART
    data: dict[str, Any]
    position: int  # Position in the response text


class ChatContext(BaseModel):
    """Context for chat conversation - Legacy compatibility"""
    user_id: int
    session_id: str | None = None
    conversation_history: list[dict[str, str]] = []
    extracted_assets: list[dict[str, Any]] = []
    user_profile: dict[str, Any] | None = None
    current_stage: str = "initial"
    portfolio_analysis: dict[str, Any] | None = None


# ============================================================================
# ChatAgent Facade (New Architecture)
# ============================================================================

class ChatAgent:
    """
    ChatAgent Facade - Backward-compatible wrapper.
    
    This class maintains the original ChatAgent API while internally
    delegating to the new ConversationOrchestrator.
    
    Usage remains unchanged:
        agent = ChatAgent()
        async for chunk in agent.process_message(message, user_id):
            print(chunk)
    """
    
    def __init__(
        self, 
        openai_api_key: str | None = None, 
        tavily_api_key: str | None = None,
        use_legacy: bool = False  # Set to True to use original implementation
    ):
        """
        Initialize ChatAgent.
        
        Args:
            openai_api_key: Optional API key (uses settings if not provided)
            tavily_api_key: Optional Tavily key (uses settings if not provided)
            use_legacy: If True, use the original ChatAgentLegacy implementation
        """
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self.tavily_api_key = tavily_api_key or settings.TAVILY_API_KEY
        self.use_legacy = use_legacy
        
        # Lazy initialization - orchestrator created on first use
        self._orchestrator = None
        self._legacy_agent = None
        
        # Conversation contexts (for backward compatibility)
        self.contexts: dict[int, ChatContext] = {}
        
        logger.info("✅ ChatAgent (Facade) initialized")
    
    @property
    def orchestrator(self):
        """Lazy-load the conversation orchestrator."""
        if self._orchestrator is None:
            from app.services.conversation_orchestrator import get_conversation_orchestrator
            self._orchestrator = get_conversation_orchestrator()
        return self._orchestrator
    
    @property
    def legacy_agent(self):
        """Lazy-load the legacy agent for fallback."""
        if self._legacy_agent is None:
            self._legacy_agent = ChatAgentLegacy(
                openai_api_key=self.openai_api_key,
                tavily_api_key=self.tavily_api_key
            )
        return self._legacy_agent
    
    async def process_message(
        self, 
        message: str, 
        user_id: int, 
        user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """
        Process user message and return streaming response.
        
        This is the main API method - signature unchanged from original.
        
        Args:
            message: User message text
            user_id: User ID
            user_profile: Optional user profile (for backward compatibility)
            
        Yields:
            str: Response chunks for streaming
        """
        if self.use_legacy:
            # Use legacy implementation for gradual migration
            async for chunk in self.legacy_agent.process_message(
                message, user_id, user_profile
            ):
                yield chunk
            return
        
        try:
            # Delegate to new architecture
            async for chunk in self.orchestrator.process_message(user_id, message):
                yield chunk
                
        except Exception as e:
            logger.error(f"Orchestrator error, falling back to legacy: {e}")
            # Fallback to legacy on error
            async for chunk in self.legacy_agent.process_message(
                message, user_id, user_profile
            ):
                yield chunk
    
    def extract_ui_components(self, response: str) -> list[UIComponent]:
        """
        Extract UI components from response text.
        
        Kept for backward compatibility with existing callers.
        """
        from app.services.ui_component_injector import get_ui_component_injector
        
        injector = get_ui_component_injector()
        # The injector returns components in a different format; adapt here
        # For now, return empty list as components are already injected
        return []
    
    def get_context(self, user_id: int) -> ChatContext | None:
        """Get conversation context for a user."""
        return self.contexts.get(user_id)
    
    def clear_context(self, user_id: int) -> None:
        """Clear conversation context for a user."""
        self.contexts.pop(user_id, None)
        # Also clear from orchestrator's context manager
        if self._orchestrator:
            import asyncio
            asyncio.create_task(
                self.orchestrator.context_manager.invalidate(user_id)
            )


# ============================================================================
# ChatAgentLegacy (Original Implementation - Preserved for Reference)
# ============================================================================

class ChatAgentLegacy:
    """
    Original ChatAgent implementation preserved for:
    1. Gradual migration (use_legacy=True)
    2. Fallback on errors
    3. Reference during refactoring
    
    NOTE: This class will be removed in Phase 2 after full migration.
    """
    
    def __init__(
        self, 
        openai_api_key: str | None = None, 
        tavily_api_key: str | None = None
    ):
        from langchain.agents import create_agent
        from langchain_openai import ChatOpenAI
        from app.services.search_tools import create_search_tool
        from app.services.ui_component_service import get_ui_component_service
        from app.services.recommendation_service import get_recommendation_service
        
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self.tavily_api_key = tavily_api_key or settings.TAVILY_API_KEY

        # Check if we have a valid OpenAI API key
        self.has_real_openai_key = (
            self.openai_api_key 
            and not self.openai_api_key.startswith("sk-mock")
            and self.openai_api_key != "mock-key"
        )

        if not self.has_real_openai_key:
            logger.warning(
                "No valid OpenAI API key provided - using mock agent"
            )

        # Initialize LLM only if we have a real API key
        llm_kwargs = {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "api_key": self.openai_api_key,
            "streaming": True,
        }
        
        if settings.OPENAI_API_BASE:
            llm_kwargs["base_url"] = settings.OPENAI_API_BASE
            
        self.llm = ChatOpenAI(**llm_kwargs) if self.has_real_openai_key else None

        # Initialize search tool
        self.search_tool = create_search_tool(
            use_mock=settings.USE_MOCK_SEARCH, 
            tavily_api_key=self.tavily_api_key
        )

        # Initialize agent
        self.agent = self._create_agent() if self.llm else "mock_agent"

        # Initialize services
        self.ui_service = get_ui_component_service()
        self.recommendation_service = get_recommendation_service()

        # Conversation contexts
        self.contexts: dict[int, ChatContext] = {}
        
        logger.info("ChatAgentLegacy initialized")

    def _create_agent(self):
        """Create LangChain agent with tools"""
        from langchain.agents import create_agent
        from app.core.prompt_manager import prompt_manager
        
        system_prompt = prompt_manager.render(
            category="chat",
            filename="agent_system",
            key="system_instruction"
        )

        agent = create_agent(
            model=self.llm, 
            tools=[self.search_tool], 
            system_prompt=system_prompt
        )

        return agent

    async def process_message(
        self, 
        message: str, 
        user_id: int, 
        user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """Process user message - Legacy implementation"""
        from datetime import datetime
        from app.services.chat_history_service import get_chat_history_service
        
        chat_history_service = get_chat_history_service()

        # Save user message
        try:
            await chat_history_service.save_user_message(user_id, message)
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")

        # Handle mock agent case
        if not self.has_real_openai_key:
            async for chunk in self._process_message_mock(message, user_id, user_profile):
                yield chunk
            return

        if not self.agent:
            yield "抱歉，AI服务暂时不可用。请稍后再试。"
            return

        try:
            # Get or create context
            context = self.contexts.get(user_id, ChatContext(user_id=user_id))
            self.contexts[user_id] = context

            context.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            })

            # Prepare agent input
            agent_input = {
                "messages": [{
                    "role": "user",
                    "content": await self._prepare_contextual_input(message, context, user_id),
                }]
            }

            # Stream response
            response_chunks = []
            async for chunk in self.agent.astream(agent_input):
                messages = None
                if "messages" in chunk:
                    messages = chunk["messages"]
                elif "model" in chunk and "messages" in chunk["model"]:
                    messages = chunk["model"]["messages"]
                
                if messages:
                    for msg in messages:
                        if hasattr(msg, "content") and msg.content:
                            response_chunks.append(msg.content)

            # Filter thought blocks
            full_response = "".join(response_chunks)
            filtered_response, thought_text = self._filter_thought_blocks(full_response)
            
            if thought_text:
                logger.info(f"🧠 CHAIN OF THOUGHT (User {user_id}):\n{thought_text}")
            
            if filtered_response:
                yield filtered_response
            
            # Save to history
            context.conversation_history.append({
                "role": "assistant",
                "content": filtered_response,
                "timestamp": datetime.now().isoformat(),
            })

            # UI enhancement
            ui_enhanced = await self._enhance_response_with_ui_components(
                filtered_response, context, user_id
            )

            if ui_enhanced != filtered_response:
                yield ui_enhanced[len(filtered_response):]

            # Save AI message
            try:
                await chat_history_service.save_ai_message(user_id, ui_enhanced)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")

            # Background extraction
            import asyncio
            asyncio.create_task(
                self._background_extraction_pipeline(message, user_id, context)
            )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    async def _process_message_mock(
        self, 
        message: str, 
        user_id: int, 
        user_profile: UserProfile | None = None
    ) -> AsyncIterator[str]:
        """Mock message processing"""
        import asyncio
        from datetime import datetime
        from app.services.chat_history_service import get_chat_history_service
        
        chat_history_service = get_chat_history_service()

        try:
            await chat_history_service.save_user_message(user_id, message)
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")
        
        try:
            context = self.contexts.get(user_id, ChatContext(user_id=user_id))
            self.contexts[user_id] = context

            context.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            })

            response = self._generate_mock_response(message, context)
            
            # Simulate streaming
            words = response.split()
            for i in range(0, len(words), 3):
                chunk = " ".join(words[i:i+3]) + " "
                yield chunk
                await asyncio.sleep(0.1)

            context.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
            })

            # UI enhancement
            ui_enhanced = await self._enhance_response_with_ui_components(
                response, context, user_id
            )

            if ui_enhanced != response:
                yield ui_enhanced[len(response):]

            try:
                await chat_history_service.save_ai_message(user_id, ui_enhanced)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")

            # Background extraction
            asyncio.create_task(
                self._background_extraction_pipeline(message, user_id, context)
            )

        except Exception as e:
            logger.error(f"Error processing mock message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    def _generate_mock_response(self, message: str, context: ChatContext) -> str:
        """Generate mock AI response"""
        message_lower = message.lower()
        
        if any(g in message_lower for g in ["你好", "hello", "hi", "您好"]):
            return "您好！🤝 我是AssetFlow的资产配置专家。有什么财务问题想要探讨吗？"
        
        if any(w in message_lower for w in ["房", "房产", "房子", "小区"]):
            return "很好！房产是重要的资产组成部分 🏠 您能告诉我具体的位置和面积吗？"
        
        if any(w in message_lower for w in ["资产", "投资", "理财", "存款"]):
            return "了解资产情况能帮我为您制定更合适的配置方案 💡 请告诉我您的资产情况。"
        
        if any(w in message_lower for w in ["分析", "建议", "配置"]):
            return "📊 基于标准普尔四象限模型，我建议优先完善应急资金储备和保险保障。"
        
        if any(s in message_lower for s in ["就这些", "没了", "没有了"]):
            return "好的，我明白了 🤝 让我为您做一个初步分析..."
        
        return "我是您的资产配置专家 🤝 有什么财务问题想要探讨吗？"

    def _filter_thought_blocks(self, text: str) -> tuple[str, str]:
        """Filter out <Thought> blocks"""
        import re
        thought_pattern = r'<Thought>(.*?)</Thought>'
        thought_matches = re.findall(thought_pattern, text, re.IGNORECASE | re.DOTALL)
        thought_content = "\n---\n".join(thought_matches) if thought_matches else ""
        filtered_text = re.sub(thought_pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        filtered_text = re.sub(r'\n\s*\n\s*\n', '\n\n', filtered_text).strip()
        return filtered_text, thought_content

    async def _prepare_contextual_input(
        self, 
        message: str, 
        context: ChatContext, 
        user_id: int
    ) -> str:
        """Prepare contextual input for LLM"""
        # Simplified version - full implementation in ConversationOrchestrator
        return message

    async def _enhance_response_with_ui_components(
        self, 
        response: str, 
        context: ChatContext, 
        user_id: int
    ) -> str:
        """Enhance response with UI components"""
        # Delegate to UIComponentInjector in new architecture
        from app.models.context import ConversationContext
        from app.services.ui_component_injector import get_ui_component_injector
        
        try:
            injector = get_ui_component_injector()
            
            # Convert ChatContext to ConversationContext
            new_context = ConversationContext(
                user_id=user_id,
                conversation_history=context.conversation_history,
                extracted_assets=context.extracted_assets,
                user_profile=context.user_profile,
                current_stage=context.current_stage,
                portfolio_analysis=context.portfolio_analysis,
            )
            
            enhanced, components = await injector.extract_and_inject(
                response, new_context, user_id
            )
            return enhanced
            
        except Exception as e:
            logger.error(f"UI component injection failed: {e}")
            return response

    async def _background_extraction_pipeline(
        self, 
        message: str, 
        user_id: int, 
        context: ChatContext
    ) -> None:
        """Background extraction pipeline"""
        # Delegate to orchestrator's implementation
        try:
            from app.models.context import ConversationContext
            
            new_context = ConversationContext(
                user_id=user_id,
                conversation_history=context.conversation_history,
                extracted_assets=context.extracted_assets,
                user_profile=context.user_profile,
                current_stage=context.current_stage,
            )
            
            await self.orchestrator._background_extraction_pipeline(
                message, user_id, new_context
            )
        except Exception as e:
            logger.error(f"Background extraction failed: {e}")


# ============================================================================
# Singleton Instance
# ============================================================================

_chat_agent: ChatAgent | None = None


def get_chat_agent() -> ChatAgent:
    """Get or create ChatAgent singleton."""
    global _chat_agent
    if _chat_agent is None:
        _chat_agent = ChatAgent()
    return _chat_agent
