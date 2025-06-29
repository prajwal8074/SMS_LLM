import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import hashlib
import time # Import time for potential delays if needed for TTL checks

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cache import RedisCache # Assuming cache.py is in the same directory

class TestRedisCache(unittest.TestCase):

    def setUp(self):
        """
        Set up the test environment before each test method.
        Connects to a live Redis instance (assumes environment variables are set).
        Clears the Redis database to ensure a clean state for each test.
        """
        # Initialize RedisCache, which will now attempt to connect to a live Redis
        # based on REDIS_HOST, REDIS_PORT, REDIS_DB from actual environment variables.
        self.cache = RedisCache()
        
        # Ensure the Redis connection is active before flushing
        try:
            self.cache.redis.ping()
        except Exception as e:
            self.fail(f"Could not connect to Redis. Ensure Redis container is running and environment variables are set correctly: {e}")

        # Clear the database before each test to ensure test isolation
        self.cache.redis.flushdb()
        print(f"\n--- Running test: {self._testMethodName} ---")

    def test_get_cache_key(self):
        """
        Test if get_cache_key generates correct and consistent SHA256 hashes.
        This method does not interact with Redis, so it remains a pure unit test.
        """
        query1 = "  Test Query "
        query2 = "test query"
        query3 = "Another Query"

        # Expected hash for "test query" (stripped and lowercased)
        expected_hash_for_test_query = hashlib.sha256("test query".encode()).hexdigest()

        self.assertEqual(self.cache.get_cache_key(query1), expected_hash_for_test_query)
        self.assertEqual(self.cache.get_cache_key(query2), expected_hash_for_test_query)
        self.assertNotEqual(self.cache.get_cache_key(query3), expected_hash_for_test_query)

    def test_set_and_get(self):
        """
        Test the set and get methods with actual Redis interactions.
        """
        query = "test query for set/get"
        response = "test response data"
        ttl = 3600 # 1 hour

        # Test set method - performs actual call to Redis
        self.cache.set(query, response, ttl)
        
        # Verify by directly getting from Redis using the generated key
        expected_key = self.cache.get_cache_key(query)
        retrieved_from_redis = self.cache.redis.get(expected_key)
        self.assertEqual(retrieved_from_redis, response)
        self.assertGreaterEqual(self.cache.redis.ttl(expected_key), ttl - 5) # Allow for slight time variance

        # Test get method - performs actual call to Redis
        retrieved_response = self.cache.get(query)
        self.assertEqual(retrieved_response, response)

        # Test get for non-existent key
        self.assertIsNone(self.cache.get("non-existent query"))

    def test_set_get_with_semantically_different_queries(self):
        """
        Test setting and getting with queries that are semantically related but
        distinct enough to generate different cache keys. This highlights that
        the cache operates on exact key matches in a live Redis environment.
        """
        query1 = "What is the capital of France?"
        response1 = "Paris"

        query2 = "Capital of France?"
        response2 = "Paris, France" # Different response to emphasize distinct entries

        query3 = "What is the capital of Germany?"
        response3 = "Berlin"

        # Set first query
        self.cache.set(query1, response1)
        key1 = self.cache.get_cache_key(query1)
        self.assertEqual(self.cache.redis.get(key1), response1)

        # Set second query
        self.cache.set(query2, response2)
        key2 = self.cache.get_cache_key(query2)
        self.assertEqual(self.cache.redis.get(key2), response2)

        # Set third query
        self.cache.set(query3, response3)
        key3 = self.cache.get_cache_key(query3)
        self.assertEqual(self.cache.redis.get(key3), response3)

        # Ensure keys are indeed different (local calculation, no Redis interaction)
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key1, key3)
        self.assertNotEqual(key2, key3)

        # Verify retrieval for query1
        self.assertEqual(self.cache.get(query1), response1)

        # Verify retrieval for query2
        self.assertEqual(self.cache.get(query2), response2)

        # Verify retrieval for query3
        self.assertEqual(self.cache.get(query3), response3)

if __name__ == '__main__':
    unittest.main()
