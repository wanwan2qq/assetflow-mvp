"""
LLM Caller Module - Abstraction layer for LLM providers

This module provides:
1. LLMProvider abstract interface for dependency injection
2. DeepSeekProvider for production use
3. MockLLMProvider for development/testing

AI Coding Guidance:
- All LLM API calls should go through this module
- Mock logic is ONLY in MockLLMProvider, not in production code
- <Thought> block filtering is centralized in _filter_thought_blocks()
"""

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """
    Abstract interface for LLM providers.
    
    This enables dependency injection and easy swapping between
    real LLM (DeepSeek) and mock implementations.
    
    Usage:
        provider = get_llm_provider()  # From dependencies.py
        async for chunk in provider.generate_stream(messages, system_prompt):
            print(chunk)
    """
    
    @abstractmethod
    async def generate_stream(
        self, 
        messages: list[dict[str, str]], 
        system_prompt: str
    ) -> AsyncIterator[str]:
        """
        Generate streaming response from LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System instruction for the LLM
            
        Yields:
            str: Response chunks (already filtered for <Thought> blocks)
        """
        pass
    
    @abstractmethod
    async def generate(
        self, 
        messages: list[dict[str, str]], 
        system_prompt: str
    ) -> str:
        """
        Generate complete response from LLM (non-streaming).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System instruction for the LLM
            
        Returns:
            str: Complete response (already filtered for <Thought> blocks)
        """
        pass
    
    def _filter_thought_blocks(self, text: str) -> tuple[str, str]:
        """
        Filter out <Thought> blocks from AI response.
        
        Returns:
            tuple: (filtered_text, thought_content)
                - filtered_text: Response without <Thought> blocks (shown to user)
                - thought_content: Extracted thought content (for logging)
        """
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


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek LLM provider for production use.
    
    Uses LangChain's ChatOpenAI with DeepSeek-compatible configuration.
    """
    
    def __init__(self, api_key: str, base_url: str | None = None):
        """
        Initialize DeepSeek provider.
        
        Args:
            api_key: DeepSeek API key
            base_url: Optional custom API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        
        llm_kwargs = {
            "model": "deepseek-chat",
            "temperature": 0.7,
            "api_key": api_key,
            "streaming": True,
        }
        
        if base_url:
            llm_kwargs["base_url"] = base_url
            
        self.llm = ChatOpenAI(**llm_kwargs)
        logger.info("✅ DeepSeekProvider initialized")
    
    async def generate_stream(
        self, 
        messages: list[dict[str, str]], 
        system_prompt: str
    ) -> AsyncIterator[str]:
        """Generate streaming response using DeepSeek."""
        try:
            # Build full message list with system prompt
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            # Collect all chunks first to filter thought blocks
            response_chunks = []
            
            async for chunk in self.llm.astream(full_messages):
                if hasattr(chunk, "content") and chunk.content:
                    response_chunks.append(chunk.content)
            
            # Filter thought blocks from complete response
            full_response = "".join(response_chunks)
            filtered_response, thought_content = self._filter_thought_blocks(full_response)
            
            # Log thought content for debugging
            if thought_content:
                logger.info(f"🧠 CHAIN OF THOUGHT:\n{thought_content}")
            
            # Yield filtered response
            if filtered_response:
                yield filtered_response
                
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            yield f"抱歉，AI服务暂时不可用：{str(e)}"
    
    async def generate(
        self, 
        messages: list[dict[str, str]], 
        system_prompt: str
    ) -> str:
        """Generate complete response using DeepSeek."""
        try:
            full_messages = [{"role": "system", "content": system_prompt}] + messages
            
            response = await self.llm.ainvoke(full_messages)
            
            if hasattr(response, "content"):
                filtered_response, thought_content = self._filter_thought_blocks(response.content)
                
                if thought_content:
                    logger.info(f"🧠 CHAIN OF THOUGHT:\n{thought_content}")
                    
                return filtered_response
            
            return ""
            
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return f"抱歉，AI服务暂时不可用：{str(e)}"


class MockLLMProvider(LLMProvider):
    """
    Mock LLM provider for development and testing.
    
    All mock response logic is centralized here, keeping production code clean.
    """
    
    def __init__(self):
        logger.warning("⚠️ MockLLMProvider initialized - using mock responses")
    
    async def generate_stream(
        self, 
        messages: list[dict[str, str]], 
        system_prompt: str
    ) -> AsyncIterator[str]:
        """Generate mock streaming response."""
        # Get the last user message
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # Generate mock response
        response = self._generate_mock_response(user_message)
        
        # Simulate streaming by yielding chunks
        words = response.split()
        for i in range(0, len(words), 3):  # Yield 3 words at a time
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.05)  # Small delay to simulate streaming
    
    async def generate(
        self, 
        messages: list[dict[str, str]], 
        system_prompt: str
    ) -> str:
        """Generate complete mock response."""
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        return self._generate_mock_response(user_message)
    
    def _generate_mock_response(self, message: str) -> str:
        """
        Generate mock AI response based on message content.
        
        This consolidates all mock logic from the original ChatAgent.
        """
        message_lower = message.lower()
        
        # Greeting responses
        if any(g in message_lower for g in ["你好", "hello", "hi", "您好"]):
            return "您好！🤝 我是AssetFlow的资产配置专家。有什么财务问题想要探讨吗？"
        
        # Property-related
        if any(w in message_lower for w in ["房", "房产", "房子", "小区"]):
            return "很好！房产是重要的资产组成部分 🏠 您能告诉我具体的位置和面积吗？"
        
        # Investment questions
        if any(w in message_lower for w in ["50万", "100万", "怎么投", "如何投资"]):
            return "💡 根据标准普尔四象限模型，建议：\n🔹 应急资金（10%）\n🔹 保险保障（20%）\n🔹 高收益投资（30%）\n🔹 稳健理财（40%）"
        
        # Asset-related
        if any(w in message_lower for w in ["资产", "投资", "理财", "存款"]):
            return "了解资产情况能帮我为您制定更合适的配置方案 💡 请告诉我您的资产情况。"
        
        # Analysis requests
        if any(w in message_lower for w in ["分析", "建议", "配置"]):
            return "📊 基于标准普尔四象限模型，我建议优先完善应急资金储备和保险保障。"
        
        # Completion signals
        if any(s in message_lower for s in ["就这些", "没了", "没有了"]):
            return "好的，我明白了 🤝 让我为您做一个初步分析..."
        
        # Default
        return "我是您的资产配置专家 🤝 有什么财务问题想要探讨吗？"
    
    def _safe_emoji_text(self, text: str) -> str:
        """Ensure emoji characters are safely encoded."""
        try:
            text.encode('utf-8').decode('utf-8')
            return text
        except UnicodeEncodeError:
            return text.encode('utf-8', errors='replace').decode('utf-8')
