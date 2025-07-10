import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import hashlib
import time # Import time for potential delays if needed for TTL checks

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cache import RedisCache

# Initialize the cache with your desired embedding model and threshold
cache = RedisCache(distance_threshold=0.7) # Adjust threshold as needed

try:
	cache.redis.ping()
except Exception as e:
	self.fail(f"Could not connect to Redis. Ensure Redis container is running and environment variables are set correctly: {e}")

class TestRedisCache(unittest.TestCase):

	def setUp(self):
		"""
		Set up the test environment before each test method.
		"""
		# Ensure the Redis connection is active before flushing
		
		# Clear the database before each test to ensure test isolation
		print(f"\n--- Running test: {self._testMethodName} ---\n")

	def test_set_and_get(self):
		"""
		Test the set and get methods with actual Redis interactions.
		"""
		query = "test query for set/get"
		response = "test response data"
		ttl = 3600 # 1 hour

		print("query = \"test query for set/get\"\nresponse = \"test response data\"\nttl = 3600 # 1 hour")

		print("\nSetting query ...")
		# Test set method - performs actual call to Redis
		cache.set(query, response, ttl)
		
		# Test get method - performs actual call to Redis
		print("\nGetting response ...")
		retrieved_response = cache.get(query)
		print(f"\nretrieved_response : {retrieved_response}\n")

		self.assertEqual(retrieved_response, response)

	def test_set_and_get_semantically(self):
		# Test cases
		query1 = "What is the capital of France?"
		response1 = "Paris"

		query2 = "Which city is the capital of France?"
		query3 = "Tell me about the biggest city in France." # Semantically similar to query1
		query4 = "What is the largest animal?" # Semantically dissimilar

		print("query1 = \"What is the capital of France?\"\nresponse1 = \"Paris\"\n\nquery2 = \"Which city is the capital of France?\"\nquery3 = \"Tell me about the biggest city in France.\" # Semantically similar to query1\nquery4 = \"What is the largest animal?\" # Semantically dissimilar")

		# Set some items in the cache
		print("\nSetting query 1 ...\n")
		cache.set(query1, response1)

		cached_response = cache.get_semantically(query1)
		if cached_response:
			print(f"Query '{query1}': Found in cache: {cached_response}")
		else:
			print(f"Query '{query1}': Not found in cache.")

		self.assertEqual(cached_response, response1)

		print("\n")

		cached_response = cache.get_semantically(query2)
		if cached_response:
			print(f"Query '{query2}': Found in cache {cached_response}")
		else:
			print(f"Query '{query2}': Not found in cache.")

		self.assertEqual(cached_response, response1)

		print("\n")

		# Try to get query3 (semantic match)
		cached_response = cache.get_semantically(query3)
		if cached_response:
			print(f"Query '{query3}': Found in cache: {cached_response}")
		else:
			print(f"Query '{query3}': Not found in cache.")

		self.assertEqual(cached_response, response1)

		print("\n")

		# Try to get query4 (no semantic match)
		cached_response = cache.get_semantically(query4)
		if cached_response:
			print(f"Query '{query4}': Found in cache: {cached_response}")
		else:
			print(f"Query '{query4}': Not found in cache.")

		self.assertNotEqual(cached_response, response1)

if __name__ == '__main__':
	unittest.main()
