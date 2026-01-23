"""
RAG Effectiveness Test Script

Tests RAG knowledge retrieval with real housing policy questions.
Compares RAG-augmented responses with confidence scores.

Usage:
    python -m scripts.test_rag_effectiveness
"""

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test questions covering different knowledge categories
TEST_QUESTIONS = [
    # Policy questions (should hit PolicyKnowledge)
    ("北京外地人买房需要什么条件？", "policy"),
    ("上海购房限购政策是什么？", "policy"),
    ("深圳买房需要几年社保？", "policy"),
    
    # Loan questions
    ("北京首套房首付比例是多少？", "loan"),
    ("公积金贷款和商业贷款有什么区别？", "loan"),
    
    # FAQ questions
    ("契税怎么算？", "faq"),
    ("什么是LPR利率？", "faq"),
    ("二手房交易流程是什么？", "faq"),
    
    # Provident fund questions
    ("公积金可以提取吗？", "provident_fund"),
    ("北京公积金贷款上限是多少？", "provident_fund"),
]


async def test_rag_retrieval():
    """Test RAG knowledge retrieval"""
    from app.services.rag_engine import get_rag_engine
    from app.services.knowledge_retriever import get_knowledge_retriever
    
    rag_engine = get_rag_engine()
    retriever = get_knowledge_retriever()
    
    results = []
    
    print("\n" + "=" * 60)
    print("🔍 RAG 检索效果测试")
    print("=" * 60)
    
    for question, expected_category in TEST_QUESTIONS:
        print(f"\n📝 问题: {question}")
        print(f"   期望类别: {expected_category}")
        
        # Test retrieval
        chunks = await retriever.search(query=question, top_k=3)
        
        if chunks:
            top_chunk = chunks[0]
            print(f"   ✅ 检索到 {len(chunks)} 条结果")
            print(f"   📚 最佳匹配: [{top_chunk.category}] {top_chunk.title}")
            print(f"   🎯 相似度: {top_chunk.score:.2%}")
            
            # Check if category matches expected
            category_match = top_chunk.category == expected_category
            results.append({
                "question": question,
                "expected": expected_category,
                "actual": top_chunk.category,
                "score": top_chunk.score,
                "matched": category_match,
                "chunks_count": len(chunks)
            })
        else:
            print(f"   ❌ 未检索到结果")
            results.append({
                "question": question,
                "expected": expected_category,
                "actual": None,
                "score": 0,
                "matched": False,
                "chunks_count": 0
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    total = len(results)
    hits = sum(1 for r in results if r["chunks_count"] > 0)
    category_matches = sum(1 for r in results if r["matched"])
    avg_score = sum(r["score"] for r in results) / total if total > 0 else 0
    
    print(f"   总测试数: {total}")
    print(f"   检索命中: {hits}/{total} ({hits/total:.0%})")
    print(f"   类别匹配: {category_matches}/{total} ({category_matches/total:.0%})")
    print(f"   平均相似度: {avg_score:.2%}")
    
    # Score distribution
    high_conf = sum(1 for r in results if r["score"] >= 0.7)
    med_conf = sum(1 for r in results if 0.4 <= r["score"] < 0.7)
    low_conf = sum(1 for r in results if r["score"] < 0.4)
    
    print(f"\n   置信度分布:")
    print(f"   - 高 (≥70%): {high_conf}")
    print(f"   - 中 (40-70%): {med_conf}")
    print(f"   - 低 (<40%): {low_conf}")
    
    return results


async def test_full_rag_query():
    """Test full RAG query with rule engine"""
    from app.services.rag_engine import get_rag_engine
    
    rag_engine = get_rag_engine()
    
    print("\n" + "=" * 60)
    print("🧠 完整 RAG 查询测试 (含规则引擎)")
    print("=" * 60)
    
    # Test with user context
    user_context = {
        "city": "北京",
        "profile": {
            "hukou": "non_local",
            "properties_owned": 0
        }
    }
    
    test_question = "我是外地人，想在北京买房，需要满足什么条件？"
    
    print(f"\n📝 问题: {test_question}")
    print(f"📍 用户上下文: 北京, 非京籍, 无房")
    
    response = await rag_engine.query(
        question=test_question,
        user_context=user_context,
        top_k=3
    )
    
    print(f"\n📚 检索来源: {len(response.sources)} 条")
    for src in response.sources:
        print(f"   - [{src.category}] {src.title} (score: {src.score:.2%})")
    
    print(f"\n⚖️ 规则匹配: {len(response.rules_applied)} 条")
    for rule in response.rules_applied:
        print(f"   - {rule.constraint_text}")
    
    print(f"\n🎯 置信度: {response.confidence:.2%}")
    print(f"\n💬 回答预览:")
    print(response.answer[:200] + "..." if len(response.answer) > 200 else response.answer)


async def main():
    print(f"\n🚀 RAG 效果测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Retrieval
    await test_rag_retrieval()
    
    # Test 2: Full RAG query
    await test_full_rag_query()
    
    print("\n✅ 测试完成!")


if __name__ == "__main__":
    asyncio.run(main())
