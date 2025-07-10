import redis
import hashlib
import os
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import numpy as np
from redis.commands.search.query import Query
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType

load_dotenv()  # Load environment variables

class RedisCache:
    def __init__(self, embedding_model_name: str = 'all-MiniLM-L6-v2', distance_threshold: float = 0.2): # Adjusted default threshold
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB')),
            decode_responses=False # Keep as bytes for vector storage
        )
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.vector_dimension = self.embedding_model.get_sentence_embedding_dimension()
        self.distance_threshold = distance_threshold
        self.index_name = "semantic_cache_idx" # Name for your Redis search index
        self._create_redis_index()

    def _create_redis_index(self):
        """Creates a RediSearch index for vector search if it doesn't exist."""
        try:
            self.redis.ft(self.index_name).info()
            print(f"RediSearch index '{self.index_name}' already exists.")
        except:
            schema = (
                TextField("query"),
                VectorField("query_vector", "FLAT", {
                    "TYPE": "FLOAT32",
                    "DIM": self.vector_dimension,
                    "DISTANCE_METRIC": "COSINE" # Or L2 (Euclidean)
                }),
                TextField("response"),
                TagField("tag") # Optional: for filtering by categories, etc.
            )
            definition = IndexDefinition(prefix=["cache:"], index_type=IndexType.HASH)
            self.redis.ft(self.index_name).create_index(fields=schema, definition=definition)
            print(f"RediSearch index '{self.index_name}' created successfully.")

    def _get_embedding(self, text: str) -> np.ndarray:
        """Generates a vector embedding for the given text."""
        return self.embedding_model.encode(text).astype(np.float32)

    def get_cache_key(self, query: str) -> str:
        """Create unique SHA256 hash from query for Redis key (still useful for direct access if needed)"""
        # Prefix with "cache:" for the index definition
        return f"cache:{hashlib.sha256(query.strip().lower().encode()).hexdigest()}"

    def get_semantically(self, query: str):
        """Get cached response using semantic matching."""
        query_vector = self._get_embedding(query).tobytes()

        # Perform a vector similarity search
        # We're looking for cached entries where the 'query_vector' is similar to the new query's embedding
        # The K-NN query finds the 'k' nearest neighbors. We'll take the closest one if it's within the threshold.
        q = Query(f"*=>[KNN 1 @query_vector $query_vec AS vector_score]")\
            .return_fields("query", "response", "vector_score")\
            .sort_by("vector_score")\
            .dialect(2) # Use dialect 2 for richer query capabilities

        params_dict = {"query_vec": query_vector}
        search_results = self.redis.ft(self.index_name).search(q, query_params=params_dict)

        if search_results.total > 0:
            # Get the top result
            top_result = search_results.docs[0]
            similarity_score = float(top_result.vector_score)

            # Cosine similarity for RediSearch returns (1 - cosine_similarity).
            # So, a lower score means more similar. Adjust threshold as needed.
            if similarity_score <= self.distance_threshold: # <<<--- CRITICAL CHANGE HERE
                print(f"Cache hit! Dissimilarity score (distance): {similarity_score}")
                return top_result.response # Assuming response was stored as JSON string
            else:
                print(f"Cache miss (below threshold). Dissimilarity score (distance): {similarity_score}")
        return None

    def get(self, query: str):
        """Get cached response if exists"""
        key = self.get_cache_key(query)
        return self.redis.hget(key, "response").decode('utf-8')
    
    def set(self, query: str, response: str, ttl: int = None):
        """Store query and response with their embeddings."""
        key = self.get_cache_key(query)
        query_vector = self._get_embedding(query).tobytes()
        
        # Store as a Hash for RediSearch to index
        self.redis.hset(key, mapping={
            "query": query,
            "query_vector": query_vector,
            "response": response, # Store response as a JSON string
            "tag": "general" # Example tag, could be dynamic
        })
        if ttl is not None:
            self.redis.expire(key, ttl)
        return key