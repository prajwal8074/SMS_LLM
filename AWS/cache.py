import redis
import hashlib
import os
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB')),
            decode_responses=False  # Required for vector storage
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Existing exact-match methods remain unchanged
    def get_cache_key(self, query: str) -> str:
        return hashlib.sha256(query.strip().lower().encode()).hexdigest()
    
    def get(self, query: str):
        key = self.get_cache_key(query)
        return self.redis.get(key)
    
    def set(self, query: str, response: str, ttl: int = 86400):
        key = self.get_cache_key(query)
        if ttl is None:
            self.redis.set(key, response)
        else:
            self.redis.setex(key, ttl, response)
        return key

    # New semantic methods
    def get_semantic(self, query: str, threshold: float = 0.85):
        """Get semantically similar cached response"""
        embedding = self.model.encode(query)
        # This would use vector similarity search in production
        # Placeholder implementation:
        for key in self.redis.scan_iter("embed:*"):
            stored_emb = np.frombuffer(self.redis.get(key))
            similarity = np.dot(embedding, stored_emb)
            if similarity > threshold:
                return self.redis.get(key.decode().replace("embed:", ""))
        return None

    def set_semantic(self, query: str, response: str, ttl: int = 86400):
        """Store with semantic indexing"""
        key = self.set(query, response, ttl)  # Standard cache
        embedding = self.model.encode(query).tobytes()
        self.redis.set(f"embed:{key}", embedding)
        return key
