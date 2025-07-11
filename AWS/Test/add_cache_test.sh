#!/bin/bash

key1=""
key2=""

cleanup_and_log()
{
    echo -e "\nDeleting query1 ..."
    sudo docker exec redis-test redis-cli DEL "$key1"

    echo -e "\nConfirming deletion for key1..."
    if [ "$(sudo docker exec redis-test redis-cli EXISTS "$key1")" -eq 0 ]; then
        echo "SUCCESS: Query 1 deleted." # Indicate success
    else
        echo "FAILURE: Query 1 still exists"
    fi

    echo -e "\nDeleting query2 ..."
    sudo docker exec redis-test redis-cli DEL "$key2"

    echo -e "\nConfirming deletion for key2..."
    if [ "$(sudo docker exec redis-test redis-cli EXISTS "$key2")" -eq 0 ]; then
        echo "SUCCESS: Query 2 deleted." # Indicate success
    else
        echo "FAILURE: Query 2 still exists"
    fi
}

trap cleanup_and_log EXIT

# Get the absolute path of the script itself, resolving symlinks
SCRIPT_FULL_PATH="$(readlink -f "$0")"

# Get the directory of the script
SCRIPT_DIR="$(dirname "$SCRIPT_FULL_PATH")"

# Go one directory up from the script's directory
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "\n--- Test adding temporary cache manually ---\n"
echo "Testing for TTL: 60"
key1=$(python "$PARENT_DIR"/add_cache.py "What is the capital of India?" "New Delhi" 60 | head -n 3 | tail -n 1)
echo -e "Extracted key for testing: '$key1'\n"
echo "Checking TTL for key in Redis..."
ttl_value=$(sudo docker exec redis-test redis-cli TTL "$key1" | awk '{print $NF}' | tr -d '\r' | xargs)
echo "Redis TTL output for key: '$ttl_value'"
if [ "$ttl_value" -eq 60 ]; then
    echo "SUCCESS: The TTL for key is the same." # Indicate success
else
    echo "FAILURE: The TTL for key is NOT the same. Expected 60, got $ttl_value."
    exit 1 # Indicate failure
fi

echo -e "\n--- Test adding permanent cache manually ---\n"
key2=$(python "$PARENT_DIR"/add_cache.py "What is the capital of Canada?" "Ottawa" | head -n 3 | tail -n 1)
echo -e "Extracted key for testing: '$key2'\n"
echo "Checking TTL for key in Redis..."
ttl_value=$(sudo docker exec redis-test redis-cli TTL "$key2" | awk '{print $NF}' | tr -d '\r' | xargs)
echo "Redis TTL output for key: '$ttl_value'"
if [ "$ttl_value" -eq -1 ]; then
    echo "SUCCESS: The entry for key is permanent (TTL: -1)." # Indicate success
else
    echo "FAILURE: The entry for key is NOT permanent. Expected -1, got $ttl_value."
    exit 1 # Indicate failure
fi

exit 0