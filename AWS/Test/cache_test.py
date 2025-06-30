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

if __name__ == '__main__':
    unittest.main()
