from typing import Dict, Any, Optional, List
import uuid
import json
import logging
from datetime import datetime, timedelta

from app.core.redis import redis_client
from app.models.activity import Activity, ActivityType
from app.schemas.websocket import WebSocketNotification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for real-time notifications"""
    
    @staticmethod
    async def publish_activity_event(activity: Activity) -> None:
        """Publish real-time notification for new activity"""
        try:
            # Create notification
            notification = WebSocketNotification(
                type="activity_created",
                channel="activities",
                data={
                    "activity_id": activity.id,
                    "activity_type": activity.type.value,
                    "contact_id": activity.contact_id,
                    "user_id": activity.user_id,
                    "created_at": activity.created_at.isoformat(),
                    "payload": activity.payload,
                    "title": NotificationService._generate_activity_title(activity),
                    "description": NotificationService._generate_activity_description(activity)
                },
                user_id=activity.user_id,
                tenant_id=activity.tenant_id
            )
            
            # Publish to multiple channels
            channels = [
                "activities",
                f"contact:{activity.contact_id}:activities",
                f"user:{activity.user_id}:activities"
            ]
            
            for channel in channels:
                notification.channel = channel
                await redis_client.publish(
                    channel, 
                    notification.dict(), 
                    tenant_id=activity.tenant_id
                )
            
            logger.info(f"Published activity notification for activity {activity.id}")
            
        except Exception as e:
            logger.error(f"Error publishing activity notification: {e}")
    
    @staticmethod
    async def publish_call_event(call_data: Dict[str, Any], tenant_id: uuid.UUID) -> None:
        """Publish real-time notification for call events"""
        try:
            notification = WebSocketNotification(
                type="call_status_update",
                channel="calls",
                data=call_data,
                user_id=call_data.get("user_id"),
                tenant_id=tenant_id
            )
            
            # Publish to multiple channels
            channels = ["calls"]
            
            if "contact_id" in call_data:
                channels.append(f"contact:{call_data['contact_id']}:calls")
            
            if "user_id" in call_data:
                channels.append(f"user:{call_data['user_id']}:calls")
            
            for channel in channels:
                notification.channel = channel
                await redis_client.publish(
                    channel,
                    notification.dict(),
                    tenant_id=tenant_id
                )
            
            logger.info(f"Published call notification for call {call_data.get('call_sid')}")
            
        except Exception as e:
            logger.error(f"Error publishing call notification: {e}")
    
    @staticmethod
    async def publish_contact_event(contact_data: Dict[str, Any], tenant_id: uuid.UUID, event_type: str) -> None:
        """Publish real-time notification for contact events"""
        try:
            notification = WebSocketNotification(
                type=f"contact_{event_type}",
                channel="contacts",
                data=contact_data,
                tenant_id=tenant_id
            )
            
            # Publish to multiple channels
            channels = [
                "contacts",
                f"contact:{contact_data.get('id')}:updates"
            ]
            
            for channel in channels:
                notification.channel = channel
                await redis_client.publish(
                    channel,
                    notification.dict(),
                    tenant_id=tenant_id
                )
            
            logger.info(f"Published contact {event_type} notification for contact {contact_data.get('id')}")
            
        except Exception as e:
            logger.error(f"Error publishing contact notification: {e}")
    
    @staticmethod
    async def send_user_notification(
        user_id: int, 
        notification_data: Dict[str, Any], 
        tenant_id: uuid.UUID,
        notification_type: str = "user_notification"
    ) -> None:
        """Send notification to specific user"""
        try:
            notification = WebSocketNotification(
                type=notification_type,
                channel=f"user:{user_id}:notifications",
                data=notification_data,
                user_id=user_id,
                tenant_id=tenant_id
            )
            
            await redis_client.publish(
                notification.channel,
                notification.dict(),
                tenant_id=tenant_id
            )
            
            logger.info(f"Sent notification to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error sending user notification: {e}")
    
    @staticmethod
    async def broadcast_to_tenant(
        notification_data: Dict[str, Any], 
        tenant_id: uuid.UUID,
        notification_type: str = "tenant_broadcast"
    ) -> None:
        """Broadcast notification to all users in tenant"""
        try:
            notification = WebSocketNotification(
                type=notification_type,
                channel="tenant:broadcast",
                data=notification_data,
                tenant_id=tenant_id
            )
            
            await redis_client.publish(
                notification.channel,
                notification.dict(),
                tenant_id=tenant_id
            )
            
            logger.info(f"Broadcasted notification to tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting notification: {e}")
    
    @staticmethod
    def _generate_activity_title(activity: Activity) -> str:
        """Generate activity title for notifications"""
        activity_type = activity.type
        payload = activity.payload
        
        if activity_type == ActivityType.CALL:
            direction = payload.get('direction', 'outbound')
            duration = payload.get('duration', 0)
            if duration:
                return f"{direction.title()} call ({duration}s)"
            else:
                return f"{direction.title()} call"
        
        elif activity_type == ActivityType.EMAIL:
            subject = payload.get('subject', 'Email')
            return f"Email: {subject}"
        
        elif activity_type == ActivityType.SMS:
            return "SMS message"
        
        elif activity_type == ActivityType.NOTE:
            return payload.get('title', 'Note')
        
        elif activity_type == ActivityType.MEETING:
            return payload.get('title', 'Meeting')
        
        return f"{activity_type.value.title()} activity"
    
    @staticmethod
    def _generate_activity_description(activity: Activity) -> str:
        """Generate activity description for notifications"""
        activity_type = activity.type
        payload = activity.payload
        
        if activity_type == ActivityType.CALL:
            from_num = payload.get('from_number', '')
            to_num = payload.get('to_number', '')
            return f"Call from {from_num} to {to_num}"
        
        elif activity_type == ActivityType.EMAIL:
            return payload.get('preview', payload.get('body', ''))[:100]
        
        elif activity_type == ActivityType.SMS:
            return payload.get('message', '')[:100]
        
        elif activity_type == ActivityType.NOTE:
            return payload.get('content', '')[:100]
        
        elif activity_type == ActivityType.MEETING:
            return payload.get('description', '')[:100]
        
        return ""
    
    @staticmethod
    async def queue_offline_notification(
        user_id: int,
        notification_data: Dict[str, Any],
        tenant_id: uuid.UUID,
        ttl_hours: int = 24
    ) -> None:
        """Queue notification for offline users"""
        try:
            # Store notification in Redis with TTL
            key = f"offline_notifications:{user_id}"
            notification_with_timestamp = {
                **notification_data,
                "queued_at": datetime.utcnow().isoformat(),
                "tenant_id": str(tenant_id)
            }
            
            # Add to list of offline notifications
            await redis_client.redis.lpush(key, json.dumps(notification_with_timestamp))
            await redis_client.redis.expire(key, ttl_hours * 3600)
            
            logger.info(f"Queued offline notification for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error queuing offline notification: {e}")
    
    @staticmethod
    async def get_offline_notifications(user_id: int, tenant_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get queued notifications for user"""
        try:
            key = f"offline_notifications:{user_id}"
            
            # Get all notifications
            notifications_raw = await redis_client.redis.lrange(key, 0, -1)
            notifications = []
            
            for notification_raw in notifications_raw:
                try:
                    notification = json.loads(notification_raw)
                    # Verify tenant matches
                    if notification.get("tenant_id") == str(tenant_id):
                        notifications.append(notification)
                except json.JSONDecodeError:
                    continue
            
            # Clear the queue
            await redis_client.redis.delete(key)
            
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting offline notifications: {e}")
            return []