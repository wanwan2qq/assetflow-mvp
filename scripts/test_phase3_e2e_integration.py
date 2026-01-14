"""
Phase 3 End-to-End Integration Test
Tests the complete flow: User message → Insight analysis → Adaptive response
"""

import asyncio
import logging
from datetime import datetime

from sqlmodel import select

from app.core.database import get_db_session
from app.models.chat import ChatMessage, MessageRole
from app.models.cognition import UserCognition
from app.models.user import User
from app.services.chat_agent import get_chat_agent
from app.services.insight_service import get_insight_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_e2e_adaptive_behavior():
    """
    End-to-end test of adaptive advisor behavior
    
    Flow:
    1. User expresses fear about stock market
    2. Chat agent processes message
    3. Insight service analyzes psychology (background)
    4. Next message: User asks for investment advice
    5. Chat agent reads advisor note and adapts response
    """
    
    logger.info("=" * 70)
    logger.info("Phase 3 E2E Integration Test: Adaptive Advisor Behavior")
    logger.info("=" * 70)
    
    # Get test user
    async for session in get_db_session():
        statement = select(User).limit(1)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("No test user found")
            return
        
        user_id = user.id
        logger.info(f"Testing with user ID: {user_id}")
        break
    
    # Clear previous data
    logger.info("\n1. Clearing previous test data...")
    async for session in get_db_session():
        # Clear messages
        statement = select(ChatMessage).where(ChatMessage.user_id == user_id)
        result = await session.execute(statement)
        messages = result.scalars().all()
        for msg in messages:
            await session.delete(msg)
        
        # Clear cognition
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        if cognition:
            await session.delete(cognition)
        
        await session.commit()
        logger.info("   ✅ Test data cleared")
        break
    
    # Get chat agent
    chat_agent = get_chat_agent()
    
    # Turn 1-4: Build conversation context
    logger.info("\n2. Building conversation context (Turns 1-4)...")
    
    conversation = [
        "你好，我想咨询资产配置",
        "我在北京有一套房，价值500万，还有房贷200万",
        "我手上有100万现金想投资",
        "但是我真的很害怕，2015年股市崩盘时我亏了50万，现在想起来还心有余悸"
    ]
    
    for i, user_message in enumerate(conversation, 1):
        logger.info(f"   Turn {i}: User says: {user_message[:30]}...")
        
        # Process message through chat agent
        response_chunks = []
        async for chunk in chat_agent.process_message(user_message, user_id):
            response_chunks.append(chunk)
        
        full_response = "".join(response_chunks)
        logger.info(f"   Turn {i}: AI responds: {full_response[:50]}...")
    
    # Wait a moment for background processing
    await asyncio.sleep(1)
    
    # Check if insight analysis was triggered
    logger.info("\n3. Checking insight analysis results...")
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if cognition and cognition.advisor_note:
            logger.info("   ✅ Insight analysis completed")
            logger.info(f"   Risk Profile: {cognition.risk_profile.get('tolerance', 'unknown')}")
            logger.info(f"   Sentiment: {cognition.risk_profile.get('current_sentiment', 'unknown')}")
            logger.info(f"   Advisor Note: {cognition.advisor_note[:100]}...")
            
            # Verify conservative profile
            if cognition.risk_profile.get('tolerance') == 'conservative':
                logger.info("   ✅ PASS: Correctly identified as conservative")
            else:
                logger.warning(f"   ⚠️  Risk tolerance is {cognition.risk_profile.get('tolerance')}")
        else:
            logger.warning("   ⚠️  No insight analysis found (may need more messages)")
        break
    
    # Turn 5: Ask for investment advice (should get adaptive response)
    logger.info("\n4. Testing adaptive response (Turn 5)...")
    investment_question = "那我这100万应该怎么投资比较好？"
    logger.info(f"   User asks: {investment_question}")
    
    response_chunks = []
    async for chunk in chat_agent.process_message(investment_question, user_id):
        response_chunks.append(chunk)
    
    full_response = "".join(response_chunks)
    logger.info(f"\n   AI Response:\n   {full_response}\n")
    
    # Analyze response for adaptive behavior
    logger.info("5. Analyzing response for adaptive behavior...")
    
    # Check for conservative keywords
    conservative_keywords = ["稳健", "保本", "债券", "银行理财", "安全", "保守", "低风险"]
    found_conservative = [kw for kw in conservative_keywords if kw in full_response]
    
    # Check for aggressive keywords (should be avoided)
    aggressive_keywords = ["股票", "高收益", "激进", "加密货币", "高风险"]
    found_aggressive = [kw for kw in aggressive_keywords if kw in full_response]
    
    # Check for empathetic tone
    empathy_keywords = ["理解", "担心", "压力", "安心", "放心", "安全感"]
    found_empathy = [kw for kw in empathy_keywords if kw in full_response]
    
    logger.info("\n   Analysis Results:")
    logger.info(f"   Conservative keywords found: {found_conservative}")
    logger.info(f"   Aggressive keywords found: {found_aggressive}")
    logger.info(f"   Empathy keywords found: {found_empathy}")
    
    # Scoring
    score = 0
    if len(found_conservative) >= 2:
        logger.info("   ✅ PASS: Response contains conservative recommendations")
        score += 1
    else:
        logger.warning("   ⚠️  Response lacks conservative recommendations")
    
    if len(found_aggressive) == 0:
        logger.info("   ✅ PASS: Response avoids aggressive recommendations")
        score += 1
    else:
        logger.warning(f"   ⚠️  Response contains aggressive keywords: {found_aggressive}")
    
    if len(found_empathy) >= 1:
        logger.info("   ✅ PASS: Response shows empathy")
        score += 1
    else:
        logger.warning("   ⚠️  Response lacks empathetic tone")
    
    logger.info(f"\n   Overall Score: {score}/3")
    
    if score >= 2:
        logger.info("   ✅ TEST PASSED: Adaptive behavior is working!")
    else:
        logger.warning("   ⚠️  TEST NEEDS REVIEW: Adaptive behavior may need tuning")
    
    logger.info("\n" + "=" * 70)
    logger.info("E2E Integration Test Completed")
    logger.info("=" * 70)


