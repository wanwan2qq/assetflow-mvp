import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.knowledge_retriever import get_knowledge_retriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_filtering():
    retriever = get_knowledge_retriever()
    
    query = "限购政策"
    
    print("\n--- Test 1: Beijing Filter ---")
    filters = {"city": "北京"}
    results_bj = await retriever.search(query, filters=filters, top_k=10)
    for r in results_bj:
        print(f"[{r.score:.2f}] {r.title} (City in Metadata: {r.metadata})")
        
    bj_titles = [r.title for r in results_bj]
    assert any("北京" in t for t in bj_titles), "Should contain Beijing policy"
    assert not any("上海" in t for t in bj_titles), "Should NOT contain Shanghai policy"
    print("✅ Beijing Filter Passed")

    print("\n--- Test 2: Shanghai Filter ---")
    filters = {"city": "上海"}
    results_sh = await retriever.search(query, filters=filters, top_k=10)
    for r in results_sh:
        print(f"[{r.score:.2f}] {r.title}")
        
    sh_titles = [r.title for r in results_sh]
    assert any("上海" in t for t in sh_titles), "Should contain Shanghai policy"
    assert not any("北京" in t for t in sh_titles), "Should NOT contain Beijing policy"
    print("✅ Shanghai Filter Passed")
    
    print("\n--- Test 3: No Filter ---")
    results_all = await retriever.search(query, top_k=10)
    all_titles = [r.title for r in results_all]
    print(f"Total results: {len(results_all)}")
    # Should likely contain both if semantic similarity is high enough
    has_bj = any("北京" in t for t in all_titles)
    has_sh = any("上海" in t for t in all_titles)
    print(f"Has Beijing: {has_bj}, Has Shanghai: {has_sh}")
    
    if has_bj and has_sh:
        print("✅ No Filter Passed (Mixed results found)")
    else:
        print("⚠️ No Filter Warning: Might not have found both, but that depends on top_k and similarity.")

if __name__ == "__main__":
    asyncio.run(test_filtering())
