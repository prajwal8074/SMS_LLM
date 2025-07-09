import redis
import hashlib
import os
import string
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer  # Add this import

load_dotenv()

class RedisCache:
    def __init__(self):
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB')),
            decode_responses=False  # Changed for binary vector storage
        )
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Embedding model
    
    def get_cache_key(self, query: str) -> str:
        """Create unique SHA256 hash from normalized query"""
        # Semantic normalization
        query = query.lower().strip()
        query = query.translate(str.maketrans('', '', string.punctuation))
        words = query.split()
        words.sort()
        normalized_query = " ".join(words)
        return hashlib.sha256(normalized_query.encode()).hexdigest()
    
    # --- Semantic Cache Methods ---
    def get_semantic_cache(self, query: str, threshold: float = 0.8):
        """Get cached response using semantic similarity"""
        # Generate embedding
        embedding = self.model.encode([query])[0].tobytes()
        
        # Find similar embeddings (pseudo-code - requires vector DB setup)
        # This would be replaced with actual vector similarity search
        similar_keys = self._find_similar_embeddings(embedding, threshold)
        
        if similar_keys:
            return self.redis.get(similar_keys[0])
        return None

    def set_semantic_cache(self, query: str, response: str, ttl: int = 86400):
        """Store response with semantic embedding"""
        # Store standard cache
        key = self.set(query, response, ttl)
        
        # Store embedding separately
        embedding = self.model.encode([query])[0].tobytes()
        self.redis.set(f"embed:{key}", embedding)
        return key

    # --- Original Methods (Updated) ---
    def get(self, query: str, semantic: bool = False, threshold: float = 0.8):
        """Get cached response (optionally using semantic matching)"""
        if semantic:
            return self.get_semantic_cache(query, threshold)
        key = self.get_cache_key(query)
        return self.redis.get(key)
    
    def set(self, query: str, response: str, ttl: int = 86400):
        """Store response with expiration"""
        key = self.get_cache_key(query)
        if ttl is None:
            self.redis.set(key, response)
        else:
            self.redis.setex(key, ttl, response)
        return key
