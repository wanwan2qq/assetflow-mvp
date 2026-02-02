
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserAsset, UserProfile
from app.services.action_reasoner import ActionReasoner
from app.models.action_plan import ActionCategory, ActionPlan
from datetime import datetime

# Helper to mock get_db_session
async def mock_get_db_session_generator(session):
    yield session

@pytest.mark.asyncio
class TestActionReasoner:
    
    async def setup_user_data(self, session: AsyncSession):
        # Create user
        user = User(phone="13900139000", device_id="test_device")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            age_range="30-35",
            family_structure="married_with_kids",
            risk_preference="conservative",
            income_range="50万",
            monthly_expense=20000
        )
        session.add(profile)
        
        # Create assets (Cash < 6 months expense -> triggers emergency gap)
        # 6 months * 20000 = 120000. Cash = 50000. Gap should be 70000.
        asset1 = UserAsset(
            user_id=user.id,
            name="存款",
            asset_type="cash",
            value=50000,
            currency="CNY"
        )
        session.add(asset1)
        
        await session.commit()
        return user

    async def test_analyze_gaps(self, db_session: AsyncSession):
        """Test gap analysis logic"""
        # Setup
        with patch("app.services.action_reasoner.get_db_session", return_value=mock_get_db_session_generator(db_session)):
            reasoner = ActionReasoner()
            user = await self.setup_user_data(db_session)
            
            # Run analysis
            gaps = await reasoner.analyze_gaps(user.id)
            
            # Assertions
            # 1. Insurance Gap (missing life/health)
            assert any(g["type"] == "life_insurance" for g in gaps["insurance_gap"])
            
            # 2. Emergency Fund Gap
            # current=50000, recommended=120000 (20000*6)
            assert gaps["emergency_fund_gap"] is not None
            assert gaps["emergency_fund_gap"]["shortfall"] == 70000

    async def test_generate_plan_flow(self, db_session: AsyncSession):
        """Test full plan generation flow with mocked LLM"""
        # Setup
        user = await self.setup_user_data(db_session)
        
        # Mock LLM Provider
        mock_llm = AsyncMock()
        mock_plan_json = """
        {
            "title": "Test Plan",
            "category": "wealth_growth",
            "priority": "high",
            "summary": "This is a test plan",
            "steps": [{"action": "Buy Insurance", "step_number": 1}],
            "expected_benefits": ["Safety"],
            "potential_risks": ["Cost"],
            "confidence": 0.9
        }
        """
        # Mock generate_stream to yield chunks
        async def mock_stream(*args, **kwargs):
            yield mock_plan_json
        
        mock_llm.generate_stream = mock_stream
        
        # Mock dependencies
        with patch("app.services.action_reasoner.get_db_session", return_value=mock_get_db_session_generator(db_session)), \
             patch("app.core.dependencies.get_llm_provider", return_value=mock_llm) as mock_get_llm, \
             patch("app.services.rag_engine.get_rag_engine") as mock_get_rag:
             
            # Setup RAG mock
            mock_rag = AsyncMock()
            mock_rag.query.return_value = MagicMock(answer="Mock knowledge")
            mock_get_rag.return_value = mock_rag
            
            # Need to patch settings to enable action reasoner
            with patch("app.services.action_reasoner.get_settings") as mock_settings:
                mock_settings.return_value.ENABLE_ACTION_REASONER = True
                
                reasoner = ActionReasoner()
                plans, status = await reasoner.generate_plan(user.id, check_existing=False)
                
                assert len(plans) == 1
                assert status == "generated"
                plan = plans[0]
                assert plan.title == "Test Plan"
                assert plan.status == "pending"

    async def test_adopt_plan(self, db_session: AsyncSession):
        """Test accepting a plan creates steps"""
        # Setup
        user = await self.setup_user_data(db_session)
        plan = ActionPlan(
            user_id=user.id,
            title="Pending Plan",
            category="wealth_growth",
            priority="medium",
            status="pending",
            original_steps_snapshot=[
                {"step_number": 1, "action": "Step 1", "description": "Desc 1"},
                {"step_number": 2, "action": "Step 2", "description": "Desc 2"}
            ]
        )
        db_session.add(plan)
        await db_session.commit()
        await db_session.refresh(plan)
        
        with patch("app.services.action_reasoner.get_db_session", return_value=mock_get_db_session_generator(db_session)):
            reasoner = ActionReasoner()
            
            # Action
            updated_plan = await reasoner.adopt_plan(plan.id)
            
            # Assert
            assert updated_plan is not None
            assert updated_plan.status == "in_progress"
            assert updated_plan.adopted_at is not None
            
            # Check steps created
            # We need to refresh/load steps relation
            # update_plan loads steps_list by default in its logic?
            # existing code: options(selectinload(ActionPlan.steps_list))
            
            assert len(updated_plan.steps_list) == 2
            assert updated_plan.steps_list[0].action == "Step 1"
            assert updated_plan.steps_list[0].status == "pending"

