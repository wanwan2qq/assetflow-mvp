
import logging
import json
import re
from typing import List

from app.core.prompt_manager import prompt_manager
from app.core.dependencies import get_llm_provider
from app.models.intent import IntentType, IntentResult
from app.models.chat import ChatMessage

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Service for classifying user intent from conversation.
    
    Uses a hybrid approach:
    1. Fast path: Keyword/Regex matching for obvious cases
    2. Smart path: LLM-based classification for nuance
    """
    
    def __init__(self):
        self.llm = get_llm_provider()
        
    async def classify(
        self, 
        message: str, 
        history: List[ChatMessage]
    ) -> IntentResult:
        """
        Classify the intent of the latest user message.
        """
        # 1. Fast Path: Check for obvious keywords
        fast_result = self._fast_classify(message)
        if fast_result:
            logger.debug(f"⚡️ Fast intent classification: {fast_result.intent_type}")
            return fast_result
            
        # 2. Smart Path: LLM Classification
        return await self._smart_classify(message, history)

    def _fast_classify(self, message: str) -> IntentResult | None:
        """Rule-based fast classification."""
        msg_lower = message.lower()
        
        # Policy/Rules keywords
        policy_keywords = ["政策", "限购", "首付", "利率", "资格", "怎么买", "能买吗", "税费"]
        if any(k in msg_lower for k in policy_keywords):
            return IntentResult(
                intent_type=IntentType.POLICY_QUERY,
                confidence=0.8,
                reasoning="Keyword match"
            )
            
        # Action keywords
        action_keywords = ["生成报告", "修改估值", "重新分析", "更新图表"]
        if any(k in msg_lower for k in action_keywords):
            return IntentResult(
                intent_type=IntentType.ACTION_REQUEST,
                confidence=0.9,
                reasoning="Keyword match"
            )
            
        return None

    async def _smart_classify(
        self, 
        message: str, 
        history: List[ChatMessage]
    ) -> IntentResult:
        """LLM-based classification."""
        try:
            # Build context string from recent history (last 2 turns)
            # history is usually chronological, we take the last few
            recent_context = ""
            if history:
                # Take up to last 4 messages (2 turns) excluding the current one if it's there
                relevant_msgs = history[-4:]
                conversation_text = []
                for msg in relevant_msgs:
                    role = "User" if msg.role == "user" else "AI"
                    conversation_text.append(f"{role}: {msg.content}")
                recent_context = "\n".join(conversation_text)

            prompt = f"""
            You are an intent classifier for a financial advisory AI.
            Analyze the user's latest message and classify their intent.
            
            INTENT CATEGORIES:
            1. info_collection: User is providing personal info, assets, income, or correcting data.
            2. policy_query: Asking about housing policies, rules, taxes, eligibility.
            3. advisory: Asking for advice, analysis, "what should I do", or expressing concerns.
            4. chit_chat: Greetings, simple confirmations ("ok", "thanks"), or meta-talk.
            5. action_request: Asking to perform a specific system action (generate report, update value).
            
            RECENT CONTEXT:
            {recent_context}
            
            LATEST USER MESSAGE:
            "{message}"
            
            OUTPUT FORMAT (JSON ONLY):
            {{
                "intent": "category_name",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation"
            }}
            """
            
            # Call LLM with low temperature for stability
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a precise classification engine. Output JSON only.",
                temperature=0.1
            )
            
            # Parse JSON
            # Handle potential markdown code blocks
            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            data = json.loads(clean_response)
            
            return IntentResult(
                intent_type=IntentType(data.get("intent", "chit_chat")),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "")
            )
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback to chit_chat or advisory depending on length
            if len(message) > 20:
                return IntentResult(intent_type=IntentType.ADVISORY, confidence=0.3, reasoning="Fallback")
            return IntentResult(intent_type=IntentType.CHIT_CHAT, confidence=0.3, reasoning="Fallback")

# Singleton
_intent_classifier: IntentClassifier | None = None

def get_intent_classifier() -> IntentClassifier:
    global _intent_classifier
    if _intent_classifier is None:
        _intent_classifier = IntentClassifier()
    return _intent_classifier
