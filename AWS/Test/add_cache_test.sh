#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Get the absolute path of the script itself, resolving symlinks
SCRIPT_FULL_PATH="$(readlink -f "$0")"

# Get the directory of the script
SCRIPT_DIR="$(dirname "$SCRIPT_FULL_PATH")"

# Go one directory up from the script's directory (assuming add_cache.py is in the parent)
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
ADD_CACHE_SCRIPT="$PARENT_DIR/add_cache.py" # Path to your add_cache.py

echo -e "\n--- Test adding and retrieving TEMPORARY semantic cache ---\n"

QUERY_TEMP="What is the capital of India?"
RESPONSE_TEMP="New Delhi"
TTL_TEMP=60
SIMILAR_QUERY_TEMP="Capital city of India please?"

echo "--- Storing primary query: '$QUERY_TEMP' with TTL $TTL_TEMP ---"
# Run add_cache.py to store the entry and capture its full output
output_add_temp=$(python "$ADD_CACHE_SCRIPT" "$QUERY_TEMP" "$RESPONSE_TEMP" "$TTL_TEMP")
echo "$output_add_temp"

# Extract the stored Redis key for TTL verification
# Using grep and awk to robustly get the last word after "Successfully Stored Semantic Cache for Key:"
STORED_KEY_TEMP=$(echo "$output_add_temp" | grep "Successfully Stored Semantic Cache for Key:" | awk '{print $NF}' | tr -d '\r')

if [ -z "$STORED_KEY_TEMP" ]; then
    echo "ERROR: Failed to extract stored semantic key for temporary cache. Exiting."
    exit 1
fi
echo "Extracted Stored Semantic Key: '$STORED_KEY_TEMP'"

# Verify TTL directly in Redis for the stored key
echo "Checking TTL for stored semantic key in Redis..."
ACTUAL_TTL_TEMP=$(docker exec redis-test redis-cli TTL "$STORED_KEY_TEMP" | awk '{print $NF}' | tr -d '\r')
echo "Redis TTL output for key '$STORED_KEY_TEMP': '$ACTUAL_TTL_TEMP'"

if [ "$ACTUAL_TTL_TEMP" -gt 0 ] && [ "$ACTUAL_TTL_TEMP" -le "$TTL_TEMP" ]; then
    echo "SUCCESS: Temporary semantic cache key set with correct TTL range."
else
    echo "FAILURE: Temporary semantic cache key TTL is not as expected. Expected >0 and <=$TTL_TEMP, got $ACTUAL_TTL_TEMP."
    exit 1
fi

echo -e "\n--- Attempting retrieval with a SEMANTICALLY SIMILAR query for TEMPORARY cache ---\n"
echo "Check Query: '$SIMILAR_QUERY_TEMP'"
# Run add_cache.py again, but this time only to check for the cache entry using a similar query
# We pass a dummy response as it won't be stored if found in cache
output_check_temp=$(python "$ADD_CACHE_SCRIPT" "dummy_query_for_check" "dummy_response_for_check" "None" "$SIMILAR_QUERY_TEMP")
echo "$output_check_temp"

if echo "$output_check_temp" | grep -q "SUCCESS: Retrieved from semantic cache." && \
   echo "$output_check_temp" | grep -q "Matched Query in Cache: $QUERY_TEMP" && \
   echo "$output_check_temp" | grep -q "Retrieved Response: $RESPONSE_TEMP"; then
    echo "SUCCESS: Semantic cache retrieved for a similar query and content matches."
else
    echo "FAILURE: Semantic cache NOT retrieved for a similar query or content mismatch."
    exit 1
fi

echo -e "\n--- Test adding and retrieving PERMANENT semantic cache ---\n"

QUERY_PERM="How big is the Earth?"
RESPONSE_PERM="About 12,742 km in diameter."
SIMILAR_QUERY_PERM="What is the Earth's diameter?"

echo "--- Storing primary query: '$QUERY_PERM' permanently ---"
output_add_perm=$(python "$ADD_CACHE_SCRIPT" "$QUERY_PERM" "$RESPONSE_PERM" "None")
echo "$output_add_perm"

STORED_KEY_PERM=$(echo "$output_add_perm" | grep "Successfully Stored Semantic Cache for Key:" | awk '{print $NF}' | tr -d '\r')

if [ -z "$STORED_KEY_PERM" ]; then
    echo "ERROR: Failed to extract stored semantic key for permanent cache. Exiting."
    exit 1
fi
echo "Extracted Stored Semantic Key: '$STORED_KEY_PERM'"

# Verify TTL directly in Redis for the permanent key
echo "Checking TTL for stored permanent semantic key in Redis..."
ACTUAL_TTL_PERM=$(docker exec redis-test redis-cli TTL "$STORED_KEY_PERM" | awk '{print $NF}' | tr -d '\r')
echo "Redis TTL output for key '$STORED_KEY_PERM': '$ACTUAL_TTL_PERM'"

if [ "$ACTUAL_TTL_PERM" -eq -1 ]; then
    echo "SUCCESS: Permanent semantic cache key set with TTL -1."
else
    echo "FAILURE: Permanent semantic cache key TTL is not -1. Expected -1, got $ACTUAL_TTL_PERM."
    exit 1
fi

echo -e "\n--- Attempting retrieval with a SEMANTICALLY SIMILAR query for PERMANENT cache ---\n"
echo "Check Query: '$SIMILAR_QUERY_PERM'"
output_check_perm=$(python "$ADD_CACHE_SCRIPT" "dummy_query_for_perm_check" "dummy_response_for_perm_check" "None" "$SIMILAR_QUERY_PERM")
echo "$output_check_perm"

if echo "$output_check_perm" | grep -q "SUCCESS: Retrieved from semantic cache." && \
   echo "$output_check_perm" | grep -q "Matched Query in Cache: $QUERY_PERM" && \
   echo "$output_check_perm" | grep -q "Retrieved Response: $RESPONSE_PERM"; then
    echo "SUCCESS: Semantic cache retrieved for a similar query and content matches."
else
    echo "FAILURE: Semantic cache NOT retrieved for a similar query or content mismatch."
    exit 1
fi

echo -e "\nAll semantic cache tests completed successfully!"
exit 0
