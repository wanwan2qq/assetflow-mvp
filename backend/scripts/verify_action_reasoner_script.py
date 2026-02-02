
import asyncio
import sys
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_verification():
    logger.info("Starting ActionReasoner verification...")
    
    try:
        from app.services.action_reasoner import ActionReasoner
        from app.models.user import User, UserAsset, UserProfile
        from app.models.action_plan import ActionPlan
        
        # Mock dependencies
        mock_db_session = AsyncMock()
        mock_db_session.add = MagicMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        mock_db_session.execute = AsyncMock()
        
        # Mock LLM
        mock_llm = AsyncMock()
        mock_llm.generate_stream = MagicMock()
        async def mock_stream(*args, **kwargs):
             yield '{"title": "Test Plan", "category": "wealth_growth", "steps": []}'
        mock_llm.generate_stream.side_effect = mock_stream

        # Mock RAG
        mock_rag = AsyncMock()
        mock_rag.query.return_value = MagicMock(answer="Mock Answer")

        # Mock Settings
        mock_settings = MagicMock()
        mock_settings.ENABLE_ACTION_REASONER = True

        async def mock_get_session_gen():
            yield mock_db_session

        # Patch everything
        with patch("app.services.action_reasoner.get_db_session", return_value=mock_get_session_gen()), \
             patch("app.core.dependencies.get_llm_provider", return_value=mock_llm), \
             patch("app.services.rag_engine.get_rag_engine", return_value=mock_rag), \
             patch("app.services.action_reasoner.get_settings", return_value=mock_settings):
             
             reasoner = ActionReasoner()
             logger.info("ActionReasoner instantiated.")
             
             # Test generate_plan (partial flow, mocking internal calls if needed)
             # To fully test generate_plan, we need to mock _load_user_context etc or mock DB returns.
             # Mocking _load_user_context is easier.
             
             mock_context = {
                 "user_id": 1,
                 "profile": {"family_structure": "married"},
                 "assets": [],
                 "total_assets": 0
             }
             
             # Mock methods to isolate logic
             reasoner._load_user_context = AsyncMock(return_value=mock_context)
             reasoner.analyze_gaps = AsyncMock(return_value={"insurance_gap": []})
             reasoner._save_plan = AsyncMock(return_value=ActionPlan(title="Saved Plan"))
             
             logger.info("Calling generate_plan...")
             plans, status = await reasoner.generate_plan(1)
             
             if plans and status == "generated":
                 logger.info("✅ generate_plan success!")
             else:
                 logger.error(f"❌ generate_plan failed: plans={plans}, status={status}")
                 sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_verification())
