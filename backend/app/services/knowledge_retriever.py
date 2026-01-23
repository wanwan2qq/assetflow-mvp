"""
Knowledge Retriever - Semantic Search for RAG System

This service provides knowledge retrieval capabilities:
- Vector search using BGE embeddings
- Keyword search using PostgreSQL full-text search
- Hybrid search combining both methods

AI Coding Guidance:
- Use MemoryService for embedding generation
- Results are sorted by relevance score
- Filter by category and status for targeted search
"""

import logging
from typing import Any

from sqlmodel import select
from sqlalchemy import text, or_, and_

from app.core.database import get_db_session
from app.models.knowledge import (
    FAQKnowledge,
    KnowledgeCategory,
    KnowledgeChunk,
    KnowledgeStatus,
    PolicyKnowledge,
    ProductKnowledge,
)
from app.services.memory_service import MemoryService
from app.services.bm25_scorer import BM25Scorer

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """
    知识检索器
    
    实现 Hybrid Search: 向量检索 + 关键词检索
    支持多种知识类型的统一检索接口
    """
    
    def __init__(self):
        self._memory_service: MemoryService | None = None
        self._bm25_scorer: BM25Scorer | None = None
    
    @property
    def memory_service(self) -> MemoryService:
        """懒加载 MemoryService"""
        if self._memory_service is None:
            self._memory_service = MemoryService()
        return self._memory_service
    
    @property
    def bm25_scorer(self) -> BM25Scorer:
        """懒加载 BM25Scorer"""
        if self._bm25_scorer is None:
            self._bm25_scorer = BM25Scorer(k1=1.5, b=0.75)
        return self._bm25_scorer
    
    async def search(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> list[KnowledgeChunk]:
        """
        混合搜索 (Hybrid Search)
        
        结合向量检索和关键词检索的结果
        
        Args:
            query: 查询文本
            category: 可选的知识分类过滤
            top_k: 返回结果数量
            min_score: 最低相似度阈值
            
        Returns:
            按相关性排序的 KnowledgeChunk 列表
        """
        # 并行执行向量搜索和关键词搜索
        vector_results = await self.vector_search(query, category, top_k * 2)
        keyword_results = await self.keyword_search(query, category, top_k * 2)
        
        # 合并结果，去重
        merged = self._merge_results(vector_results, keyword_results)
        
        # 过滤低分结果，截取 top_k
        filtered = [r for r in merged if r.score >= min_score]
        
        return filtered[:top_k]
    
    async def vector_search(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 10
    ) -> list[KnowledgeChunk]:
        """
        向量相似度搜索
        
        使用 BGE 生成 query embedding，
        通过余弦相似度检索最相关的知识
        """
        results: list[KnowledgeChunk] = []
        
        # 生成 query embedding
        if self.memory_service.embeddings is None:
            logger.warning("Embedding model not loaded, skipping vector search")
            return results
        
        try:
            query_embedding = self.memory_service.embeddings.embed_query(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return results
        
        # 搜索 PolicyKnowledge
        policy_results = await self._vector_search_table(
            PolicyKnowledge,
            query_embedding,
            category,
            top_k
        )
        results.extend(policy_results)
        
        # 搜索 FAQKnowledge
        faq_results = await self._vector_search_table(
            FAQKnowledge,
            query_embedding,
            category,
            top_k
        )
        results.extend(faq_results)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    async def keyword_search(
        self,
        query: str,
        category: str | None = None,
        top_k: int = 10
    ) -> list[KnowledgeChunk]:
        """
        关键词搜索
        
        使用 PostgreSQL LIKE 和分词匹配
        """
        results: list[KnowledgeChunk] = []
        
        # 分词
        keywords = self._tokenize_query(query)
        if not keywords:
            return results
        
        async for session in get_db_session():
            # 搜索 PolicyKnowledge
            policy_results = await self._keyword_search_table(
                session,
                PolicyKnowledge,
                keywords,
                category,
                top_k
            )
            results.extend(policy_results)
            
            # 搜索 FAQKnowledge  
            faq_results = await self._keyword_search_table(
                session,
                FAQKnowledge,
                keywords,
                category,
                top_k
            )
            results.extend(faq_results)
        
        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:top_k]
    
    async def _vector_search_table(
        self,
        model,
        query_embedding: list[float],
        category: str | None,
        top_k: int
    ) -> list[KnowledgeChunk]:
        """对单个表执行向量搜索"""
        results = []
        
        async for session in get_db_session():
            # 构建查询
            stmt = select(model).where(
                model.status == KnowledgeStatus.ACTIVE
            )
            
            if category and hasattr(model, 'category'):
                stmt = stmt.where(model.category == category)
            
            # 只查询有 embedding 的记录
            stmt = stmt.where(model.embedding.isnot(None))
            
            records = (await session.execute(stmt)).scalars().all()
            
            for record in records:
                if record.embedding:
                    score = self._cosine_similarity(query_embedding, record.embedding)
                    
                    # 构建 KnowledgeChunk
                    if hasattr(record, 'title'):
                        title = record.title
                        content = record.content
                    else:
                        title = record.question if hasattr(record, 'question') else record.name
                        content = record.answer if hasattr(record, 'answer') else record.description
                    
                    results.append(KnowledgeChunk(
                        id=record.id,
                        category=record.category.value if hasattr(record.category, 'value') else str(record.category),
                        title=title,
                        content=content,
                        score=score,
                        source=getattr(record, 'source', None),
                        metadata={"type": model.__tablename__}
                    ))
        
        return results
    
    async def _keyword_search_table(
        self,
        session,
        model,
        keywords: list[str],
        category: str | None,
        top_k: int
    ) -> list[KnowledgeChunk]:
        """对单个表执行关键词搜索"""
        results = []
        
        # 构建 LIKE 条件
        conditions = []
        for kw in keywords:
            like_pattern = f"%{kw}%"
            if hasattr(model, 'content'):
                conditions.append(model.content.ilike(like_pattern))
            if hasattr(model, 'title'):
                conditions.append(model.title.ilike(like_pattern))
            if hasattr(model, 'question'):
                conditions.append(model.question.ilike(like_pattern))
            if hasattr(model, 'answer'):
                conditions.append(model.answer.ilike(like_pattern))
        
        if not conditions:
            return results
        
        stmt = select(model).where(
            and_(
                model.status == KnowledgeStatus.ACTIVE,
                or_(*conditions)
            )
        )
        
        if category and hasattr(model, 'category'):
            stmt = stmt.where(model.category == category)
        
        stmt = stmt.limit(top_k)
        
        records = (await session.execute(stmt)).scalars().all()
        
        # Collect all document texts for BM25 fitting
        doc_texts = []
        for record in records:
            if hasattr(record, 'title'):
                text_content = f"{record.title} {record.content}"
            else:
                text_content = f"{getattr(record, 'question', '')} {getattr(record, 'answer', getattr(record, 'description', ''))}"
            doc_texts.append(text_content)
        
        # Fit BM25 on the corpus if we have documents
        if doc_texts:
            self.bm25_scorer.fit(doc_texts)
        
        # Reconstruct query from keywords
        query_text = " ".join(keywords)
        
        for i, record in enumerate(records):
            # Use BM25 score instead of simple hit count
            text_content = doc_texts[i] if i < len(doc_texts) else ""
            bm25_score = self.bm25_scorer.score_document(query_text, text_content)
            
            # Normalize BM25 score to 0-0.8 range (keyword search max 0.8)
            # Typical BM25 scores range from 0 to ~10-20 for relevant docs
            normalized_score = min(0.8, bm25_score / 10.0)
            
            if hasattr(record, 'title'):
                title = record.title
                content = record.content
            else:
                title = record.question if hasattr(record, 'question') else record.name
                content = getattr(record, 'answer', getattr(record, 'description', ''))
            
            results.append(KnowledgeChunk(
                id=record.id,
                category=record.category.value if hasattr(record.category, 'value') else str(record.category),
                title=title,
                content=content,
                score=normalized_score,
                source=getattr(record, 'source', None),
                metadata={"type": model.__tablename__, "search_type": "bm25"}
            ))
        
        return results
    
    def _merge_results(
        self,
        vector_results: list[KnowledgeChunk],
        keyword_results: list[KnowledgeChunk]
    ) -> list[KnowledgeChunk]:
        """合并向量和关键词搜索结果，去重"""
        seen_ids = set()
        merged = []
        
        # 向量结果优先
        for r in vector_results:
            key = (r.metadata.get("type", ""), r.id)
            if key not in seen_ids:
                seen_ids.add(key)
                merged.append(r)
        
        # 添加关键词结果 (未在向量中出现的)
        for r in keyword_results:
            key = (r.metadata.get("type", ""), r.id)
            if key not in seen_ids:
                seen_ids.add(key)
                merged.append(r)
        
        # 按分数排序
        merged.sort(key=lambda x: x.score, reverse=True)
        
        return merged
    
    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        import math
        
        if len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _tokenize_query(self, query: str) -> list[str]:
        """简单中文分词 (按空格和标点)"""
        import re
        
        # 移除标点，按空格分割
        cleaned = re.sub(r'[^\w\s]', ' ', query)
        tokens = [t.strip() for t in cleaned.split() if t.strip()]
        
        # 对于中文，也提取连续的中文字符作为关键词
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')
        chinese_tokens = chinese_pattern.findall(query)
        
        # 合并去重
        all_tokens = list(set(tokens + chinese_tokens))
        
        return all_tokens


# ============================================================================
# Singleton Factory
# ============================================================================

_knowledge_retriever: KnowledgeRetriever | None = None


def get_knowledge_retriever() -> KnowledgeRetriever:
    """获取 KnowledgeRetriever 单例"""
    global _knowledge_retriever
    if _knowledge_retriever is None:
        _knowledge_retriever = KnowledgeRetriever()
    return _knowledge_retriever
