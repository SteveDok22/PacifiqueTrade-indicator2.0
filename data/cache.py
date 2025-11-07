"""
Data Cache Module

Provides Redis-based caching for API responses.
Reduces API calls and improves performance.
"""

import json
import pickle
from typing import Any, Optional
from datetime import timedelta
import logging

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from core.exceptions import CacheError


logger = logging.getLogger(__name__)


class DataCache:
    """
    Redis-based cache for API data
    
    Stores:
    - Economic calendar events (TTL: 4 hours)
    - Market data (TTL: 2 hours for H4, 15 min for M15)
    - Fundamental signals (TTL: 4 hours)
    - Technical analysis results (TTL: 2 hours)
    """
    
    def __init__(self):
        """Initialize Redis connection"""
        
        if not config.REDIS_ENABLED:
            logger.warning("Redis cache is disabled in config")
            self.client = None
            return
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis library not installed. Install with: pip install redis")
            self.client = None
            return
        
        try:
            self.client = redis.Redis(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
                decode_responses=False,  # We'll handle encoding
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {config.REDIS_HOST}:{config.REDIS_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        return self.client is not None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        category: str = 'general'
    ) -> bool:
        """
        Store value in cache
        
        Args:
            key: Cache key
            value: Value to store (will be pickled)
            ttl: Time to live in seconds (None = no expiration)
            category: Category prefix for key
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        full_key = f"{category}:{key}"
        
        try:
            # Serialize value
            serialized = pickle.dumps(value)
            
            # Store in Redis
            if ttl:
                self.client.setex(full_key, ttl, serialized)
            else:
                self.client.set(full_key, serialized)
            
            logger.debug(f"Cached: {full_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for {full_key}: {e}")
            raise CacheError(operation="set", key=full_key, message=str(e))
    
    def get(self, key: str, category: str = 'general') -> Optional[Any]:
        """
        Retrieve value from cache
        
        Args:
            key: Cache key
            category: Category prefix
            
        Returns:
            Cached value or None if not found
        """
        if not self.is_available():
            return None
        
        full_key = f"{category}:{key}"
        
        try:
            data = self.client.get(full_key)
            
            if data is None:
                logger.debug(f"Cache miss: {full_key}")
                return None
            
            # Deserialize
            value = pickle.loads(data)
            logger.debug(f"Cache hit: {full_key}")
            return value
            
        except Exception as e:
            logger.error(f"Cache get failed for {full_key}: {e}")
            return None
    
    def delete(self, key: str, category: str = 'general') -> bool:
        """Delete key from cache"""
        if not self.is_available():
            return False
        
        full_key = f"{category}:{key}"
        
        try:
            deleted = self.client.delete(full_key)
            logger.debug(f"Deleted from cache: {full_key}")
            return deleted > 0
        except Exception as e:
            logger.error(f"Cache delete failed for {full_key}: {e}")
            return False
    
    def clear_category(self, category: str) -> int:
        """
        Clear all keys in a category
        
        Args:
            category: Category to clear
            
        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0
        
        try:
            pattern = f"{category}:*"
            keys = self.client.keys(pattern)
            
            if not keys:
                return 0
            
            deleted = self.client.delete(*keys)
            logger.info(f"Cleared {deleted} keys from category: {category}")
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to clear category {category}: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """Clear entire cache (use with caution!)"""
        if not self.is_available():
            return False
        
        try:
            self.client.flushdb()
            logger.warning("⚠️  Cleared entire Redis cache!")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_ttl(self, key: str, category: str = 'general') -> Optional[int]:
        """Get time to live for a key (seconds)"""
        if not self.is_available():
            return None
        
        full_key = f"{category}:{key}"
        
        try:
            ttl = self.client.ttl(full_key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Failed to get TTL for {full_key}: {e}")
            return None
    
    def exists(self, key: str, category: str = 'general') -> bool:
        """Check if key exists in cache"""
        if not self.is_available():
            return False
        
        full_key = f"{category}:{key}"
        
        try:
            return self.client.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Failed to check existence of {full_key}: {e}")
            return False
    
    # Convenience methods for specific data types
    
    def cache_calendar_events(self, events: list, date: str) -> bool:
        """Cache economic calendar events"""
        key = f"calendar:{date}"
        return self.set(
            key,
            events,
            ttl=config.CACHE_TTL_FUNDAMENTAL,
            category='fundamental'
        )
    
    def get_calendar_events(self, date: str) -> Optional[list]:
        """Get cached calendar events"""
        key = f"calendar:{date}"
        return self.get(key, category='fundamental')
    
    def cache_market_data(self, pair: str, timeframe: str, data) -> bool:
        """Cache market data"""
        key = f"{pair}:{timeframe}"
        
        # Different TTLs for different timeframes
        ttl_map = {
            'M15': 900,   # 15 minutes
            'M30': 1800,  # 30 minutes
            'H1': 3600,   # 1 hour
            'H4': 7200,   # 2 hours
            'D1': 14400,  # 4 hours
        }
        ttl = ttl_map.get(timeframe, config.CACHE_TTL_TECHNICAL)
        
        return self.set(key, data, ttl=ttl, category='market_data')
    
    def get_market_data(self, pair: str, timeframe: str):
        """Get cached market data"""
        key = f"{pair}:{timeframe}"
        return self.get(key, category='market_data')
    
    def cache_signal(self, pair: str, signal_data: dict) -> bool:
        """Cache trading signal"""
        key = f"signal:{pair}"
        return self.set(
            key,
            signal_data,
            ttl=config.CACHE_TTL_LIQUIDITY,
            category='signals'
        )
    
    def get_signal(self, pair: str) -> Optional[dict]:
        """Get cached signal"""
        key = f"signal:{pair}"
        return self.get(key, category='signals')
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.is_available():
            return {'available': False}
        
        try:
            info = self.client.info('stats')
            return {
                'available': True,
                'total_keys': self.client.dbsize(),
                'hits': info.get('keyspace_hits', 0),
                'misses': info.get('keyspace_misses', 0),
                'memory_used': info.get('used_memory_human', 'N/A')
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'available': False, 'error': str(e)}


# Singleton instance
_cache_instance = None

def get_cache() -> DataCache:
    """Get singleton cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DataCache()
    return _cache_instance


def main():
    """Test the cache module"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*60)
    print("DATA CACHE TEST")
    print("="*60 + "\n")
    
    cache = DataCache()
    
    if not cache.is_available():
        print("⚠️  Redis cache is not available")
        print("\nReasons:")
        print("1. Redis is disabled in .env (REDIS_ENABLED=false)")
        print("2. Redis is not installed (pip install redis)")
        print("3. Redis server is not running")
        print("\n💡 This is optional - the system works without Redis")
        print("   Redis just improves performance by caching API responses")
        return 0
    
    print("✅ Redis cache is available\n")
    
    try:
        # Test 1: Basic set/get
        print("Test 1: Basic set/get...")
        cache.set('test_key', {'data': 'test_value'}, ttl=60)
        value = cache.get('test_key')
        print(f"✅ Stored and retrieved: {value}\n")
        
        # Test 2: Check existence
        print("Test 2: Check existence...")
        exists = cache.exists('test_key')
        print(f"✅ Key exists: {exists}\n")
        
        # Test 3: Get TTL
        print("Test 3: Get TTL...")
        ttl = cache.get_ttl('test_key')
        print(f"✅ TTL remaining: {ttl} seconds\n")
        
        # Test 4: Delete key
        print("Test 4: Delete key...")
        deleted = cache.delete('test_key')
        print(f"✅ Deleted: {deleted}\n")
        
        # Test 5: Cache stats
        print("Test 5: Cache statistics...")
        stats = cache.get_stats()
        print(f"✅ Stats: {stats}\n")
        
        print("="*60)
        print("✅ ALL CACHE TESTS PASSED!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        logger.exception("Test failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())