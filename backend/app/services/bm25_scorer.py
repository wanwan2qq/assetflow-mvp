"""
BM25 Scoring Algorithm for Knowledge Retrieval

Implements the Okapi BM25 ranking function for improved text relevance scoring.
BM25 is a bag-of-words retrieval function that ranks documents based on query terms.

Formula: BM25(D,Q) = Σ IDF(qi) * (f(qi,D) * (k1 + 1)) / (f(qi,D) + k1 * (1 - b + b * |D|/avgdl))

Where:
- f(qi,D): frequency of term qi in document D
- |D|: length of document D in words
- avgdl: average document length
- k1: term frequency saturation parameter (typically 1.2-2.0)
- b: length normalization parameter (typically 0.75)
- IDF(qi): inverse document frequency of term qi

AI Coding Guidance:
- Use this for keyword-based retrieval in RAG system
- Combine with vector search for hybrid search
- Parameters k1 and b can be tuned for domain-specific optimization
"""

import math
import logging
import re
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)


class BM25Scorer:
    """
    BM25 scoring for document ranking.
    
    Example:
        scorer = BM25Scorer()
        scorer.fit(documents)  # Build IDF statistics
        scores = scorer.score(query, documents)
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 scorer.
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
                Higher values give more weight to term frequency
            b: Length normalization parameter (default: 0.75)
                0 = no length normalization, 1 = full normalization
        """
        self.k1 = k1
        self.b = b
        self.avgdl: float = 0.0
        self.doc_lengths: list[int] = []
        self.idf: dict[str, float] = {}
        self.doc_count: int = 0
    
    def tokenize(self, text: str) -> list[str]:
        """
        Tokenize Chinese and English text.
        
        Uses simple character-level tokenization for Chinese
        and word-level for English/numbers.
        """
        if not text:
            return []
        
        tokens = []
        
        # Split by whitespace and punctuation first
        text = text.lower()
        
        # Remove common punctuation
        text = re.sub(r'[,，。！？、；：""''（）【】《》\-_=+\[\]{}|\\/<>]', ' ', text)
        
        # Split into segments
        segments = text.split()
        
        for segment in segments:
            # Check if segment is mostly Chinese
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', segment)
            if len(chinese_chars) > len(segment) * 0.5:
                # Chinese: character-level tokenization with n-grams
                chars = list(segment)
                tokens.extend(chars)
                # Add bigrams for better phrase matching
                for i in range(len(chars) - 1):
                    tokens.append(chars[i] + chars[i + 1])
            else:
                # English/numbers: word-level
                if len(segment) > 1:  # Skip single characters
                    tokens.append(segment)
        
        return tokens
    
    def fit(self, documents: list[str]) -> "BM25Scorer":
        """
        Build IDF statistics from document corpus.
        
        Args:
            documents: List of document texts
            
        Returns:
            Self for chaining
        """
        self.doc_count = len(documents)
        if self.doc_count == 0:
            return self
        
        # Calculate document lengths and term document frequencies
        df: dict[str, int] = {}  # Document frequency
        total_length = 0
        
        for doc in documents:
            tokens = self.tokenize(doc)
            self.doc_lengths.append(len(tokens))
            total_length += len(tokens)
            
            # Count unique terms in document
            unique_terms = set(tokens)
            for term in unique_terms:
                df[term] = df.get(term, 0) + 1
        
        # Calculate average document length
        self.avgdl = total_length / self.doc_count if self.doc_count > 0 else 1.0
        
        # Calculate IDF for each term
        # IDF(q) = log((N - n(q) + 0.5) / (n(q) + 0.5) + 1)
        for term, freq in df.items():
            numerator = self.doc_count - freq + 0.5
            denominator = freq + 0.5
            self.idf[term] = math.log(numerator / denominator + 1.0)
        
        logger.debug(f"BM25 fitted on {self.doc_count} documents, avgdl={self.avgdl:.1f}")
        return self
    
    def score_document(self, query: str, document: str, doc_length: int | None = None) -> float:
        """
        Calculate BM25 score for a single document.
        
        Args:
            query: Query text
            document: Document text
            doc_length: Optional pre-calculated document length
            
        Returns:
            BM25 score (higher = more relevant)
        """
        query_tokens = self.tokenize(query)
        doc_tokens = self.tokenize(document)
        
        if not query_tokens or not doc_tokens:
            return 0.0
        
        dl = doc_length if doc_length is not None else len(doc_tokens)
        avgdl = self.avgdl if self.avgdl > 0 else len(doc_tokens)
        
        # Count term frequencies in document
        tf = Counter(doc_tokens)
        
        score = 0.0
        for term in query_tokens:
            if term not in tf:
                continue
            
            # Get IDF (use default if term not seen during fit)
            idf = self.idf.get(term, math.log((self.doc_count + 0.5) / 0.5 + 1.0))
            
            # BM25 term score
            freq = tf[term]
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (1 - self.b + self.b * dl / avgdl)
            
            score += idf * numerator / denominator
        
        return score
    
    def score_batch(self, query: str, documents: list[str]) -> list[float]:
        """
        Calculate BM25 scores for multiple documents.
        
        Args:
            query: Query text
            documents: List of document texts
            
        Returns:
            List of BM25 scores
        """
        return [self.score_document(query, doc) for doc in documents]
    
    def score_with_indices(
        self, 
        query: str, 
        documents: list[str]
    ) -> list[tuple[int, float]]:
        """
        Score documents and return indexed results sorted by score.
        
        Args:
            query: Query text
            documents: List of document texts
            
        Returns:
            List of (index, score) tuples sorted by score descending
        """
        scores = self.score_batch(query, documents)
        indexed = [(i, score) for i, score in enumerate(scores)]
        indexed.sort(key=lambda x: x[1], reverse=True)
        return indexed


# Pre-built scorer instance for knowledge base
_default_scorer: BM25Scorer | None = None


def get_bm25_scorer() -> BM25Scorer:
    """Get or create default BM25 scorer."""
    global _default_scorer
    if _default_scorer is None:
        _default_scorer = BM25Scorer()
    return _default_scorer


def score_documents(
    query: str,
    documents: list[str],
    top_k: int | None = None
) -> list[tuple[int, float]]:
    """
    Convenience function to score documents with BM25.
    
    Args:
        query: Query text
        documents: List of document texts
        top_k: Optional limit on results
        
    Returns:
        List of (index, score) tuples sorted by score
    """
    scorer = get_bm25_scorer()
    
    # Fit on documents if not already fitted
    if scorer.doc_count == 0:
        scorer.fit(documents)
    
    results = scorer.score_with_indices(query, documents)
    
    if top_k is not None:
        results = results[:top_k]
    
    return results
