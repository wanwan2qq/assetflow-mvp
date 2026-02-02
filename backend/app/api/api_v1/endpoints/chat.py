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
from app.services.chat_history_service import get_chat_history_service

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

        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "timestamp": "2024-01-01T00:00:00Z"
        }))

        # Get chat agent
        agent = get_chat_agent()

        # Check if user has chat history
        # Only send welcome message if no history exists to avoid spamming on reconnect
        from app.services.chat_history_service import get_chat_history_service
        chat_history_service = get_chat_history_service()
        # Check last 1 message to see if history exists
        history_exists = await chat_history_service.has_history(user_id)
        
        if not history_exists:
            # Send welcome message
            welcome_msg = {
                "type": "system",
                "content": """欢迎使用 AssetFlow！我是您的 AI 资产配置顾问 🤝。

我不仅仅是聊天机器人，我能为您提供深度的财富管理服务：\n\n
🏠 **房产评估**：结合实时市场数据，精准评估您的房产价值；\n
📊 **资产配置**：基于标准普尔四象限模型，诊断您的资金分布健康度；\n
🚀 **行动计划**：根据您的资产现状，生成专属的**财富增值与风控行动方案**。\n\n

我们可以先从了解您的资产情况开始，您目前持有房产、现金或其他投资吗？💡""",
                "timestamp": "2024-01-01T00:00:00Z",
            }
            try:
                # Ensure proper UTF-8 encoding for WebSocket messages
                welcome_json = json.dumps(welcome_msg, ensure_ascii=False)
                # Validate UTF-8 encoding before sending
                welcome_json.encode('utf-8')
                await websocket.send_text(welcome_json)
            except UnicodeEncodeError as e:
                logger.error(f"UTF-8 encoding error in welcome message: {e}")
                # Fallback with ASCII-safe message
                fallback_msg = {
                    "type": "system",
                    "content": "欢迎使用AssetFlow！我是您的AI资产配置顾问。",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
                await websocket.send_text(json.dumps(fallback_msg, ensure_ascii=True))
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
                    typing_json = json.dumps(typing_msg, ensure_ascii=False)
                    # Validate UTF-8 encoding before sending
                    typing_json.encode('utf-8')
                    await websocket.send_text(typing_json)
                except UnicodeEncodeError as e:
                    logger.error(f"UTF-8 encoding error in typing message: {e}")
                    # Fallback with ASCII-safe message
                    fallback_typing = {
                        "type": "typing",
                        "content": "AI正在思考中...",
                        "timestamp": "2024-01-01T00:00:00Z",
                    }
                    await websocket.send_text(json.dumps(fallback_typing, ensure_ascii=True))
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

                        # Send streaming chunk with UTF-8 validation
                        chunk_msg = {
                            "type": "chunk",
                            "content": chunk,
                            "timestamp": "2024-01-01T00:00:00Z",
                        }
                        try:
                            chunk_json = json.dumps(chunk_msg, ensure_ascii=False)
                            # Validate UTF-8 encoding before sending
                            chunk_json.encode('utf-8')
                            await websocket.send_text(chunk_json)
                        except UnicodeEncodeError as e:
                            logger.error(f"UTF-8 encoding error in chunk: {e}")
                            # Try to clean the chunk content
                            try:
                                # Remove problematic characters and retry
                                clean_chunk = chunk.encode('utf-8', errors='replace').decode('utf-8')
                                clean_msg = {
                                    "type": "chunk",
                                    "content": clean_chunk,
                                    "timestamp": "2024-01-01T00:00:00Z",
                                }
                                await websocket.send_text(json.dumps(clean_msg, ensure_ascii=False))
                            except Exception as clean_error:
                                logger.error(f"Failed to send cleaned chunk: {clean_error}")
                                # Skip this chunk to prevent connection break
                                continue
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
                    complete_json = json.dumps(complete_msg, ensure_ascii=False)
                    # Validate UTF-8 encoding before sending
                    complete_json.encode('utf-8')
                    await websocket.send_text(complete_json)
                except UnicodeEncodeError as e:
                    logger.error(f"UTF-8 encoding error in complete message: {e}")
                    # Try to clean the response content
                    try:
                        clean_response = full_response.encode('utf-8', errors='replace').decode('utf-8')
                        clean_msg = {
                            "type": "complete",
                            "content": clean_response,
                            "ui_components": [comp.model_dump() for comp in ui_components],
                            "timestamp": "2024-01-01T00:00:00Z",
                        }
                        await websocket.send_text(json.dumps(clean_msg, ensure_ascii=False))
                    except Exception as clean_error:
                        logger.error(f"Failed to send cleaned complete message: {clean_error}")
                        # Send minimal fallback message
                        fallback_msg = {
                            "type": "complete",
                            "content": "回复内容包含特殊字符，已自动处理。",
                            "ui_components": [],
                            "timestamp": "2024-01-01T00:00:00Z",
                        }
                        await websocket.send_text(json.dumps(fallback_msg, ensure_ascii=True))
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
                    error_json = json.dumps(error_msg, ensure_ascii=False)
                    # Validate UTF-8 encoding before sending
                    error_json.encode('utf-8')
                    await websocket.send_text(error_json)
                except UnicodeEncodeError as e:
                    logger.error(f"UTF-8 encoding error in error message: {e}")
                    await websocket.send_text(json.dumps(error_msg, ensure_ascii=True))
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
                    error_json = json.dumps(error_msg, ensure_ascii=False)
                    # Validate UTF-8 encoding before sending
                    error_json.encode('utf-8')
                    await websocket.send_text(error_json)
                except UnicodeEncodeError as e:
                    logger.error(f"UTF-8 encoding error in error message: {e}")
                    # Fallback with ASCII-safe message
                    fallback_error = {
                        "type": "error",
                        "content": "处理消息时出现错误",
                        "timestamp": "2024-01-01T00:00:00Z",
                    }
                    await websocket.send_text(json.dumps(fallback_error, ensure_ascii=True))
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


@router.get("/chat/history")
async def get_chat_history(
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_user)
):
    """Get chat history for the current user"""
    
    try:
        chat_history_service = get_chat_history_service()
        messages = await chat_history_service.get_chat_history(current_user.id, limit)
        
        # Convert messages to response format
        history = []
        for message in messages:
            history.append({
                "id": message.id,
                "role": message.role.value,
                "content": message.content,
                "meta_data": message.meta_data,
                "timestamp": message.timestamp.isoformat()
            })
        
        # Hydrate widgets with current asset data
        asset_ids = set()
        for msg in history:
            if not msg.get("meta_data") or not msg["meta_data"].get("widgets"):
                continue
                
            for widget in msg["meta_data"]["widgets"]:
                w_type = widget.get("widget_type")
                w_data = widget.get("data", {})
                if w_type in ["VALUATION_CARD", "ASSET_CARD"] and w_data.get("id"):
                    try:
                        asset_ids.add(int(w_data["id"]))
                    except (ValueError, TypeError):
                        pass

            # Fallback: Scan content for IDs if metadata is missing/incomplete
            # Look for id pattern in the data attribute string: &quot;id&quot;: 123 OR "id": 123
            if msg.get("content") and "<WIDGET:" in msg["content"]:
                import re
                # Match "id": 123 or &quot;id&quot;: 123
                # We handle both integer and string IDs, but only collect integers effectively 
                # (since our DB uses int IDs for assets)
                id_matches = re.finditer(r'(?:&quot;|")id(?:&quot;|")\s*:\s*(\d+)', msg["content"])
                for match in id_matches:
                    try:
                        asset_ids.add(int(match.group(1)))
                    except (ValueError, TypeError):
                        pass

        if asset_ids:
            try:
                from app.models.user import UserAsset
                from sqlmodel import select
                from app.core.database import get_db_session

                # We need a session to query
                async for session in get_db_session():
                    stmt = select(UserAsset).where(UserAsset.id.in_(asset_ids))
                    result = await session.execute(stmt)
                    current_assets = {asset.id: asset for asset in result.scalars().all()}
                    
                    # Update widget data in history
                    for msg in history:
                        if not msg.get("meta_data") or not msg["meta_data"].get("widgets"):
                            continue
                            
                        for widget in msg["meta_data"]["widgets"]:
                            w_type = widget.get("widget_type")
                            w_data = widget.get("data", {})
                            a_id = w_data.get("id")
                            
                            if a_id and int(a_id) in current_assets:
                                asset = current_assets[int(a_id)]
                                # Update fields
                                w_data["value"] = asset.value
                                w_data["price"] = asset.value # For ValuationCard compatibility
                                
                                # Update status based on confirmation
                                if asset.is_confirmed:
                                    w_data["status"] = "completed"
                                else:
                                    w_data["status"] = "active"
                                
                                if w_type == "VALUATION_CARD":
                                    # Update derived fields if possible (e.g. price per sqm)
                                    area = w_data.get("area", 0)
                                    if area and area > 0:
                                        w_data["price_per_sqm"] = asset.value / area
                                
                                # Update name/location if changed?
                                if asset.name:
                                    w_data["name"] = asset.name
                                if asset.extra_data and asset.extra_data.get("location"):
                                    w_data["location"] = asset.extra_data.get("location")
                    
                    break # Only need one session
            
                # Hydrate content strings with fresh data
                import re
                
                def match_replace(match):
                    try:
                        w_type = match.group(1)
                        raw_json = match.group(2).replace('&quot;', '"')
                        data = json.loads(raw_json)
                        
                        a_id = data.get("id")
                        if a_id and int(a_id) in current_assets:
                            asset = current_assets[int(a_id)]
                            
                            # Update key fields
                            data["value"] = asset.value
                            data["price"] = asset.value
                            data["status"] = "completed" if asset.is_confirmed else "active"
                            if asset.name:
                                data["name"] = asset.name
                                
                            # Update derived fields 
                            if w_type == "VALUATION_CARD":
                                area = data.get("area", 0)
                                if area and area > 0:
                                    data["price_per_sqm"] = asset.value / area
                                    
                            # Re-serialize
                            new_json = json.dumps(data, ensure_ascii=False, default=str)
                            escaped_json = new_json.replace('"', '&quot;')
                            return f'<WIDGET:{w_type} data="{escaped_json}" />'
                    except Exception:
                        pass
                    return match.group(0)

                for msg in history:
                    if msg.get("content") and "<WIDGET:" in msg["content"]:
                        # Match both /> and > endings
                        msg["content"] = re.sub(
                            r'<WIDGET:([A-Z_]+)\s+data="([^"]*)"(?:\s*/)?>', 
                            match_replace,
                            msg["content"]
                        )
            
            except Exception as e:
                logger.error(f"Error hydrating widgets: {e}")

        
        return {
            "messages": history,
            "total": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chat history")
