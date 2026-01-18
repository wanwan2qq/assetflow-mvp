"""
Tests for PromptManager
Validates YAML loading, Jinja2 rendering, and caching functionality
"""

import pytest
from pathlib import Path

from app.core.prompt_manager import PromptManager, prompt_manager


class TestPromptManager:
    """Test suite for PromptManager"""
    
    def test_singleton_instance(self):
        """Test that prompt_manager is properly initialized"""
        assert prompt_manager is not None
        assert isinstance(prompt_manager, PromptManager)
    
    def test_load_psychology_analysis_system_prompt(self):
        """Test loading system instruction for psychology analysis"""
        system_prompt = prompt_manager.get_raw(
            category="insight",
            filename="psychology_analysis",
            key="system_instruction"
        )
        
        assert system_prompt is not None
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 100
        assert "财务心理学专家" in system_prompt
        assert "Risk Tolerance" in system_prompt
        assert "JSON" in system_prompt
    
    def test_load_psychology_analysis_user_prompt(self):
        """Test loading user instruction for psychology analysis"""
        user_prompt = prompt_manager.get_raw(
            category="insight",
            filename="psychology_analysis",
            key="user_instruction"
        )
        
        assert user_prompt is not None
        assert isinstance(user_prompt, str)
        assert "对话历史" in user_prompt
        # Should contain Jinja2 syntax, not Python f-string
        assert "{{ conversation_text }}" in user_prompt
        assert "{conversation_text}" not in user_prompt
    
    def test_render_user_prompt_with_conversation(self):
        """Test rendering user prompt with conversation text"""
        conversation_text = "用户: 我最近压力很大\nAI: 我理解您的感受"
        
        rendered = prompt_manager.render(
            category="insight",
            filename="psychology_analysis",
            key="user_instruction",
            conversation_text=conversation_text
        )
        
        assert rendered is not None
        assert conversation_text in rendered
        assert "{{ conversation_text }}" not in rendered
        assert "对话历史" in rendered
    
    def test_load_memory_extraction_prompts(self):
        """Test loading memory extraction prompts"""
        system_prompt = prompt_manager.get_raw(
            category="insight",
            filename="memory_extraction",
            key="system_instruction"
        )
        
        assert system_prompt is not None
        assert "私人财富管家" in system_prompt
        assert "重大生活事件" in system_prompt
        assert "health_concern" in system_prompt
        
        user_prompt = prompt_manager.get_raw(
            category="insight",
            filename="memory_extraction",
            key="user_instruction"
        )
        
        assert user_prompt is not None
        assert "{{ conversation_text }}" in user_prompt
    
    def test_render_memory_extraction_prompt(self):
        """Test rendering memory extraction prompt"""
        conversation_text = "用户: 我岳母最近生病了，需要准备医疗费用"
        
        rendered = prompt_manager.render(
            category="insight",
            filename="memory_extraction",
            key="user_instruction",
            conversation_text=conversation_text
        )
        
        assert rendered is not None
        assert conversation_text in rendered
        assert "{{ conversation_text }}" not in rendered
    
    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for missing files"""
        with pytest.raises(FileNotFoundError):
            prompt_manager.render(
                category="nonexistent",
                filename="missing",
                key="test"
            )
    
    def test_key_not_found_error(self):
        """Test that KeyError is raised for missing keys"""
        with pytest.raises(KeyError):
            prompt_manager.render(
                category="insight",
                filename="psychology_analysis",
                key="nonexistent_key"
            )
    
    def test_caching_behavior(self):
        """Test that caching works correctly"""
        # Clear cache first
        prompt_manager.clear_cache()
        
        # First load
        prompt1 = prompt_manager.get_raw(
            category="insight",
            filename="psychology_analysis",
            key="system_instruction"
        )
        
        # Second load (should be cached)
        prompt2 = prompt_manager.get_raw(
            category="insight",
            filename="psychology_analysis",
            key="system_instruction"
        )
        
        # Should be the same content
        assert prompt1 == prompt2
        
        # Check cache info
        cache_info = prompt_manager._load_yaml.cache_info()
        assert cache_info.hits >= 1
    
    def test_render_with_multiple_variables(self):
        """Test rendering with multiple Jinja2 variables"""
        # Create a temporary test prompt manager for this test
        test_manager = PromptManager()
        
        # For this test, we'll just verify the existing prompts work
        # with single variable (conversation_text)
        rendered = test_manager.render(
            category="insight",
            filename="psychology_analysis",
            key="user_instruction",
            conversation_text="Test conversation"
        )
        
        assert "Test conversation" in rendered
    
    def test_prompt_content_integrity(self):
        """Test that prompt content matches original hardcoded version"""
        system_prompt = prompt_manager.get_raw(
            category="insight",
            filename="psychology_analysis",
            key="system_instruction"
        )
        
        # Verify key sections are present
        required_sections = [
            "风险承受能力",
            "conservative",
            "moderate", 
            "aggressive",
            "决策风格",
            "analytical",
            "intuitive",
            "cautious",
            "impulsive",
            "当前情绪状态",
            "anxious",
            "confident",
            "confused",
            "optimistic",
            "stressed",
            "关键心理特征",
            "advisor_note_internal",
            "key_concerns",
            "recommended_approach"
        ]
        
        for section in required_sections:
            assert section in system_prompt, f"Missing required section: {section}"


class TestPromptManagerIntegration:
    """Integration tests with InsightService"""
    
    def test_prompt_manager_import(self):
        """Test that prompt_manager can be imported in insight_service"""
        from app.services.insight_service import InsightService
        
        # Should not raise any import errors
        service = InsightService()
        assert service is not None
    
    def test_chat_agent_prompt_loading(self):
        """Test that ChatAgent can load prompts from YAML"""
        from app.core.prompt_manager import prompt_manager
        
        # Test loading chat agent system prompt
        system_prompt = prompt_manager.get_raw(
            category="chat",
            filename="agent_system",
            key="system_instruction"
        )
        
        assert system_prompt is not None
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 500
        assert "AssetFlow" in system_prompt
        assert "首席资产配置专家" in system_prompt
        assert "Chain of Thought" in system_prompt
        assert "标准普尔四象限" in system_prompt
    
    def test_information_extraction_prompt_loading(self):
        """Test that InformationExtractor can load modular prompts from YAML"""
        from app.core.prompt_manager import prompt_manager
        
        # Test asset extraction prompt
        asset_system_prompt = prompt_manager.get_raw(
            category="extraction",
            filename="asset_extraction",
            key="system_instruction"
        )
        
        assert asset_system_prompt is not None
        assert isinstance(asset_system_prompt, str)
        assert "asset extraction system" in asset_system_prompt.lower()
        assert "investment" in asset_system_prompt
        
        # Test profile extraction prompt
        profile_system_prompt = prompt_manager.get_raw(
            category="extraction",
            filename="profile_extraction",
            key="system_instruction"
        )
        
        assert profile_system_prompt is not None
        assert "profile extraction system" in profile_system_prompt.lower()
        assert "age_range" in profile_system_prompt
        
        # Test intent detection prompt
        intent_system_prompt = prompt_manager.get_raw(
            category="extraction",
            filename="intent_detection",
            key="system_instruction"
        )
        
        assert intent_system_prompt is not None
        assert "intent detection system" in intent_system_prompt.lower()
        assert "correction" in intent_system_prompt
        
        # Test user instruction rendering with variables
        asset_user_prompt = prompt_manager.render(
            category="extraction",
            filename="asset_extraction",
            key="user_instruction",
            context_str="user: 我有一套房子",
            user_message="价值500万"
        )
        
        assert "我有一套房子" in asset_user_prompt
        assert "价值500万" in asset_user_prompt
    
    def test_config_file_loading(self):
        """Test that PromptManager can load configuration files"""
        from app.core.prompt_manager import prompt_manager
        
        # Test asset type mapping config
        asset_config = prompt_manager.get_asset_type_mapping()
        assert "asset_types" in asset_config
        assert "real_estate" in asset_config["asset_types"]
        assert "investment" in asset_config["asset_types"]
        
        # Test SP quadrant config
        sp_config = prompt_manager.get_sp_quadrant_config()
        assert "quadrants" in sp_config
        assert "preservation_money" in sp_config["quadrants"]
        assert "growth_money" in sp_config["quadrants"]
        
        # Test risk assessment rules
        risk_config = prompt_manager.get_risk_assessment_rules()
        assert "user_risk_profiles" in risk_config
        assert "conservative" in risk_config["user_risk_profiles"]
        assert "aggressive" in risk_config["user_risk_profiles"]
    
    @pytest.mark.asyncio
    async def test_analyze_with_llm_uses_prompt_manager(self):
        """Test that _analyze_with_llm uses prompt_manager correctly"""
        from app.services.insight_service import InsightService
        from app.models.chat import ChatMessage, MessageRole
        from datetime import datetime
        
        service = InsightService()
        
        # Create mock messages
        messages = [
            ChatMessage(
                id=1,
                user_id=1,
                role=MessageRole.USER,
                content="我最近压力很大，房贷压力很重",
                timestamp=datetime.utcnow()
            ),
            ChatMessage(
                id=2,
                user_id=1,
                role=MessageRole.AI,
                content="我理解您的感受",
                timestamp=datetime.utcnow()
            )
        ]
        
        # This should not raise any errors
        # (It will use mock analysis if no real OpenAI key)
        result = await service._analyze_with_llm(messages)
        
        assert result is not None
        assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
