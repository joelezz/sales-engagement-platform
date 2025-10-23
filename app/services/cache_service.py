from typing import Any, Optional, Dict, List, Union
import json
import uuid
import hashlib
from datetime import datetime, timedelta
import logging

from app.core.redis import redis_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching frequently accessed data"""
    
    def __init__(self):
        self.default_ttl = settings.redis_cache_ttl
    
    def _generate_cache_key(self, prefix: str, identifier: str, tenant_id: Optional[uuid.UUID] = None) -> str:
        """Generate a cache key with optional tenant isolation"""
        if tenant_id:
            return f"cache:{tenant_id}:{prefix}:{identifier}"
        return f"cache:global:{prefix}:{identifier}"
    
    def _hash_complex_key(self, data: Dict[str, Any]) -> str:
        """Generate hash for complex cache keys"""
        # Sort the dictionary to ensure consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    async def get(self, key: str, tenant_id: Optional[uuid.UUID] = None) -> Optional[Any]:
        """Get cached value"""
        try:
            cache_key = self._generate_cache_key("data", key, tenant_id)
            cached_value = await redis_client.get(cache_key, tenant_id=tenant_id)
            
            if cached_value:
                return json.loads(cached_value)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        tenant_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Set cached value"""
        try:
            cache_key = self._generate_cache_key("data", key, tenant_id)
            serialized_value = json.dumps(value, default=str)
            
            await redis_client.set(
                cache_key,
                serialized_value,
                tenant_id=tenant_id,
                ttl=ttl or self.default_ttl
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str, tenant_id: Optional[uuid.UUID] = None) -> bool:
        """Delete cached value"""
        try:
            cache_key = self._generate_cache_key("data", key, tenant_id)
            await redis_client.delete(cache_key, tenant_id=tenant_id)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def get_or_set(
        self,
        key: str,
        fetch_function,
        ttl: Optional[int] = None,
        tenant_id: Optional[uuid.UUID] = None,
        *args,
        **kwargs
    ) -> Any:
        """Get cached value or fetch and cache if not exists"""
        try:
            # Try to get from cache first
            cached_value = await self.get(key, tenant_id)
            if cached_value is not None:
                return cached_value
            
            # Fetch fresh data
            fresh_value = await fetch_function(*args, **kwargs)
            
            # Cache the fresh data
            if fresh_value is not None:
                await self.set(key, fresh_value, ttl, tenant_id)
            
            return fresh_value
            
        except Exception as e:
            logger.error(f"Cache get_or_set error: {e}")
            # Return fresh data even if caching fails
            try:
                return await fetch_function(*args, **kwargs)
            except Exception as fetch_error:
                logger.error(f"Fetch function error: {fetch_error}")
                return None
    
    async def invalidate_pattern(self, pattern: str, tenant_id: Optional[uuid.UUID] = None) -> int:
        """Invalidate all cache keys matching a pattern"""
        try:
            if tenant_id:
                search_pattern = f"cache:{tenant_id}:*{pattern}*"
            else:
                search_pattern = f"cache:*{pattern}*"
            
            # Note: This is a simplified implementation
            # In production, you might want to use Redis SCAN for better performance
            keys = await redis_client.redis.keys(search_pattern)
            
            if keys:
                deleted_count = await redis_client.redis.delete(*keys)
                logger.info(f"Invalidated {deleted_count} cache keys matching pattern: {pattern}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error: {e}")
            return 0
    
    # Specific caching methods for common use cases
    
    async def cache_contact(self, contact_id: int, contact_data: Dict[str, Any], tenant_id: uuid.UUID) -> bool:
        """Cache contact data"""
        key = f"contact:{contact_id}"
        return await self.set(key, contact_data, ttl=1800, tenant_id=tenant_id)  # 30 minutes
    
    async def get_cached_contact(self, contact_id: int, tenant_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get cached contact data"""
        key = f"contact:{contact_id}"
        return await self.get(key, tenant_id=tenant_id)
    
    async def invalidate_contact_cache(self, contact_id: int, tenant_id: uuid.UUID) -> bool:
        """Invalidate contact cache"""
        key = f"contact:{contact_id}"
        return await self.delete(key, tenant_id=tenant_id)
    
    async def cache_user_profile(self, user_id: int, user_data: Dict[str, Any], tenant_id: uuid.UUID) -> bool:
        """Cache user profile data"""
        key = f"user_profile:{user_id}"
        return await self.set(key, user_data, ttl=3600, tenant_id=tenant_id)  # 1 hour
    
    async def get_cached_user_profile(self, user_id: int, tenant_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get cached user profile"""
        key = f"user_profile:{user_id}"
        return await self.get(key, tenant_id=tenant_id)
    
    async def cache_activity_timeline(
        self, 
        contact_id: int, 
        page: int, 
        timeline_data: Dict[str, Any], 
        tenant_id: uuid.UUID
    ) -> bool:
        """Cache activity timeline data"""
        key = f"timeline:{contact_id}:page:{page}"
        return await self.set(key, timeline_data, ttl=300, tenant_id=tenant_id)  # 5 minutes
    
    async def get_cached_activity_timeline(
        self, 
        contact_id: int, 
        page: int, 
        tenant_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Get cached activity timeline"""
        key = f"timeline:{contact_id}:page:{page}"
        return await self.get(key, tenant_id=tenant_id)
    
    async def invalidate_activity_timeline_cache(self, contact_id: int, tenant_id: uuid.UUID) -> int:
        """Invalidate all timeline cache for a contact"""
        pattern = f"timeline:{contact_id}:"
        return await self.invalidate_pattern(pattern, tenant_id=tenant_id)
    
    async def cache_search_results(
        self, 
        search_query: str, 
        search_type: str,
        results: List[Dict[str, Any]], 
        tenant_id: uuid.UUID
    ) -> bool:
        """Cache search results"""
        query_hash = self._hash_complex_key({"query": search_query, "type": search_type})
        key = f"search:{search_type}:{query_hash}"
        return await self.set(key, results, ttl=600, tenant_id=tenant_id)  # 10 minutes
    
    async def get_cached_search_results(
        self, 
        search_query: str, 
        search_type: str,
        tenant_id: uuid.UUID
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results"""
        query_hash = self._hash_complex_key({"query": search_query, "type": search_type})
        key = f"search:{search_type}:{query_hash}"
        return await self.get(key, tenant_id=tenant_id)
    
    async def cache_statistics(
        self, 
        stat_type: str, 
        stat_data: Dict[str, Any], 
        tenant_id: uuid.UUID,
        ttl: int = 1800
    ) -> bool:
        """Cache statistics data"""
        key = f"stats:{stat_type}"
        return await self.set(key, stat_data, ttl=ttl, tenant_id=tenant_id)
    
    async def get_cached_statistics(self, stat_type: str, tenant_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get cached statistics"""
        key = f"stats:{stat_type}"
        return await self.get(key, tenant_id=tenant_id)
    
    async def cache_call_history(
        self, 
        filters_hash: str, 
        call_data: Dict[str, Any], 
        tenant_id: uuid.UUID
    ) -> bool:
        """Cache call history data"""
        key = f"call_history:{filters_hash}"
        return await self.set(key, call_data, ttl=300, tenant_id=tenant_id)  # 5 minutes
    
    async def get_cached_call_history(self, filters_hash: str, tenant_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """Get cached call history"""
        key = f"call_history:{filters_hash}"
        return await self.get(key, tenant_id=tenant_id)
    
    async def warm_cache_for_tenant(self, tenant_id: uuid.UUID) -> Dict[str, int]:
        """Warm up cache with frequently accessed data for a tenant"""
        warmed_items = {
            "contacts": 0,
            "users": 0,
            "statistics": 0
        }
        
        try:
            # This would typically be called during off-peak hours
            # Implementation would fetch and cache frequently accessed data
            logger.info(f"Cache warming initiated for tenant {tenant_id}")
            
            # Example: Pre-cache recent contacts, active users, etc.
            # This is a placeholder - actual implementation would fetch real data
            
            return warmed_items
            
        except Exception as e:
            logger.error(f"Cache warming error for tenant {tenant_id}: {e}")
            return warmed_items
    
    async def get_cache_stats(self, tenant_id: Optional[uuid.UUID] = None) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            # Get Redis info
            info = await redis_client.redis.info()
            
            # Count keys for tenant if specified
            if tenant_id:
                pattern = f"cache:{tenant_id}:*"
                keys = await redis_client.redis.keys(pattern)
                tenant_key_count = len(keys)
            else:
                tenant_key_count = None
            
            return {
                "redis_info": {
                    "used_memory": info.get("used_memory_human"),
                    "connected_clients": info.get("connected_clients"),
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses")
                },
                "tenant_keys": tenant_key_count,
                "cache_hit_ratio": self._calculate_hit_ratio(info)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}
    
    def _calculate_hit_ratio(self, redis_info: Dict[str, Any]) -> Optional[float]:
        """Calculate cache hit ratio"""
        try:
            hits = int(redis_info.get("keyspace_hits", 0))
            misses = int(redis_info.get("keyspace_misses", 0))
            
            if hits + misses > 0:
                return round((hits / (hits + misses)) * 100, 2)
            return None
            
        except Exception:
            return None


# Global cache service instance
cache_service = CacheService()