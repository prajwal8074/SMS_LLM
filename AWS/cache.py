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
        if ttl is None:
            self.redis.set(key, response) # Set permanently
        else:
            self.redis.setex(key, ttl, response) # Set with expiration
        return key
