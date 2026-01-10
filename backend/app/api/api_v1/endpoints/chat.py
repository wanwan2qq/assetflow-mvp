"""
Chat WebSocket endpoints for real-time AI conversation
"""

import json
import logging
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)

from app.core.auth import get_current_user
from app.models.user import User
from app.services.auth import auth_service
from app.services.chat_agent import get_chat_agent

logger = logging.getLogger(__name__)
router = APIRouter()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected for user {user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_message(self, user_id: int, message: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


async def authenticate_websocket(token: str) -> User:
    """Authenticate WebSocket connection using JWT token"""
    try:
        from sqlmodel import select
        from app.core.database import get_db_session

        logger.info(f"WebSocket认证开始，Token: {token[:20]}...")
        
        try:
            user_id = auth_service.verify_token(token)
            logger.info(f"Token验证结果，用户ID: {user_id}")
        except Exception as e:
            logger.error(f"Token验证异常: {e}")
            user_id = None
        
        if user_id is None:
            logger.error("Token验证失败：无效或过期的token")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Get database session using async generator
        async for session in get_db_session():
            logger.info(f"数据库会话获取成功，查询用户ID: {user_id}")
            statement = select(User).where(User.id == user_id)
            result = await session.execute(statement)
            user = result.scalar_one_or_none()

            if user is None:
                logger.error(f"用户不存在：ID {user_id}")
                raise HTTPException(status_code=401, detail="User not found")
            
            logger.info(f"WebSocket认证成功：用户 {user.phone}")
            return user

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed") from e


@router.websocket("/ws/chat/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int, token: str = Query(...)):
    """WebSocket endpoint for real-time chat with AI agent"""

    try:
        # Authenticate user
        user = await authenticate_websocket(token)
        if user.id != user_id:
            await websocket.close(code=1008, reason="Unauthorized")
            return

        # Connect to WebSocket
        await manager.connect(websocket, user_id)

        # Get chat agent
        agent = get_chat_agent()

        # Send welcome message
        welcome_msg = {
            "type": "system",
            "content": "欢迎使用AssetFlow！我是您的AI资产配置顾问。请告诉我您的房产情况，我来帮您分析资产配置。",
            "timestamp": "2024-01-01T00:00:00Z",
        }
        try:
            await websocket.send_text(json.dumps(welcome_msg, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
            return

        # Handle messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                
                # Handle heartbeat messages
                if data.strip() == "ping":
                    try:
                        await websocket.send_text("pong")
                    except Exception as e:
                        logger.error(f"Failed to send pong: {e}")
                        break
                    continue
                elif data.strip() == "pong":
                    # Heartbeat response, ignore
                    continue
                
                message_data = json.loads(data)

                user_message = message_data.get("content", "")
                if not user_message.strip():
                    continue

                logger.info(f"Received message from user {user_id}: {user_message}")

                # Send typing indicator
                typing_msg = {
                    "type": "typing",
                    "content": "AI正在思考中...",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
                try:
                    await websocket.send_text(json.dumps(typing_msg, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"Failed to send typing indicator: {e}")
                    break

                # Process message with AI agent
                response_chunks = []
                async for chunk in agent.process_message(
                    user_message, user_id, None  # Don't pass user.profile to avoid lazy loading
                ):
                    if chunk.strip():
                        response_chunks.append(chunk)

                        # Send streaming chunk
                        chunk_msg = {
                            "type": "chunk",
                            "content": chunk,
                            "timestamp": "2024-01-01T00:00:00Z",
                        }
                        try:
                            await websocket.send_text(
                                json.dumps(chunk_msg, ensure_ascii=False)
                            )
                        except Exception as e:
                            logger.error(f"Failed to send chunk: {e}")
                            break

                # Send complete response
                full_response = "".join(response_chunks)

                # Extract UI components
                ui_components = agent.extract_ui_components(full_response)

                complete_msg = {
                    "type": "complete",
                    "content": full_response,
                    "ui_components": [comp.model_dump() for comp in ui_components],
                    "timestamp": "2024-01-01T00:00:00Z",
                }
                try:
                    await websocket.send_text(json.dumps(complete_msg, ensure_ascii=False))
                except Exception as e:
                    logger.error(f"Failed to send complete message: {e}")
                    break

            except json.JSONDecodeError:
                error_msg = {
                    "type": "error",
                    "content": "消息格式错误",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
                try:
                    await websocket.send_text(json.dumps(error_msg, ensure_ascii=False))
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
                    break

            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                error_msg = {
                    "type": "error",
                    "content": f"处理消息时出现错误：{str(e)}",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
                try:
                    await websocket.send_text(json.dumps(error_msg, ensure_ascii=False))
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {send_error}")
                    break

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass
        manager.disconnect(user_id)


@router.get("/chat/context/{user_id}")
async def get_chat_context(
    user_id: int, current_user: User = Depends(get_current_user)
):
    """Get current chat context for a user"""

    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    agent = get_chat_agent()
    context = agent.get_conversation_context(user_id)

    if not context:
        return {"message": "No active conversation"}

    return {
        "user_id": context.user_id,
        "current_stage": context.current_stage,
        "conversation_length": len(context.conversation_history),
        "extracted_assets": context.extracted_assets,
        "user_profile": context.user_profile,
    }


@router.delete("/chat/context/{user_id}")
async def clear_chat_context(
    user_id: int, current_user: User = Depends(get_current_user)
):
    """Clear chat context for a user"""

    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    agent = get_chat_agent()
    agent.clear_conversation_context(user_id)

    return {"message": "Chat context cleared"}


@router.post("/chat/message")
async def send_chat_message(
    message_data: dict[str, Any], current_user: User = Depends(get_current_user)
):
    """Send a single chat message (non-WebSocket alternative)"""

    user_message = message_data.get("message", "")
    if not user_message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    agent = get_chat_agent()

    # Collect response chunks
    response_chunks = []
    async for chunk in agent.process_message(
        user_message, current_user.id, current_user.profile
    ):
        response_chunks.append(chunk)

    full_response = "".join(response_chunks)
    ui_components = agent.extract_ui_components(full_response)

    return {
        "response": full_response,
        "ui_components": [comp.model_dump() for comp in ui_components],
        "timestamp": "2024-01-01T00:00:00Z",
    }
