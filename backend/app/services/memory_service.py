"""
Phase 4: L3 Vector Memory Service (RAG)
Handles long-term unstructured memory with semantic search using local BGE embeddings
"""

import logging
import os
from datetime import datetime
from typing import Any

# CRITICAL: Force offline mode for HuggingFace
# These environment variables must be set BEFORE importing HuggingFaceEmbeddings
# to prevent the library from trying to check for model updates online
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

from langchain_huggingface import HuggingFaceEmbeddings
import sqlalchemy as sa
from sqlalchemy import text
from sqlmodel import select

from app.core.config import settings
from app.core.database import get_db_session
from app.models.memory import VectorMemory

logger = logging.getLogger(__name__)


class MemoryService:
    """
    L3 Vector Memory Service
    
    Provides semantic memory storage and retrieval using pgvector.
    Uses local BAAI/bge-large-zh-v1.5 model for embeddings (1024 dimensions).
    Stores unstructured long-term memories that don't fit L1/L2.
    """
    
    def __init__(self):
        """
        Initialize memory service with lazy loading of BGE embeddings.
        Model will be loaded on first use to avoid blocking service startup.
        """
        self._embeddings = None  # Lazy initialization
        self._model_loading = False
        self._model_load_failed = False
        
        # Log initialization mode
        if os.getenv('HF_HUB_OFFLINE') == '1':
            logger.info("MemoryService initialized in OFFLINE mode (using cached BGE model)")
        else:
            logger.info("MemoryService initialized (BGE model will load on first use)")
    
    @property
    def embeddings(self):
        """
        Lazy loading of embedding model.
        Model is loaded on first access to avoid blocking service startup.
        """
        if self._embeddings is None and not self._model_load_failed and not self._model_loading:
            self._model_loading = True
            try:
                # Check if offline mode is enabled
                offline_mode = os.getenv('HF_HUB_OFFLINE') == '1'
                if offline_mode:
                    logger.info("Loading BGE model in OFFLINE mode (using local cache)")
                else:
                    logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
                    logger.info("This may take a few seconds on first use...")
                
                # Initialize local BGE embeddings (BAAI/bge-large-zh-v1.5, 1024 dimensions)
                # Use CPU to avoid complex GPU setup in Docker, it's fast enough for embeddings
                model_kwargs = {'device': 'cpu'}
                if offline_mode:
                    model_kwargs['local_files_only'] = True
                    logger.info("🔧 Forced local_files_only=True for SentenceTransformer")

                self._embeddings = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL_NAME,
                    model_kwargs=model_kwargs,
                    encode_kwargs={'normalize_embeddings': True}
                )
                logger.info(f"✅ Embedding model loaded successfully: {settings.EMBEDDING_MODEL_NAME}")
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                logger.warning("⚠️  Vector memory features will be disabled")
                logger.warning("⚠️  Tip: Set HF_ENDPOINT=https://hf-mirror.com in .env to use mirror")
                self._model_load_failed = True
            finally:
                self._model_loading = False
        
        return self._embeddings
    
    async def add_memory(
        self, 
        user_id: int, 
        text: str,
        metadata: dict[str, Any] | None = None
    ) -> VectorMemory | None:
        """
        Add a new memory to the vector store
        
        Args:
            user_id: User ID
            text: Memory text content
            metadata: Optional metadata (e.g., source_message_id, tags, category)
            
        Returns:
            Created VectorMemory object or None if failed
        """
        try:
            # Generate embedding
            embedding = await self._generate_embedding(text)
            
            if embedding is None:
                logger.warning(f"Failed to generate embedding for memory: {text[:50]}...")
                # Still store the memory without embedding for development
            
            # Create memory record
            memory = VectorMemory(
                user_id=user_id,
                content=text,
                embedding=embedding,
                metadata_=metadata or {},
                created_at=datetime.utcnow()
            )
            
            # Save to database
            async for session in get_db_session():
                session.add(memory)
                await session.commit()
                await session.refresh(memory)
                
                logger.info(f"Added memory for user {user_id}: {text[:50]}...")
                return memory
                
        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {e}")
            return None
    
    async def retrieve_relevant(
        self, 
        user_id: int, 
        query_text: str, 
        limit: int = 3,
        similarity_threshold: float = 0.7
    ) -> list[dict[str, Any]]:
        """
        Retrieve relevant memories using semantic search
        
        Args:
            user_id: User ID
            query_text: Query text to search for
            limit: Maximum number of memories to return
            similarity_threshold: Minimum cosine similarity (0-1)
            
        Returns:
            List of relevant memories with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query_text)
            
            if query_embedding is None:
                logger.warning("Failed to generate query embedding, falling back to keyword search")
                return await self._fallback_keyword_search(user_id, query_text, limit)
            
            # Perform cosine similarity search using pgvector
            async for session in get_db_session():
                # Use parameterized query to prevent SQL injection
                # Convert embedding list to PostgreSQL array format
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                # Use SQLAlchemy text() with bound parameters for safety
                # Note: PostgreSQL uses $1, $2 for positional parameters with asyncpg
                sql_query = text("""
                    SELECT 
                        id,
                        user_id,
                        content,
                        metadata,
                        created_at,
                        1 - (embedding <=> CAST(:embedding_vector AS vector)) as similarity
                    FROM vector_memory
                    WHERE user_id = :user_id
                        AND embedding IS NOT NULL
                        AND 1 - (embedding <=> CAST(:embedding_vector AS vector)) >= :threshold
                    ORDER BY embedding <=> CAST(:embedding_vector AS vector)
                    LIMIT :limit_val
                """)
                
                # Execute with bound parameters
                result = await session.execute(
                    sql_query,
                    {
                        "embedding_vector": embedding_str,
                        "user_id": user_id,
                        "threshold": similarity_threshold,
                        "limit_val": limit
                    }
                )
                
                rows = result.fetchall()
                
                memories = []
                for row in rows:
                    memories.append({
                        "id": row.id,
                        "content": row.content,
                        "metadata": row.metadata,
                        "created_at": row.created_at,
                        "similarity": float(row.similarity)
                    })
                
                logger.info(f"Retrieved {len(memories)} relevant memories for user {user_id}")
                return memories
                
        except Exception as e:
            logger.error(f"Error retrieving memories for user {user_id}: {e}")
            # Fallback to keyword search
            return await self._fallback_keyword_search(user_id, query_text, limit)
    
    async def _generate_embedding(self, text: str) -> list[float] | None:
        """
        Generate embedding vector for text using local BGE model
        
        Note: HuggingFaceEmbeddings.embed_query is synchronous, but it's fast enough
        that we don't need to run it in a thread pool for typical use cases.
        """
        try:
            if not self.embeddings:
                logger.warning("Embeddings not initialized")
                return None
            
            # Generate embedding using local BGE model
            # This is a synchronous call but typically completes in < 100ms
            embedding = self.embeddings.embed_query(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    async def _fallback_keyword_search(
        self, 
        user_id: int, 
        query_text: str, 
        limit: int
    ) -> list[dict[str, Any]]:
        """
        Fallback keyword-based search when embeddings are not available
        Uses PostgreSQL full-text search
        """
        try:
            async for session in get_db_session():
                # Simple keyword search using ILIKE
                keywords = query_text.split()[:5]  # Use first 5 words
                
                statement = (
                    select(VectorMemory)
                    .where(VectorMemory.user_id == user_id)
                    .order_by(VectorMemory.created_at.desc())
                    .limit(limit * 2)  # Get more results for filtering
                )
                
                result = await session.execute(statement)
                all_memories = result.scalars().all()
                
                # Filter by keyword match
                matched_memories = []
                for memory in all_memories:
                    content_lower = memory.content.lower()
                    match_count = sum(1 for kw in keywords if kw.lower() in content_lower)
                    
                    if match_count > 0:
                        matched_memories.append({
                            "id": memory.id,
                            "content": memory.content,
                            "metadata": memory.metadata_,
                            "created_at": memory.created_at,
                            "similarity": match_count / len(keywords)  # Simple relevance score
                        })
                
                # Sort by relevance and limit
                matched_memories.sort(key=lambda x: x["similarity"], reverse=True)
                return matched_memories[:limit]
                
        except Exception as e:
            logger.error(f"Error in fallback keyword search: {e}")
            return []
    
    async def get_recent_memories(
        self, 
        user_id: int, 
        limit: int = 10
    ) -> list[VectorMemory]:
        """Get recent memories for a user (chronological order)"""
        try:
            async for session in get_db_session():
                statement = (
                    select(VectorMemory)
                    .where(VectorMemory.user_id == user_id)
                    .order_by(VectorMemory.created_at.desc())
                    .limit(limit)
                )
                
                result = await session.execute(statement)
                memories = result.scalars().all()
                
                return list(memories)
                
        except Exception as e:
            logger.error(f"Error getting recent memories: {e}")
            return []
    
    async def delete_memory(self, memory_id: int, user_id: int) -> bool:
        """Delete a specific memory"""
        try:
            async for session in get_db_session():
                statement = (
                    select(VectorMemory)
                    .where(VectorMemory.id == memory_id)
                    .where(VectorMemory.user_id == user_id)
                )
                
                result = await session.execute(statement)
                memory = result.scalar_one_or_none()
                
                if memory:
                    await session.delete(memory)
                    await session.commit()
                    logger.info(f"Deleted memory {memory_id} for user {user_id}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False


# Global service instance
_memory_service: MemoryService | None = None


def get_memory_service() -> MemoryService:
    """Get or create memory service instance"""
    global _memory_service
    if _memory_service is None:
        _memory_service = MemoryService()
    return _memory_service
