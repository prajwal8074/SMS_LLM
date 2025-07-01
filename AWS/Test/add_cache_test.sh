#!/bin/bash

# Get the absolute path of the script itself, resolving symlinks
SCRIPT_FULL_PATH="$(readlink -f "$0")"

# Get the directory of the script
SCRIPT_DIR="$(dirname "$SCRIPT_FULL_PATH")"

# Go one directory up from the script's directory
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "\n--- Test adding temporary cache manually ---\n"
key=$(python "$PARENT_DIR"/add_cache.py "What is the capital of India?" "New Delhi" 60 | head -n 1)
echo "Extracted key for testing: '$key'"
echo "Checking TTL for key in Redis..."
ttl_value=$(docker exec redis-test redis-cli TTL "$key" | awk '{print $NF}' | tr -d '\r' | xargs)
echo "Redis TTL output for key: '$ttl_value'"
if [ "$ttl_value" -eq 60 ]; then
    echo "SUCCESS: The TTL for key is the same." # Indicate success
else
    echo "FAILURE: The TTL for key is NOT the same. Expected 60, got $ttl_value."
    exit 1 # Indicate failure
fi

echo -e "\n--- Test adding permanent cache manually ---\n"
key=$(python "$PARENT_DIR"/add_cache.py "What is the capital of Canada?" "Ottawa" | head -n 1)
echo "Extracted key for testing: '$key'"
echo "Checking TTL for key in Redis..."
ttl_value=$(docker exec redis-test redis-cli TTL "$key" | awk '{print $NF}' | tr -d '\r' | xargs)
echo "Redis TTL output for key: '$ttl_value'"
if [ "$ttl_value" -eq -1 ]; then
    echo "SUCCESS: The entry for key is permanent (TTL: -1)." # Indicate success
else
    echo "FAILURE: The entry for key is NOT permanent. Expected -1, got $ttl_value."
    exit 1 # Indicate failure
fi

exit 0