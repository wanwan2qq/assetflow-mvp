"""
Phase 4: L3 Vector Memory Model
Long-term unstructured memory storage with semantic search capabilities
"""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, Index, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    # Fallback for development without pgvector
    Vector = None


class VectorMemory(SQLModel, table=True):
    """
    L3 Layer: Vector Memory for long-term unstructured memory
    
    Stores semantic memories that don't fit into L1 (Assets) or L2 (Cognition)
    Examples:
    - "User mentioned mother is sick, needs liquidity"
    - "User is planning to buy a house in 2 years"
    - "User expressed concern about stock market volatility"
    """
    
    __tablename__ = "vector_memory"
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    
    # The actual memory text
    content: str = Field(sa_column=Column(Text, nullable=False))
    
    # Vector embedding for semantic search (1024 dimensions for BAAI/bge-large-zh-v1.5)
    # Using sa_column to handle pgvector type
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(Vector(1024), nullable=True) if PGVECTOR_AVAILABLE else Column(Text, nullable=True)
    )
    
    # Metadata for context (JSON) - using JSONB for PostgreSQL
    metadata_: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column("metadata", JSONB, nullable=True)
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Add index for user_id and created_at for efficient queries
    __table_args__ = (
        Index('ix_vector_memory_user_created', 'user_id', 'created_at'),
    )
    
    class Config:
        arbitrary_types_allowed = True


class VectorMemoryCreate(SQLModel):
    """Schema for creating vector memory"""
    user_id: int
    content: str
    metadata_: dict[str, Any] | None = None


class VectorMemoryRead(SQLModel):
    """Schema for reading vector memory"""
    id: int
    user_id: int
    content: str
    metadata_: dict[str, Any] | None
    created_at: datetime
    
    class Config:
        from_attributes = True
