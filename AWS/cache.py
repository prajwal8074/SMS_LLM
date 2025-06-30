import redis
import hashlib
import os
from dotenv import load_dotenv
import json

load_dotenv()  # Load environment variables

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB')),
            decode_responses=True
        )
    
    def get_cache_key(self, query: str) -> str:
        """Create unique SHA256 hash from query"""
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()
    
    def get(self, query: str):
        """Get cached response if exists"""
        key = self.get_cache_key(query)
        return self.redis.get(key)
    
    def set(self, query: str, response: str, ttl: int = 86400):
        """Store response with expiration (default 24 hours)"""
        key = self.get_cache_key(query)
        if ttl is None or ttl == 0:
            self.redis.set(key, response) # Set permanently
        else:
            self.redis.setex(key, ttl, response) # Set with expiration
    
    def cache_hit_rate(self) -> float:
        """Calculate cache effectiveness"""
        stats = self.redis.info('stats')
        hits = int(stats['keyspace_hits'])
        misses = int(stats['keyspace_misses'])
        return hits / (hits + misses) if (hits + misses) > 0 else 0

    #Adding Cache limiting
    def is_rate_limited(self, user_id: str, max_requests: int = 5, window_sec: int = 60) -> bool:
        """
        Check if user exceeds request limit
        Returns True if rate limited, False otherwise
        """
        key = f"rate_limit:{user_id}"
        current_count = self.redis.incr(key)
    
        # Set expiration only on first request
        if current_count == 1:
            self.redis.expire(key, window_sec)
    
        return current_count > max_requests

    # ADD CACHE WARMING:
    def warm_cache(self, queries: dict, ttl=86400):
        """Preload cache with key-value pairs"""
        for query, response in queries.items():
            key = self.get_cache_key(query)
            if not self.redis.exists(key):
                self.redis.setex(key, ttl, response)

    # ADD MONITORING:
    def get_stats(self) -> dict:
        """Return cache performance statistics"""
        info = self.redis.info(section='all')
        hits = info['stats']['keyspace_hits']
        misses = info['stats']['keyspace_misses']
        total = hits + misses
    
        return {
            'hit_rate': hits / total if total > 0 else 0,
            'total_keys': self.redis.dbsize(),
            'memory_used': info['memory']['used_memory_human'],
            'uptime_days': info['server']['uptime_in_days'],
            'avg_hit_time': f"{info['stats']['avg_ttl']}ms" 
        }