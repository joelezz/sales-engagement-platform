import redis.asyncio as redis
from app.core.config import settings
from typing import Optional
import json
import uuid


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Initialize Redis connection"""
        self.redis = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    def _get_tenant_key(self, tenant_id: uuid.UUID, key: str) -> str:
        """Generate tenant-specific Redis key"""
        return f"tenant:{tenant_id}:{key}"
    
    async def get(self, key: str, tenant_id: Optional[uuid.UUID] = None) -> Optional[str]:
        """Get value from Redis with optional tenant isolation"""
        if tenant_id:
            key = self._get_tenant_key(tenant_id, key)
        return await self.redis.get(key)
    
    async def set(
        self, 
        key: str, 
        value: str, 
        tenant_id: Optional[uuid.UUID] = None,
        ttl: Optional[int] = None
    ):
        """Set value in Redis with optional tenant isolation and TTL"""
        if tenant_id:
            key = self._get_tenant_key(tenant_id, key)
        
        if ttl:
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)
    
    async def delete(self, key: str, tenant_id: Optional[uuid.UUID] = None):
        """Delete key from Redis with optional tenant isolation"""
        if tenant_id:
            key = self._get_tenant_key(tenant_id, key)
        await self.redis.delete(key)
    
    async def publish(self, channel: str, message: dict, tenant_id: Optional[uuid.UUID] = None):
        """Publish message to Redis channel with optional tenant isolation"""
        if tenant_id:
            channel = self._get_tenant_key(tenant_id, channel)
        await self.redis.publish(channel, json.dumps(message))
    
    async def subscribe(self, channel: str, tenant_id: Optional[uuid.UUID] = None):
        """Subscribe to Redis channel with optional tenant isolation"""
        if tenant_id:
            channel = self._get_tenant_key(tenant_id, channel)
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Global Redis client instance
redis_client = RedisClient()