async def test_context_injection():
    """
    Test that advisor note is properly injected into context
    """
    
    logger.info("\n" + "=" * 70)
    logger.info("Testing Context Injection")
    logger.info("=" * 70)
    
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
    
    # Manually create a cognition record with advisor note
    logger.info("\n1. Creating test cognition record...")
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if not cognition:
            cognition = UserCognition(user_id=user_id)
            session.add(cognition)
        
        cognition.risk_profile = {
            "tolerance": "conservative",
            "current_sentiment": "anxious"
        }
        cognition.advisor_note = "TEST NOTE: 用户极度保守，只推荐债券和银行理财。"
        cognition.updated_at = datetime.utcnow()
        
        await session.commit()
        logger.info("   ✅ Test cognition record created")
        break
    
    # Get chat agent and check context preparation
    logger.info("\n2. Testing context preparation...")
    chat_agent = get_chat_agent()
    
    # Get conversation context
    context = chat_agent.get_conversation_context(user_id)
    if not context:
        from app.services.chat_agent import ChatContext
        context = ChatContext(user_id=user_id)
        chat_agent.contexts[user_id] = context
    
    # Prepare contextual input
    test_message = "我该怎么投资？"
    contextual_input = await chat_agent._prepare_contextual_input(test_message, context, user_id)
    
    logger.info("\n   Contextual Input Preview:")
    logger.info("   " + "-" * 60)
    logger.info(f"   {contextual_input[:500]}...")
    logger.info("   " + "-" * 60)
    
    # Check if advisor note is included
    if "ADVISOR STRATEGY NOTE" in contextual_input:
        logger.info("\n   ✅ PASS: Advisor note is injected into context")
        
        if "TEST NOTE" in contextual_input:
            logger.info("   ✅ PASS: Correct advisor note content found")
        else:
            logger.warning("   ⚠️  Advisor note content may be incorrect")
    else:
        logger.error("   ❌ FAIL: Advisor note is NOT injected into context")
    
    logger.info("\n" + "=" * 70)
    logger.info("Context Injection Test Completed")
    logger.info("=" * 70)


async def main():
    """Run all E2E tests"""
    await test_context_injection()
    await test_e2e_adaptive_behavior()


if __name__ == "__main__":
    asyncio.run(main())
