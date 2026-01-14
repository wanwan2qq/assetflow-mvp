"""
Chat history persistence service
"""

import json
import logging
import re
from datetime import datetime
from typing import Any

from sqlmodel import select

from app.core.database import get_db_session
from app.models.chat import ChatMessage, MessageRole

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """Service for managing chat message persistence"""

    async def save_user_message(self, user_id: int, content: str) -> ChatMessage:
        """Save a user message to the database"""
        try:
            async for session in get_db_session():
                message = ChatMessage(
                    user_id=user_id,
                    role=MessageRole.USER,
                    content=content,
                    meta_data=None,  # User messages typically don't have widget data
                    timestamp=datetime.utcnow()
                )
                
                session.add(message)
                await session.commit()
                await session.refresh(message)
                
                logger.info(f"Saved user message for user {user_id}")
                return message
                
        except Exception as e:
            logger.error(f"Error saving user message: {e}")
            raise

    async def save_ai_message(self, user_id: int, content: str) -> ChatMessage:
        """Save an AI message to the database, extracting widget data if present"""
        try:
            # Extract widget data from content
            meta_data = self._extract_widget_metadata(content)
            
            async for session in get_db_session():
                message = ChatMessage(
                    user_id=user_id,
                    role=MessageRole.AI,
                    content=content,
                    meta_data=meta_data,
                    timestamp=datetime.utcnow()
                )
                
                session.add(message)
                await session.commit()
                await session.refresh(message)
                
                logger.info(f"Saved AI message for user {user_id} with meta_data: {bool(meta_data)}")
                return message
                
        except Exception as e:
            logger.error(f"Error saving AI message: {e}")
            raise

    async def get_chat_history(self, user_id: int, limit: int = 50) -> list[ChatMessage]:
        """Get chat history for a user, ordered by timestamp (newest first)"""
        try:
            async for session in get_db_session():
                statement = (
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user_id)
                    .order_by(ChatMessage.timestamp.desc())
                    .limit(limit)
                )
                
                result = await session.execute(statement)
                messages = result.scalars().all()
                
                # Return in chronological order (oldest first) for conversation display
                return list(reversed(messages))
                
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            raise

    def _extract_widget_metadata(self, content: str) -> dict[str, Any] | None:
        """Extract widget data from AI response content"""
        try:
            # Pattern to match <WIDGET:TYPE data='...'>
            widget_pattern = r'<WIDGET:(\w+)\s+data=\'([^\']+)\'>'
            matches = re.findall(widget_pattern, content)
            
            # Also try pattern with double quotes
            if not matches:
                widget_pattern = r'<WIDGET:(\w+)\s+data="([^"]+)">'
                matches = re.findall(widget_pattern, content)
            
            if not matches:
                return None
            
            widgets = []
            for widget_type, data_str in matches:
                try:
                    # Parse the data string as JSON
                    widget_data = json.loads(data_str)
                    
                    widgets.append({
                        "widget_type": widget_type,
                        "data": widget_data
                    })
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse widget data: {data_str}, error: {e}")
                    continue
            
            return {"widgets": widgets} if widgets else None
            
        except Exception as e:
            logger.error(f"Error extracting widget metadata: {e}")
            return None


# Global service instance
chat_history_service = ChatHistoryService()


def get_chat_history_service() -> ChatHistoryService:
    """Get chat history service instance"""
    return chat_history_service