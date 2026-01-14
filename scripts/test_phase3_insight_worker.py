"""
Test script for Phase 3: Cognitive Insight Worker
Tests psychological profiling and adaptive advisor behavior
"""

import asyncio
import logging
from datetime import datetime

from sqlmodel import select

from app.core.database import get_db_session
from app.models.chat import ChatMessage, MessageRole
from app.models.cognition import UserCognition
from app.models.user import User
from app.services.insight_service import get_insight_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_test_conversation(user_id: int) -> None:
    """Create a test conversation with emotional content"""
    
    test_messages = [
        ("你好，我想咨询一下资产配置", MessageRole.USER),
        ("您好！很高兴为您服务。请问您目前有房产吗？", MessageRole.AI),
        ("有的，我在北京有一套房，但是房贷压力很大，每个月要还2万多", MessageRole.USER),
        ("我理解高房贷确实会带来压力。让我帮您看看如何优化配置。", MessageRole.AI),
        ("我真的很担心，万一股市再崩盘怎么办？我2015年亏了很多钱", MessageRole.USER),
        ("我理解您的担忧。基于您的情况，我建议采用保守的配置策略。", MessageRole.AI),
        ("我手上还有50万现金，不知道该怎么投资，又怕亏损", MessageRole.USER),
        ("考虑到您的风险承受能力，建议优先配置稳健型产品。", MessageRole.AI),
    ]
    
    async for session in get_db_session():
        for content, role in test_messages:
            message = ChatMessage(
                user_id=user_id,
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
            session.add(message)
        
        await session.commit()
        logger.info(f"Created {len(test_messages)} test messages for user {user_id}")
        break


async def test_insight_analysis():
    """Test the insight analysis service"""
    
    logger.info("=" * 60)
    logger.info("Phase 3: Cognitive Insight Worker Test")
    logger.info("=" * 60)
    
    # Get test user
    async for session in get_db_session():
        statement = select(User).limit(1)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("No test user found. Please create a user first.")
            return
        
        user_id = user.id
        logger.info(f"Testing with user ID: {user_id}")
        break
    
    # Create test conversation
    logger.info("\n1. Creating test conversation with emotional content...")
    await create_test_conversation(user_id)
    
    # Run insight analysis
    logger.info("\n2. Running psychological analysis...")
    insight_service = get_insight_service()
    analysis = await insight_service.analyze_user_psychology(user_id)
    
    if analysis.get("error"):
        logger.error(f"Analysis failed: {analysis['error']}")
        return
    
    if analysis.get("skipped"):
        logger.warning(f"Analysis skipped: {analysis['reason']}")
        return
    
    # Display analysis results
    logger.info("\n3. Analysis Results:")
    logger.info("-" * 60)
    
    risk_profile = analysis.get("risk_profile", {})
    logger.info(f"Risk Tolerance: {risk_profile.get('tolerance', 'unknown')}")
    logger.info(f"Decision Style: {risk_profile.get('decision_style', 'unknown')}")
    logger.info(f"Confidence Level: {risk_profile.get('confidence_level', 'unknown')}")
    
    logger.info(f"\nCurrent Sentiment: {analysis.get('current_sentiment', 'unknown')}")
    
    psychological_traits = analysis.get("psychological_traits", {})
    logger.info("\nPsychological Traits:")
    for trait, value in psychological_traits.items():
        logger.info(f"  - {trait}: {value}")
    
    logger.info(f"\nAdvisor Note (Internal):")
    logger.info(f"  {analysis.get('advisor_note_internal', 'N/A')}")
    
    key_concerns = analysis.get("key_concerns", [])
    logger.info(f"\nKey Concerns: {', '.join(key_concerns)}")
    
    # Check database update
    logger.info("\n4. Verifying database update...")
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if cognition:
            logger.info("✅ UserCognition record updated successfully")
            logger.info(f"   Risk Profile: {cognition.risk_profile}")
            logger.info(f"   Advisor Note: {cognition.advisor_note[:100]}..." if cognition.advisor_note else "   Advisor Note: None")
        else:
            logger.error("❌ UserCognition record not found")
        break
    
    # Test advisor strategy retrieval
    logger.info("\n5. Testing advisor strategy retrieval...")
    advisor_note = await insight_service.get_advisor_strategy(user_id)
    if advisor_note:
        logger.info(f"✅ Advisor strategy retrieved: {advisor_note[:100]}...")
    else:
        logger.warning("⚠️  No advisor strategy found")
    
    logger.info("\n" + "=" * 60)
    logger.info("Test completed!")
    logger.info("=" * 60)


async def test_acceptance_criteria():
    """
    Test the acceptance criteria from requirements:
    1. User says: "I'm really scared of the stock market crashing again."
    2. Background Task: InsightService updates risk_profile -> "conservative"
    3. Next Turn: AI suggests "Bonds/Gold" instead of "Crypto/Stocks"
    """
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing Acceptance Criteria")
    logger.info("=" * 60)
    
    # Get test user
    async for session in get_db_session():
        statement = select(User).limit(1)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("No test user found")
            return
        
        user_id = user.id
        break
    
    # Step 1: User expresses fear
    logger.info("\n1. User says: '我真的很害怕股市再次崩盘，2015年亏惨了'")
    
    async for session in get_db_session():
        # Clear previous messages
        statement = select(ChatMessage).where(ChatMessage.user_id == user_id)
        result = await session.execute(statement)
        messages = result.scalars().all()
        for msg in messages:
            await session.delete(msg)
        await session.commit()
        
        # Add fear message
        fear_messages = [
            ("你好", MessageRole.USER),
            ("您好！", MessageRole.AI),
            ("我有100万想投资", MessageRole.USER),
            ("好的，请问您的风险偏好如何？", MessageRole.AI),
            ("我真的很害怕股市再次崩盘，2015年我亏了50万，现在想起来还心有余悸", MessageRole.USER),
            ("我理解您的担忧，那次经历确实让人印象深刻", MessageRole.AI),
        ]
        
        for content, role in fear_messages:
            message = ChatMessage(
                user_id=user_id,
                role=role,
                content=content,
                timestamp=datetime.utcnow()
            )
            session.add(message)
        
        await session.commit()
        break
    
    # Step 2: Run insight analysis
    logger.info("\n2. Running insight analysis (Background Task)...")
    insight_service = get_insight_service()
    analysis = await insight_service.analyze_user_psychology(user_id)
    
    if not analysis.get("error") and not analysis.get("skipped"):
        risk_tolerance = analysis.get("risk_profile", {}).get("tolerance")
        logger.info(f"   ✅ Risk profile updated: {risk_tolerance}")
        
        if risk_tolerance == "conservative":
            logger.info("   ✅ PASS: Risk profile correctly identified as 'conservative'")
        else:
            logger.warning(f"   ⚠️  UNEXPECTED: Risk profile is '{risk_tolerance}', expected 'conservative'")
    
    # Step 3: Check advisor note
    logger.info("\n3. Checking advisor strategy note...")
    advisor_note = await insight_service.get_advisor_strategy(user_id)
    
    if advisor_note:
        logger.info(f"   Advisor Note: {advisor_note}")
        
        # Check if note mentions conservative approach
        conservative_keywords = ["保守", "稳健", "保本", "低风险", "债券", "避免激进"]
        has_conservative_guidance = any(keyword in advisor_note for keyword in conservative_keywords)
        
        if has_conservative_guidance:
            logger.info("   ✅ PASS: Advisor note contains conservative guidance")
        else:
            logger.warning("   ⚠️  Advisor note may not emphasize conservative approach")
    else:
        logger.error("   ❌ FAIL: No advisor note generated")
    
    logger.info("\n4. Expected Behavior in Next Turn:")
    logger.info("   When user asks 'What should I buy?'")
    logger.info("   AI should suggest: Bonds, Bank Wealth Management, Gold")
    logger.info("   AI should avoid: Stocks, Crypto, High-risk investments")
    logger.info("   AI should use: Reassuring, empathetic tone")
    
    logger.info("\n" + "=" * 60)
    logger.info("Acceptance Criteria Test Completed")
    logger.info("=" * 60)


async def main():
    """Run all tests"""
    await test_insight_analysis()
    await test_acceptance_criteria()


if __name__ == "__main__":
    asyncio.run(main())
