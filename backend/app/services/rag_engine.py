"""
RAG Engine - Retrieval Augmented Generation

This is the core RAG engine that coordinates:
- Knowledge retrieval (KnowledgeRetriever)
- Rule evaluation (RuleEngine)
- Prompt construction and LLM generation

AI Coding Guidance:
- Use prompt_manager.render() for all prompts
- Fallback gracefully when knowledge is empty
- Include sources in response for traceability
"""

import logging
from typing import Any

from app.core.prompt_manager import prompt_manager
from app.models.knowledge import (
    KnowledgeChunk,
    RAGResponse,
    RuleResult,
)
from app.services.knowledge_retriever import get_knowledge_retriever
from app.services.rule_engine import get_rule_engine

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    RAG 核心引擎
    
    协调知识检索、规则引擎和 LLM 生成。
    使用 core/prompt_manager 管理 Prompt 模板。
    
    设计原则:
    - 有则增强，无则降级 (知识库空也能运行)
    - 规则优先 (政策硬约束优先于 LLM)
    - 来源可追溯 (返回引用的知识)
    """
    
    def __init__(self):
        self.retriever = get_knowledge_retriever()
        self.rule_engine = get_rule_engine()
    
    async def query(
        self, 
        question: str,
        user_context: dict | None = None,
        top_k: int = 5
    ) -> RAGResponse:
        """
        执行 RAG 查询
        
        Args:
            question: 用户问题
            user_context: 用户上下文 (profile, city, etc.)
            top_k: 检索知识数量
            
        Returns:
            RAGResponse 包含回答、来源和置信度
        """
        # 1. 检索相关知识
        knowledge = await self.retriever.search(
            query=question,
            top_k=top_k
        )
        logger.info(f"RAG retrieved {len(knowledge)} knowledge chunks")
        
        # 2. 应用规则引擎
        rules: list[RuleResult] = []
        if user_context:
            city = user_context.get("city", "")
            profile = user_context.get("profile", {})
            if city:
                rules = await self.rule_engine.evaluate(
                    user_profile=profile,
                    city=city
                )
                logger.info(f"RAG evaluated {len(rules)} rules, {sum(1 for r in rules if r.is_matched)} matched")
        
        # 3. 构建增强 Prompt
        prompt = self._build_prompt(
            question=question,
            knowledge=knowledge,
            rules=rules
        )
        
        # 4. 调用 LLM 生成
        from app.core.dependencies import get_llm_provider
        llm = get_llm_provider()
        
        try:
            answer = await llm.generate(
                [{"role": "user", "content": prompt}], 
                ""
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            answer = "抱歉，我暂时无法回答这个问题。请稍后再试。"
        
        # 5. 计算置信度
        confidence = self._calculate_confidence(knowledge, rules)
        
        return RAGResponse(
            answer=answer,
            sources=knowledge,
            rules_applied=[r for r in rules if r.is_matched],
            confidence=confidence
        )
    
    async def query_with_sources(
        self,
        question: str,
        user_context: dict | None = None,
        top_k: int = 5
    ) -> tuple[str, list[KnowledgeChunk]]:
        """
        便捷方法: 返回回答和来源
        
        Returns:
            (answer, sources) 元组
        """
        response = await self.query(question, user_context, top_k)
        return response.answer, response.sources
    
    def _build_prompt(
        self, 
        question: str,
        knowledge: list[KnowledgeChunk],
        rules: list[RuleResult]
    ) -> str:
        """
        使用 prompt_manager.render() 构建增强 Prompt
        
        根据知识是否命中选择不同的 Prompt 模板
        """
        # 格式化知识上下文
        if knowledge:
            knowledge_context = "\n\n".join([
                f"【{k.category}】{k.title}\n{k.content}"
                for k in knowledge
            ])
        else:
            knowledge_context = "无相关参考知识"
        
        # 格式化规则约束
        matched_rules = [r for r in rules if r.is_matched]
        if matched_rules:
            rule_constraints = "\n".join([
                f"- {r.constraint_text}" 
                for r in matched_rules
            ])
        else:
            rule_constraints = "无特殊政策约束"
        
        # 根据知识是否命中选择不同 Prompt 文件
        try:
            if knowledge:
                return prompt_manager.render(
                    category="rag",
                    filename="knowledge_query",
                    key="system_instruction",
                    knowledge_context=knowledge_context,
                    rule_constraints=rule_constraints,
                    question=question
                )
            else:
                return prompt_manager.render(
                    category="rag",
                    filename="no_knowledge_fallback",
                    key="system_instruction",
                    question=question
                )
        except FileNotFoundError as e:
            logger.warning(f"Prompt file not found, using fallback: {e}")
            return self._fallback_prompt(question, knowledge_context, rule_constraints)
    
    def _fallback_prompt(
        self,
        question: str,
        knowledge_context: str,
        rule_constraints: str
    ) -> str:
        """备用 Prompt (当 YAML 文件不存在时)"""
        return f"""你是一位专业的购房顾问。请基于以下参考知识回答用户问题。

## 参考知识
{knowledge_context}

## 政策约束
{rule_constraints}

## 用户问题
{question}

## 回答要求
1. 优先使用参考知识中的信息
2. 政策约束是硬性规定，必须遵守
3. 如果知识不足以回答，请明确说明
4. 语气亲切专业"""
    
    def _calculate_confidence(
        self,
        knowledge: list[KnowledgeChunk],
        rules: list[RuleResult]
    ) -> float:
        """
        计算回答置信度
        
        置信度基于:
        - 知识命中数量和相似度
        - 规则匹配情况
        """
        base = 0.5
        
        # 知识命中加分 (最多 +0.3)
        if knowledge:
            avg_score = sum(k.score for k in knowledge) / len(knowledge)
            # 按知识数量和质量加分
            knowledge_bonus = min(0.3, avg_score * 0.3 + len(knowledge) * 0.02)
            base += knowledge_bonus
        
        # 规则匹配加分 (最多 +0.15)
        if rules:
            matched_count = sum(1 for r in rules if r.is_matched)
            if matched_count > 0:
                base += min(0.15, matched_count * 0.05)
        
        return min(1.0, base)


# ============================================================================
# Singleton Factory
# ============================================================================

_rag_engine: RAGEngine | None = None


def get_rag_engine() -> RAGEngine:
    """获取 RAGEngine 单例"""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
