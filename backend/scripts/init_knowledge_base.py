"""
Knowledge Base Initialization Script

This script populates the knowledge base with initial data:
- 20+ policy records (purchase limits, loan policies)
- 50+ FAQ records
- Sample product records

Usage:
    python -m scripts.init_knowledge_base

AI Coding Guidance:
- Run after database migration
- Generates embeddings for all records
- Safe to run multiple times (checks for existing data)
"""

import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import get_db_session
from app.models.knowledge import (
    FAQKnowledge,
    KnowledgeCategory,
    KnowledgeStatus,
    PolicyKnowledge,
    ProductKnowledge,
)
from app.services.memory_service import MemoryService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Initial Policy Data
# ============================================================================


def load_yaml_data(filename: str) -> list[dict]:
    """Load data from YAML file in backend/data/knowledge directory"""
    import yaml
    
    data_dir = Path(__file__).parent.parent / "data" / "knowledge"
    file_path = data_dir / filename
    
    if not file_path.exists():
        logger.warning(f"Data file not found: {file_path}")
        return []
        
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or []


async def init_policies(memory_service: MemoryService):
    """初始化政策知识"""
    policies = load_yaml_data("policies.yaml")
    if not policies:
        logger.warning("No policies found in policies.yaml")
        return

    async for session in get_db_session():
        for policy_data in policies:
            # 检查是否已存在
            from sqlmodel import select
            stmt = select(PolicyKnowledge).where(
                PolicyKnowledge.title == policy_data["title"]
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if existing:
                logger.info(f"Policy already exists: {policy_data['title']}")
                continue
            
            # 生成 embedding
            embedding = None
            if memory_service.embeddings:
                try:
                    text_for_embedding = f"{policy_data['title']} {policy_data['content']}"
                    embedding = memory_service.embeddings.embed_query(text_for_embedding)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")
            
            # 转换 category 字符串为枚举
            if "category" in policy_data:
                try:
                    category_str = policy_data["category"]
                    policy_data["category"] = KnowledgeCategory(category_str)
                except ValueError:
                    logger.warning(f"Invalid category {policy_data.get('category')} for {policy_data['title']}, defaulting to POLICY")
                    policy_data["category"] = KnowledgeCategory.POLICY

            policy = PolicyKnowledge(
                **policy_data,
                embedding=embedding
            )
            session.add(policy)
            logger.info(f"Added policy: {policy_data['title']}")
        
        await session.commit()




async def init_faqs(memory_service: MemoryService):
    """初始化 FAQ 知识"""
    faqs = load_yaml_data("faqs.yaml")
    if not faqs:
        logger.warning("No FAQs found in faqs.yaml")
        return

    async for session in get_db_session():
        for faq_data in faqs:
            # 检查是否已存在
            from sqlmodel import select
            stmt = select(FAQKnowledge).where(
                FAQKnowledge.question == faq_data["question"]
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if existing:
                logger.info(f"FAQ already exists: {faq_data['question'][:30]}...")
                continue
            
            # 生成 embedding
            embedding = None
            if memory_service.embeddings:
                try:
                    embedding = memory_service.embeddings.embed_query(faq_data["question"])
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")
            
            # 转换 category 字符串为枚举
            if "category" in faq_data:
                try:
                    category_str = faq_data["category"]
                    faq_data["category"] = KnowledgeCategory(category_str)
                except ValueError:
                    faq_data["category"] = KnowledgeCategory.FAQ

            faq = FAQKnowledge(
                **faq_data,
                embedding=embedding
            )
            session.add(faq)
            logger.info(f"Added FAQ: {faq_data['question'][:30]}...")
        
        await session.commit()


async def init_products(memory_service: MemoryService):
    """初始化产品知识"""
    products = load_yaml_data("products.yaml")
    if not products:
        logger.warning("No products found in products.yaml")
        return

    async for session in get_db_session():
        for product_data in products:
            # 检查是否已存在
            from sqlmodel import select
            stmt = select(ProductKnowledge).where(
                ProductKnowledge.name == product_data["name"]
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if existing:
                logger.info(f"Product already exists: {product_data['name']}")
                continue
            
            # 生成 embedding
            embedding = None
            if memory_service.embeddings:
                try:
                    text_for_embedding = f"{product_data['name']} {product_data['description']}"
                    embedding = memory_service.embeddings.embed_query(text_for_embedding)
                except Exception as e:
                    logger.warning(f"Failed to generate embedding: {e}")
            
            product = ProductKnowledge(
                **product_data,
                embedding=embedding
            )
            session.add(product)
            logger.info(f"Added product: {product_data['name']}")
        
        await session.commit()


async def main():
    """主入口"""
    logger.info("=== Knowledge Base Initialization ===")
    
    # 初始化 MemoryService (用于生成 embedding)
    memory_service = MemoryService()
    
    # 初始化政策
    logger.info("\n📋 Initializing policies...")
    await init_policies(memory_service)
    
    # 初始化 FAQ
    logger.info("\n❓ Initializing FAQs...")
    await init_faqs(memory_service)
    
    # 初始化产品
    logger.info("\n💼 Initializing Products...")
    await init_products(memory_service)
    
    logger.info("\n✅ Knowledge base initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
