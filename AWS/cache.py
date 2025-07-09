import redis
import hashlib
import os
from dotenv import load_dotenv
from redis.commands.search.field import VectorField, TagField, TextField
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer
import numpy as np
import json

from redis.commands.search.index_definition import IndexDefinition

load_dotenv()

class RedisCache:
    def __init__(self):
        # decode_responses=False is crucial here because embeddings are bytes
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT')),
            db=int(os.getenv('REDIS_DB')),
            decode_responses=False
        )
        try:
            self.redis_client.ping()
            print("Connected to Redis successfully!")
        except redis.exceptions.ConnectionError as e:
            print(f"Could not connect to Redis: {e}")
            raise

        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2') # A small, fast model for demonstration
        self.vector_dim = self.embedding_model.get_sentence_embedding_dimension()
        self.index_name = "query_embeddings_idx" # Unique index name
        self._create_index()

    def _create_index(self):
        try:
            # Check if index exists
            self.redis_client.ft(self.index_name).info()
            print(f"RediSearch index '{self.index_name}' already exists.")
        except Exception as e:
            # If info() fails, it means the index doesn't exist
            print(f"Creating RediSearch index '{self.index_name}'...")
            schema = (
                TextField("query_text"), # Original query string
                VectorField("query_vector", "FLAT", { # Vector field for embeddings
                    "TYPE": "FLOAT32",
                    "DIM": self.vector_dim,
                    "DISTANCE_METRIC": "COSINE"
                }),
                TextField("response_text"), # Cached response
                TagField("type", sortable=True), # e.g., 'semantic_cache'
            )
            # Define how the index maps to Redis keys
            definition = IndexDefinition(
                prefix=["semantic_query:"],
                 index_type="HASH"   # Should be a string, not a list
            )
            try:
                self.redis_client.ft(self.index_name).create_index(fields=schema, definition=definition)
                print(f"RediSearch index '{self.index_name}' created successfully.")
            except Exception as create_e:
                print(f"Error creating RediSearch index: {create_e}")
                raise

    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generates a numerical embedding for the given text."""
        # Ensure input is string
        if not isinstance(text, str):
            text = str(text)
        return self.embedding_model.encode(text, convert_to_numpy=True)

    def set_semantic(self, query_text: str, response_text: str, ttl: int = None):
        """
        Stores query, its embedding, and response in Redis with an optional TTL.
        Returns the Redis key used for storage.
        """
        query_embedding = self._generate_embedding(query_text)
        # Create a unique ID for the Redis key based on the query text
        key_id = hashlib.sha256(query_text.strip().lower().encode('utf-8')).hexdigest()
        redis_key = f"semantic_query:{key_id}"

        # Store data as a Redis Hash, converting embedding to bytes
        data = {
            "query_text": query_text.encode('utf-8'), # Store as bytes if decode_responses=False
            "query_vector": query_embedding.astype(np.float32).tobytes(), # Convert numpy array to bytes
            "response_text": response_text.encode('utf-8'), # Store as bytes
            "type": "semantic_cache".encode('utf-8') # Store as bytes
        }

        try:
            self.redis_client.hset(redis_key, mapping=data)
            if ttl is not None and ttl > 0:
                self.redis_client.expire(redis_key, ttl)
                print(f"Set semantic cache for key '{redis_key}' (query: '{query_text[:30]}...') with TTL {ttl}s.")
            else:
                print(f"Set permanent semantic cache for key '{redis_key}' (query: '{query_text[:30]}...').")
            return redis_key
        except Exception as e:
            print(f"Error setting semantic cache for key '{redis_key}': {e}")
            return None

    def get_semantic(self, query_text: str, similarity_threshold: float = 0.8):
        """
        Retrieves a semantically similar cached response using vector search.
        Returns (response_text, actual_query_matched, similarity_score) or (None, None, None)
        """
        query_embedding = self._generate_embedding(query_text).astype(np.float32).tobytes()

        # Construct the query for vector similarity search
        # K is the number of nearest neighbors to return (we want just the top 1)
        # BLOB indicates the embedding is passed as a raw blob (bytes)
        # return_fields specify which fields from the hash to return
        return_fields = ["query_text", "response_text", "vector_score", "id"] # 'id' is the Redis key
        q = Query(f"*=>[KNN 1 @query_vector BLOB '{query_embedding}']") \
            .return_fields(*return_fields) \
            .sort_by("vector_score") \
            .dialect(2) # Use query dialect 2 for BLOB support

        try:
            results = self.redis_client.ft(self.index_name).search(q)

            if results and results.docs:
                doc = results.docs[0]
                # Cosine distance (returned by RediSearch) is 0-2, where 0 is identical.
                # Cosine similarity is -1 to 1, where 1 is identical.
                # similarity = 1 - distance
                similarity_score = 1 - float(doc.vector_score)
                
                # Decode bytes results to strings
                matched_query_text = doc.query_text.decode('utf-8')
                cached_response_text = doc.response_text.decode('utf-8')

                print(f"Found potential match for '{query_text[:30]}...': Query='{matched_query_text[:30]}...', Score={similarity_score:.4f}")

                if similarity_score >= similarity_threshold:
                    print(f"Match above threshold ({similarity_threshold:.2f}). Returning cached response.")
                    return cached_response_text, matched_query_text, similarity_score
                else:
                    print(f"Match below threshold ({similarity_threshold:.2f}). No semantic cache hit.")
            else:
                print("No semantic cache entry found for this query.")
        except Exception as e:
            print(f"Error during semantic cache retrieval: {e}")

        return None, None, None

    def get_ttl(self, redis_key: str) -> int:
        """Returns the TTL for a given Redis key."""
        try:
            return self.redis_client.ttl(redis_key)
        except Exception as e:
            print(f"Error getting TTL for key '{redis_key}': {e}")
            return -3 # Custom error code
