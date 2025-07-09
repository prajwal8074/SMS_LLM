#!/bin/bash

# Get the absolute path of the script itself, resolving symlinks
SCRIPT_FULL_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_FULL_PATH")"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Verify Redis connection
echo "Testing Redis connection..."
if ! docker exec redis-test redis-cli PING | grep -q "PONG"; then
    echo "ERROR: Could not connect to Redis"
    exit 1
fi

echo -e "\n--- Test adding temporary cache manually ---\n"
full_output=$(python "$PARENT_DIR"/add_cache.py "What is the capital of India?" "New Delhi" 60)
key=$(echo "$full_output" | grep "^Cache Key:" | awk '{print $3}')
echo "Full Python output:"
echo "$full_output"
echo "Extracted key for testing: '$key'"

if [ -z "$key" ]; then
    echo "ERROR: Failed to extract cache key"
    exit 1
fi

echo "Checking TTL for key in Redis..."
ttl_value=$(docker exec redis-test redis-cli TTL "$key" | awk '{print $NF}' | tr -d '\r' | xargs)
echo "Redis TTL output for key: '$ttl_value'"
if [ "$ttl_value" -eq 60 ]; then
    echo "SUCCESS: The TTL for key is the same."
else
    echo "FAILURE: The TTL for key is NOT the same. Expected 60, got $ttl_value."
    exit 1
fi

echo -e "\n--- Test adding permanent cache manually ---\n"
full_output=$(python "$PARENT_DIR"/add_cache.py "What is the capital of Canada?" "Ottawa")
key=$(echo "$full_output" | grep "^Cache Key:" | awk '{print $3}')
echo "Full Python output:"
echo "$full_output"
echo "Extracted key for testing: '$key'"

if [ -z "$key" ]; then
    echo "ERROR: Failed to extract cache key"
    exit 1
fi

echo "Checking TTL for key in Redis..."
ttl_value=$(docker exec redis-test redis-cli TTL "$key" | awk '{print $NF}' | tr -d '\r' | xargs)
echo "Redis TTL output for key: '$ttl_value'"
if [ "$ttl_value" -eq -1 ]; then
    echo "SUCCESS: The entry for key is permanent (TTL: -1)."
else
    echo "FAILURE: The entry for key is NOT permanent. Expected -1, got $ttl_value."
    exit 1
fi

exit 0
