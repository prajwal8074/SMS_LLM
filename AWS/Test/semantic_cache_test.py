import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cache import RedisCache

# Initialize the cache with your desired embedding model and threshold
cache = RedisCache(embedding_model_name='all-MiniLM-L6-v2', distance_threshold=0.7) # Adjust threshold as needed

# Test cases
query1 = "What is the capital of France?"
response1 = {"answer": "Paris"}

query2 = "Which city is the capital of France?"
response2 = {"answer": "Paris"} # This would be if you processed it

query3 = "Tell me about the biggest city in France." # Semantically similar to query1
query4 = "What is the largest animal?" # Semantically dissimilar

# Set some items in the cache
cache.set(query1, response1) # Only set query 1 and check if it returns response for query 1 also

print("\n--- Testing GET with semantic matching ---")

# Try to get query1 (exact match)
cached_response = cache.get(query1)
if cached_response:
    print(f"Query '{query1}': Found in cache: {cached_response}")
else:
    print(f"Query '{query1}': Not found in cache.")

# Try to get query3 (semantic match)
cached_response = cache.get(query3)
if cached_response:
    print(f"Query '{query3}': Found in cache: {cached_response}")
else:
    print(f"Query '{query3}': Not found in cache.")

# Try to get query4 (no semantic match)
cached_response = cache.get(query4)
if cached_response:
    print(f"Query '{query4}': Found in cache: {cached_response}")
else:
    print(f"Query '{query4}': Not found in cache.")