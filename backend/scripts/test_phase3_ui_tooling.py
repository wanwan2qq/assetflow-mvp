import asyncio
import sys
import os
from unittest.mock import MagicMock

# Ensure app modules can be imported
sys.path.append(os.getcwd())

from app.services.llm_caller import MockLLMProvider
from app.models.context import ConversationContext

# --- SETUP MOCKS BEFORE IMPORTS ---

# 1. Intent Classifier Mock
mock_intent_module = MagicMock()
mock_classifier = MagicMock()
# Mock classify method
async def async_classify(*args, **kwargs):
    result = MagicMock()
    result.intent_type = "general" # Use attribute access
    result.confidence = 0.9
    result.model_dump.return_value = {"intent": "general"}
    return result
mock_classifier.classify = async_classify
# Mock factory
mock_intent_module.get_intent_classifier.return_value = mock_classifier
sys.modules['app.services.intent_classifier'] = mock_intent_module

# 2. Memory Service Mock
mock_memory_module = MagicMock()
mock_memory_service = MagicMock()
async def async_retrieve(*args, **kwargs): return []
mock_memory_service.retrieve_relevant = async_retrieve
mock_memory_module.get_memory_service.return_value = mock_memory_service
sys.modules['app.services.memory_service'] = mock_memory_module

# 3. Chat History Service Mock
mock_history_module = MagicMock()
mock_history_service = MagicMock()
async def async_save(*args, **kwargs): pass
mock_history_service.save_user_message = async_save
mock_history_service.save_ai_message = async_save
mock_history_module.get_chat_history_service.return_value = mock_history_service
sys.modules['app.services.chat_history_service'] = mock_history_module

# 4. Action Reasoner Mock (used in background pipeline)
mock_action_module = MagicMock()
sys.modules['app.services.action_reasoner'] = mock_action_module

# 5. Information Extraction Mock
mock_info_module = MagicMock()
sys.modules['app.services.information_extraction'] = mock_info_module

# 6. Asset Extraction Service Mock
mock_asset_module = MagicMock()
sys.modules['app.services.asset_extraction_service'] = mock_asset_module

# 7. Insight Service Mock
mock_insight_module = MagicMock()
sys.modules['app.services.insight_service'] = mock_insight_module

# 8. RAG Engine (used in process_message)
mock_rag_module = MagicMock()
sys.modules['app.services.rag_engine'] = mock_rag_module


# Now import Orchestrator
try:
    from app.services.conversation_orchestrator import ConversationOrchestrator
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

# Mock Context Manager
class MockContextManager:
    async def get_context(self, user_id):
        ctx = ConversationContext(user_id=user_id, conversation_history=[])
        # Inject asset relevant for Valuation Tool
        ctx.extracted_assets = [{
            "id": 1,
            "name": "My House",
            "type": "real_estate",
            "value": 5000000,
            "extra_data": {"area": 100, "location": "Shanghai"},
            "is_confirmed": True
        }]
        return ctx

    def update_in_memory(self, user_id, context):
        pass
    
    async def invalidate(self, user_id):
        pass

async def main():
    print("🚀 Starting Phase 3 UI Tooling Verification...")
    
    # Initialize
    llm_provider = MockLLMProvider()
    context_manager = MockContextManager()
    orchestrator = ConversationOrchestrator(llm_provider, context_manager)
    
    # Test Message triggering the mock tool
    user_id = 1
    test_message = "test_tool_valuation" 
    
    print(f"\n📨 Sending message: {test_message}")
    
    response_chunks = []
    try:
        async for chunk in orchestrator.process_message(user_id, test_message):
            response_chunks.append(chunk)
            # print(f"  Chunk: {chunk}") 
            # Commented out verbose chunk logging to reduce noise
            
        full_response = "".join(response_chunks)
        print(f"\n✅ Full Response (Length {len(full_response)}):\n{full_response}")
        
        # Verify Widget Tag logic
        if '<WIDGET:VALUATION_CARD' in full_response:
            print("\n🎉 SUCCESS: Valuation Widget detected!")
            if 'data="' in full_response:
                print("   Data attribute present.")
                # Optional: Parse data to verify asset_id=1
            else:
                 print("   ⚠️ Data attribute missing?")
        else:
            print("\n❌ FAILED: Valuation Widget NOT detected.")
            print("Debug: UI Injector might have failed or Tool Call wasn't processed.")
            
    except Exception as e:
        print(f"\n❌ FAILED with Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
