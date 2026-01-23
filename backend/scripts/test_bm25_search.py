"""
BM25 Search Test Script

Tests the BM25 scoring functionality in KnowledgeRetriever.

Usage:
    python -m scripts.test_bm25_search
"""

import asyncio
import logging
from app.services.knowledge_retriever import KnowledgeRetriever
from app.services.bm25_scorer import BM25Scorer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bm25_scorer_direct():
    """Test BM25Scorer class directly"""
    print("\n" + "=" * 60)
    print("🧪 Testing BM25Scorer Direct")
    print("=" * 60)
    
    documents = [
        "家庭财务规划是管理家庭资产的重要方式",
        "保险保障可以规避家庭重大风险",
        "如何进行合理的资产配置",
        "股票基金属于高风险高收益投资",
        "定期存款适合作为保本升值的钱"
    ]
    
    scorer = BM25Scorer()
    scorer.fit(documents)
    
    query = "家庭资产配置"
    print(f"\nQuery: {query}")
    
    scores = scorer.score_with_indices(query, documents)
    
    for idx, score in scores:
        print(f"Doc: {documents[idx]}")
        print(f"Score: {score:.4f}")

async def test_knowledge_retriever_bm25():
    """Test KnowledgeRetriever with BM25"""
    print("\n" + "=" * 60)
    print("🧪 Testing KnowledgeRetriever (Hybrid/BM25)")
    print("=" * 60)
    
    retriever = KnowledgeRetriever()
    
    # Test queries that should trigger keyword matches
    queries = [
        "家庭财务规划",
        "保险保障",
        "资产配置建议"
    ]
    
    for query in queries:
        print(f"\n🔍 Searching for: {query}")
        try:
            results = await retriever.search(query, top_k=3)
            
            if not results:
                print("   No results found.")
            else:
                for r in results:
                    search_type = r.metadata.get('search_type', 'unknown')
                    print(f"   [{search_type}] {r.title} (Score: {r.score:.4f})")
                    # print(f"      Content snippet: {r.content[:50]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    await test_bm25_scorer_direct()
    await test_knowledge_retriever_bm25()

if __name__ == "__main__":
    asyncio.run(main())
