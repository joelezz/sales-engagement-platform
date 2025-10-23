from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.services.auth_service import AuthService
from app.services.websocket_manager import websocket_manager
from app.schemas.websocket import WebSocketMessage, WebSocketMessageType
from app.models.user import User

router = APIRouter(prefix="/ws", tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for real-time notifications"""
    connection_id = None
    
    try:
        # Authenticate user from token
        auth_service = AuthService(db)
        user_claims = await auth_service.validate_token(token)
        
        if not user_claims:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        user_id = int(user_claims.sub)
        tenant_id = user_claims.tenant_id
        
        # Establish WebSocket connection
        connection_id = await websocket_manager.connect(websocket, user_id, tenant_id)
        
        # Auto-subscribe to user-specific channels
        await websocket_manager.subscribe_to_channel(connection_id, f"user:{user_id}:notifications")
        await websocket_manager.subscribe_to_channel(connection_id, "tenant:broadcast")
        
        # Send any queued offline notifications
        from app.services.notification_service import NotificationService
        offline_notifications = await NotificationService.get_offline_notifications(user_id, tenant_id)
        
        if offline_notifications:
            for notification in offline_notifications:
                await websocket_manager._send_to_connection(
                    connection_id,
                    WebSocketMessage(
                        type=WebSocketMessageType.NOTIFICATION,
                        data={
                            "type": "offline_notification",
                            "data": notification
                        }
                    )
                )
        
        # Listen for messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle the message
                await websocket_manager.handle_message(connection_id, message_data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection_id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {connection_id}")
                await websocket_manager._send_error(
                    connection_id, 
                    "invalid_json", 
                    "Invalid JSON format"
                )
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket_manager._send_error(
                    connection_id,
                    "message_error",
                    str(e)
                )
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close(code=4000, reason="Connection error")
    
    finally:
        # Clean up connection
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@router.get("/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics"""
    return websocket_manager.get_connection_stats()


@router.get("/notifications/offline")
async def get_offline_notifications(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get offline notifications for current user"""
    from app.services.notification_service import NotificationService
    
    notifications = await NotificationService.get_offline_notifications(
        current_user.id, 
        current_user.tenant_id
    )
    
    return {
        "notifications": notifications,
        "count": len(notifications)
    }


@router.post("/broadcast/{tenant_id}")
async def broadcast_to_tenant(
    tenant_id: str,
    message: dict,
    # Add authentication here in production
):
    """Broadcast message to all connections in a tenant (admin only)"""
    from app.schemas.websocket import WebSocketNotification
    import uuid
    
    try:
        notification = WebSocketNotification(
            type="admin_broadcast",
            channel="tenant:broadcast",
            data=message,
            tenant_id=uuid.UUID(tenant_id)
        )
        
        await websocket_manager.send_to_tenant(uuid.UUID(tenant_id), notification)
        
        return {"status": "success", "message": "Broadcast sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )