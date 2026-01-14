"""
Phase 3: Cognitive Insight Worker - Final Verification Script

This script demonstrates the complete Phase 3 functionality:
1. User expresses emotional concerns
2. Insight service analyzes psychology
3. AI adapts its behavior based on insights
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

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str):
    """Print a formatted section header"""
    logger.info("\n" + "=" * 80)
    logger.info(f"  {title}")
    logger.info("=" * 80)


def print_subsection(title: str):
    """Print a formatted subsection header"""
    logger.info(f"\n{'─' * 80}")
    logger.info(f"  {title}")
    logger.info(f"{'─' * 80}")


async def demonstrate_phase3():
    """Demonstrate Phase 3 functionality"""
    
    print_section("Phase 3: Cognitive Insight Worker - Demonstration")
    
    # Get test user
    async for session in get_db_session():
        statement = select(User).limit(1)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.error("❌ No test user found. Please create a user first.")
            return
        
        user_id = user.id
        logger.info(f"\n✅ Using test user ID: {user_id}")
        break
    
    # Clear previous data
    print_subsection("Step 1: Preparing Test Environment")
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
        logger.info("✅ Test environment prepared (previous data cleared)")
        break
    
    # Scenario: User with stock market trauma
    print_subsection("Step 2: User Conversation (Building Context)")
    
    chat_agent = get_chat_agent()
    
    conversation = [
        {
            "user": "你好，我想咨询一下资产配置",
            "expected": "Initial greeting and information gathering"
        },
        {
            "user": "我在北京有一套房，市值大概500万，还有200万房贷",
            "expected": "Acknowledge property and ask about other assets"
        },
        {
            "user": "我手上还有100万现金，不知道该怎么投资",
            "expected": "Ask about risk preference or investment goals"
        },
        {
            "user": "说实话，我真的很害怕。2015年股市崩盘的时候，我亏了50万，那段时间每天都睡不着觉，现在想起来还心有余悸",
            "expected": "Show empathy and understanding"
        },
        {
            "user": "我现在就是不敢碰股票了，一看到股市的新闻就紧张",
            "expected": "Reassure and suggest conservative options"
        }
    ]
    
    for i, turn in enumerate(conversation, 1):
        logger.info(f"\n💬 Turn {i}:")
        logger.info(f"   User: {turn['user']}")
        
        # Process message
        response_chunks = []
        async for chunk in chat_agent.process_message(turn['user'], user_id):
            response_chunks.append(chunk)
        
        full_response = "".join(response_chunks)
        logger.info(f"   AI: {full_response[:150]}...")
        logger.info(f"   Expected: {turn['expected']}")
    
    # Wait for background processing
    logger.info("\n⏳ Waiting for background insight analysis...")
    await asyncio.sleep(2)
    
    # Check insight analysis results
    print_subsection("Step 3: Insight Analysis Results (System 2 Thinking)")
    
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if cognition and cognition.risk_profile and cognition.advisor_note:
            logger.info("\n✅ Psychological Analysis Completed:")
            logger.info(f"\n📊 Risk Profile:")
            logger.info(f"   • Tolerance: {cognition.risk_profile.get('tolerance', 'N/A')}")
            logger.info(f"   • Decision Style: {cognition.risk_profile.get('decision_style', 'N/A')}")
            logger.info(f"   • Confidence Level: {cognition.risk_profile.get('confidence_level', 'N/A')}")
            logger.info(f"   • Current Sentiment: {cognition.risk_profile.get('current_sentiment', 'N/A')}")
            
            logger.info(f"\n🧠 Psychological Traits:")
            logger.info(f"   • Loss Aversion: {cognition.risk_profile.get('loss_aversion', 'N/A')}")
            logger.info(f"   • Uncertainty Tolerance: {cognition.risk_profile.get('uncertainty_tolerance', 'N/A')}")
            logger.info(f"   • Financial Literacy: {cognition.risk_profile.get('financial_literacy', 'N/A')}")
            
            logger.info(f"\n💡 Advisor Strategy Note (Internal - User Cannot See):")
            logger.info(f"   {cognition.advisor_note}")
            
            # Verify correctness
            logger.info(f"\n✅ Verification:")
            if cognition.risk_profile.get('tolerance') == 'conservative':
                logger.info("   ✓ Correctly identified as CONSERVATIVE")
            if cognition.risk_profile.get('current_sentiment') == 'anxious':
                logger.info("   ✓ Correctly identified sentiment as ANXIOUS")
            if '2015' in cognition.advisor_note or '创伤' in cognition.advisor_note or '恐惧' in cognition.advisor_note:
                logger.info("   ✓ Advisor note references user's trauma")
            if '保本' in cognition.advisor_note or '稳健' in cognition.advisor_note:
                logger.info("   ✓ Advisor note recommends conservative approach")
        else:
            logger.warning("⚠️  Insight analysis not completed (may need more messages)")
        break
    
    # Test adaptive response
    print_subsection("Step 4: Adaptive Response (Next Turn)")
    
    logger.info("\n💬 User asks for investment advice:")
    investment_question = "那我这100万应该怎么投资比较好？有什么建议吗？"
    logger.info(f"   User: {investment_question}")
    
    response_chunks = []
    async for chunk in chat_agent.process_message(investment_question, user_id):
        response_chunks.append(chunk)
    
    full_response = "".join(response_chunks)
    logger.info(f"\n   AI Response:")
    logger.info(f"   {full_response}")
    
    # Analyze adaptive behavior
    print_subsection("Step 5: Adaptive Behavior Analysis")
    
    logger.info("\n🔍 Analyzing AI response for adaptive behavior...")
    
    # Check for conservative recommendations
    conservative_keywords = ["稳健", "保本", "债券", "银行理财", "货币基金", "安全", "保守", "低风险", "固定收益"]
    found_conservative = [kw for kw in conservative_keywords if kw in full_response]
    
    # Check for aggressive keywords (should be avoided)
    aggressive_keywords = ["股票", "股市", "高收益", "激进", "加密货币", "高风险", "波动"]
    found_aggressive = [kw for kw in aggressive_keywords if kw in full_response]
    
    # Check for empathetic tone
    empathy_keywords = ["理解", "担心", "压力", "安心", "放心", "安全感", "谨慎", "明智"]
    found_empathy = [kw for kw in empathy_keywords if kw in full_response]
    
    logger.info(f"\n📈 Conservative Keywords Found ({len(found_conservative)}):")
    for kw in found_conservative:
        logger.info(f"   ✓ {kw}")
    
    logger.info(f"\n⚠️  Aggressive Keywords Found ({len(found_aggressive)}):")
    if found_aggressive:
        for kw in found_aggressive:
            logger.info(f"   ✗ {kw}")
    else:
        logger.info("   ✓ None (Good!)")
    
    logger.info(f"\n💚 Empathy Keywords Found ({len(found_empathy)}):")
    for kw in found_empathy:
        logger.info(f"   ✓ {kw}")
    
    # Final scoring
    print_subsection("Step 6: Final Verification")
    
    score = 0
    max_score = 4
    
    logger.info("\n📊 Scoring:")
    
    if len(found_conservative) >= 2:
        logger.info("   ✅ [1/1] Response contains conservative recommendations")
        score += 1
    else:
        logger.info("   ❌ [0/1] Response lacks conservative recommendations")
    
    if len(found_aggressive) == 0:
        logger.info("   ✅ [1/1] Response avoids aggressive/triggering keywords")
        score += 1
    else:
        logger.info(f"   ❌ [0/1] Response contains {len(found_aggressive)} aggressive keywords")
    
    if len(found_empathy) >= 1:
        logger.info("   ✅ [1/1] Response shows empathy and understanding")
        score += 1
    else:
        logger.info("   ❌ [0/1] Response lacks empathetic tone")
    
    # Check if advisor note was used
    async for session in get_db_session():
        statement = select(UserCognition).where(UserCognition.user_id == user_id)
        result = await session.execute(statement)
        cognition = result.scalar_one_or_none()
        
        if cognition and cognition.advisor_note:
            logger.info("   ✅ [1/1] Advisor note exists and was available for context")
            score += 1
        else:
            logger.info("   ❌ [0/1] No advisor note found")
        break
    
    logger.info(f"\n{'=' * 80}")
    logger.info(f"  FINAL SCORE: {score}/{max_score}")
    logger.info(f"{'=' * 80}")
    
    if score >= 3:
        logger.info("\n🎉 SUCCESS! Phase 3 is working correctly!")
        logger.info("   The AI successfully:")
        logger.info("   • Analyzed user's psychological profile")
        logger.info("   • Identified conservative risk tolerance")
        logger.info("   • Adapted its recommendations accordingly")
        logger.info("   • Used empathetic and reassuring tone")
    else:
        logger.info(f"\n⚠️  NEEDS REVIEW: Score {score}/{max_score}")
        logger.info("   Some aspects of adaptive behavior may need tuning")
    
    print_section("Phase 3 Demonstration Complete")


if __name__ == "__main__":
    asyncio.run(demonstrate_phase3())
