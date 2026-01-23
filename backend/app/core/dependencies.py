"""
Dependency Injection Configuration for AssetFlow Backend

This module provides factory functions for obtaining service instances,
enabling easy swapping between real and mock implementations.
"""

from functools import lru_cache

from app.core.config import settings


@lru_cache()
def get_llm_provider():
    """
    Get LLM Provider instance (singleton).
    
    Returns MockLLMProvider if USE_MOCK_LLM is True or no valid API key,
    otherwise returns DeepSeekProvider.
    
    Usage:
        from app.core.dependencies import get_llm_provider
        
        llm = get_llm_provider()
        async for chunk in llm.generate_stream(messages, system_prompt):
            print(chunk)
    """
    from app.services.llm_caller import DeepSeekProvider, MockLLMProvider
    
    # Check if we should use mock
    use_mock = settings.USE_MOCK_LLM
    
    # Also check if API key is valid
    api_key = settings.OPENAI_API_KEY
    has_valid_key = (
        api_key 
        and not api_key.startswith("sk-mock")
        and api_key != "mock-key"
    )
    
    if use_mock or not has_valid_key:
        return MockLLMProvider()
    
    return DeepSeekProvider(
        api_key=api_key,
        base_url=settings.OPENAI_API_BASE
    )


def get_context_manager():
    """
    Get ContextManager singleton instance.
    
    Returns a ContextManager that handles user conversation context,
    including caching (Redis or in-memory) and database persistence.
    """
    from app.services.context_manager import get_context_manager as _get_context_manager
    return _get_context_manager()


def get_conversation_orchestrator():
    """
    Get ConversationOrchestrator instance.
    
    This is the main entry point for processing chat messages.
    It coordinates LLM calls, context management, and UI component injection.
    """
    from app.services.conversation_orchestrator import ConversationOrchestrator
    
    llm_provider = get_llm_provider()
    context_manager = get_context_manager()
    
    return ConversationOrchestrator(
        llm_provider=llm_provider,
        context_manager=context_manager
    )
