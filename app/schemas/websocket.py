from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
from enum import Enum


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    NOTIFICATION = "notification"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    ACK = "ack"


class WebSocketMessage(BaseModel):
    """Base WebSocket message schema"""
    type: WebSocketMessageType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_id: Optional[str] = None


class WebSocketSubscription(BaseModel):
    """WebSocket subscription schema"""
    channel: str = Field(..., description="Channel to subscribe to")
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional filters")


class WebSocketNotification(BaseModel):
    """WebSocket notification schema"""
    type: str = Field(..., description="Notification type")
    channel: str = Field(..., description="Channel the notification is for")
    data: Dict[str, Any] = Field(..., description="Notification payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[int] = None
    tenant_id: Optional[uuid.UUID] = None


class ConnectionInfo(BaseModel):
    """WebSocket connection information"""
    connection_id: str
    user_id: int
    tenant_id: uuid.UUID
    connected_at: datetime
    last_heartbeat: datetime
    subscriptions: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class WebSocketError(BaseModel):
    """WebSocket error message"""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None