from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime, timedelta
import asyncio
import json
import logging
import uuid
from collections import defaultdict

from app.core.redis import redis_client
from app.schemas.websocket import (
    WebSocketMessage,
    WebSocketMessageType,
    WebSocketNotification,
    ConnectionInfo,
    WebSocketError
)

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections and real-time notifications"""
    
    def __init__(self):
        # Active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Connection info: {connection_id: ConnectionInfo}
        self.connection_info: Dict[str, ConnectionInfo] = {}
        
        # User connections: {user_id: Set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)
        
        # Tenant connections: {tenant_id: Set[connection_id]}
        self.tenant_connections: Dict[uuid.UUID, Set[str]] = defaultdict(set)
        
        # Channel subscriptions: {channel: Set[connection_id]}
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        
        # Redis subscription tasks
        self.redis_tasks: Dict[str, asyncio.Task] = {}
        
        # Heartbeat task
        self.heartbeat_task: Optional[asyncio.Task] = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure background tasks are started"""
        if not self._initialized:
            try:
                if not self.heartbeat_task or self.heartbeat_task.done():
                    self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
                self._initialized = True
            except RuntimeError:
                # No event loop running, will initialize later
                pass
    
    async def connect(
        self, 
        websocket: WebSocket, 
        user_id: int, 
        tenant_id: uuid.UUID
    ) -> str:
        await self._ensure_initialized()
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        # Generate unique connection ID
        connection_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Store connection
        self.active_connections[connection_id] = websocket
        
        # Create connection info
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            user_id=user_id,
            tenant_id=tenant_id,
            connected_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow()
        )
        self.connection_info[connection_id] = connection_info
        
        # Add to user and tenant mappings
        self.user_connections[user_id].add(connection_id)
        self.tenant_connections[tenant_id].add(connection_id)
        
        # Store connection info in Redis for persistence
        await self._store_connection_in_redis(connection_info)
        
        # Send connection confirmation
        await self._send_to_connection(connection_id, WebSocketMessage(
            type=WebSocketMessageType.CONNECT,
            data={
                "connection_id": connection_id,
                "user_id": user_id,
                "tenant_id": str(tenant_id),
                "status": "connected"
            }
        ))
        
        logger.info(f"WebSocket connected: {connection_id} (user: {user_id}, tenant: {tenant_id})")
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection"""
        if connection_id not in self.active_connections:
            return
        
        connection_info = self.connection_info.get(connection_id)
        if connection_info:
            # Remove from user and tenant mappings
            self.user_connections[connection_info.user_id].discard(connection_id)
            self.tenant_connections[connection_info.tenant_id].discard(connection_id)
            
            # Remove from channel subscriptions
            for channel in connection_info.subscriptions:
                self.channel_subscriptions[channel].discard(connection_id)
            
            # Clean up empty sets
            if not self.user_connections[connection_info.user_id]:
                del self.user_connections[connection_info.user_id]
            if not self.tenant_connections[connection_info.tenant_id]:
                del self.tenant_connections[connection_info.tenant_id]
        
        # Remove connection
        del self.active_connections[connection_id]
        if connection_id in self.connection_info:
            del self.connection_info[connection_id]
        
        # Remove from Redis
        await self._remove_connection_from_redis(connection_id)
        
        logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def subscribe_to_channel(self, connection_id: str, channel: str):
        """Subscribe a connection to a channel"""
        if connection_id not in self.connection_info:
            return False
        
        # Add to channel subscriptions
        self.channel_subscriptions[channel].add(connection_id)
        self.connection_info[connection_id].subscriptions.append(channel)
        
        # Start Redis subscription for this channel if not already active
        await self._ensure_redis_subscription(channel)
        
        # Send subscription confirmation
        await self._send_to_connection(connection_id, WebSocketMessage(
            type=WebSocketMessageType.ACK,
            data={
                "action": "subscribe",
                "channel": channel,
                "status": "success"
            }
        ))
        
        logger.info(f"Connection {connection_id} subscribed to channel: {channel}")
        return True
    
    async def unsubscribe_from_channel(self, connection_id: str, channel: str):
        """Unsubscribe a connection from a channel"""
        if connection_id not in self.connection_info:
            return False
        
        # Remove from channel subscriptions
        self.channel_subscriptions[channel].discard(connection_id)
        if channel in self.connection_info[connection_id].subscriptions:
            self.connection_info[connection_id].subscriptions.remove(channel)
        
        # Stop Redis subscription if no more connections
        if not self.channel_subscriptions[channel]:
            await self._stop_redis_subscription(channel)
            del self.channel_subscriptions[channel]
        
        # Send unsubscription confirmation
        await self._send_to_connection(connection_id, WebSocketMessage(
            type=WebSocketMessageType.ACK,
            data={
                "action": "unsubscribe",
                "channel": channel,
                "status": "success"
            }
        ))
        
        logger.info(f"Connection {connection_id} unsubscribed from channel: {channel}")
        return True
    
    async def send_to_user(self, user_id: int, notification: WebSocketNotification):
        """Send notification to all connections of a specific user"""
        connection_ids = self.user_connections.get(user_id, set())
        
        message = WebSocketMessage(
            type=WebSocketMessageType.NOTIFICATION,
            data=notification.dict()
        )
        
        for connection_id in connection_ids.copy():  # Copy to avoid modification during iteration
            await self._send_to_connection(connection_id, message)
    
    async def send_to_tenant(self, tenant_id: uuid.UUID, notification: WebSocketNotification):
        """Send notification to all connections in a tenant"""
        connection_ids = self.tenant_connections.get(tenant_id, set())
        
        message = WebSocketMessage(
            type=WebSocketMessageType.NOTIFICATION,
            data=notification.dict()
        )
        
        for connection_id in connection_ids.copy():
            await self._send_to_connection(connection_id, message)
    
    async def send_to_channel(self, channel: str, notification: WebSocketNotification):
        """Send notification to all connections subscribed to a channel"""
        connection_ids = self.channel_subscriptions.get(channel, set())
        
        message = WebSocketMessage(
            type=WebSocketMessageType.NOTIFICATION,
            data=notification.dict()
        )
        
        for connection_id in connection_ids.copy():
            await self._send_to_connection(connection_id, message)
    
    async def handle_message(self, connection_id: str, message_data: dict):
        """Handle incoming WebSocket message"""
        try:
            message = WebSocketMessage(**message_data)
            
            if message.type == WebSocketMessageType.SUBSCRIBE:
                channel = message.data.get("channel")
                if channel:
                    await self.subscribe_to_channel(connection_id, channel)
            
            elif message.type == WebSocketMessageType.UNSUBSCRIBE:
                channel = message.data.get("channel")
                if channel:
                    await self.unsubscribe_from_channel(connection_id, channel)
            
            elif message.type == WebSocketMessageType.HEARTBEAT:
                await self._handle_heartbeat(connection_id)
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await self._send_error(connection_id, "message_error", str(e))
    
    async def _send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to a specific connection"""
        websocket = self.active_connections.get(connection_id)
        if not websocket:
            return False
        
        try:
            await websocket.send_text(message.json())
            return True
        except Exception as e:
            logger.error(f"Error sending to connection {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False
    
    async def _send_error(self, connection_id: str, error_code: str, message: str):
        """Send error message to connection"""
        error_msg = WebSocketMessage(
            type=WebSocketMessageType.ERROR,
            data=WebSocketError(
                error_code=error_code,
                message=message
            ).dict()
        )
        await self._send_to_connection(connection_id, error_msg)
    
    async def _handle_heartbeat(self, connection_id: str):
        """Handle heartbeat from connection"""
        if connection_id in self.connection_info:
            self.connection_info[connection_id].last_heartbeat = datetime.utcnow()
            
            # Send heartbeat response
            await self._send_to_connection(connection_id, WebSocketMessage(
                type=WebSocketMessageType.HEARTBEAT,
                data={"status": "alive"}
            ))
    
    async def _heartbeat_monitor(self):
        """Monitor connections for heartbeat timeouts"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                timeout_threshold = datetime.utcnow() - timedelta(minutes=2)
                disconnected_connections = []
                
                for connection_id, info in self.connection_info.items():
                    if info.last_heartbeat < timeout_threshold:
                        disconnected_connections.append(connection_id)
                
                # Disconnect timed-out connections
                for connection_id in disconnected_connections:
                    logger.warning(f"Connection {connection_id} timed out")
                    await self.disconnect(connection_id)
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
    
    async def _ensure_redis_subscription(self, channel: str):
        """Ensure Redis subscription is active for channel"""
        if channel not in self.redis_tasks or self.redis_tasks[channel].done():
            self.redis_tasks[channel] = asyncio.create_task(
                self._redis_subscription_handler(channel)
            )
    
    async def _stop_redis_subscription(self, channel: str):
        """Stop Redis subscription for channel"""
        if channel in self.redis_tasks:
            self.redis_tasks[channel].cancel()
            del self.redis_tasks[channel]
    
    async def _redis_subscription_handler(self, channel: str):
        """Handle Redis pub/sub messages for a channel"""
        try:
            # Subscribe to Redis channel
            pubsub = await redis_client.subscribe(channel)
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Parse notification
                        notification_data = json.loads(message['data'])
                        notification = WebSocketNotification(**notification_data)
                        
                        # Send to all subscribed connections
                        await self.send_to_channel(channel, notification)
                        
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {e}")
            
        except Exception as e:
            logger.error(f"Error in Redis subscription handler for {channel}: {e}")
        finally:
            if channel in self.redis_tasks:
                del self.redis_tasks[channel]
    
    async def _store_connection_in_redis(self, connection_info: ConnectionInfo):
        """Store connection info in Redis for persistence"""
        try:
            key = f"ws_connection:{connection_info.connection_id}"
            await redis_client.set(
                key,
                connection_info.json(),
                tenant_id=connection_info.tenant_id,
                ttl=3600  # 1 hour TTL
            )
        except Exception as e:
            logger.error(f"Error storing connection in Redis: {e}")
    
    async def _remove_connection_from_redis(self, connection_id: str):
        """Remove connection info from Redis"""
        try:
            key = f"ws_connection:{connection_id}"
            # We need tenant_id to delete, but connection might be gone
            # This is a limitation - in production you'd want a global cleanup
            await redis_client.redis.delete(key)
        except Exception as e:
            logger.error(f"Error removing connection from Redis: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "users_connected": len(self.user_connections),
            "tenants_active": len(self.tenant_connections),
            "active_channels": len(self.channel_subscriptions),
            "redis_subscriptions": len(self.redis_tasks)
        }


# Global WebSocket manager instance
websocket_manager = WebSocketConnectionManager()