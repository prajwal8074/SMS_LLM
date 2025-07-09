import sys
import time
from cache import RedisSemanticCache # Use the new semantic cache

def main():
    # Adjusted usage for semantic cache context
    if len(sys.argv) < 3:
        print("Usage: python add_cache.py <query> <response> [ttl_in_seconds] [check_query]")
        print("  <query>: The primary query text to cache or search for.")
        print("  <response>: The response associated with the primary query.")
        print("  [ttl_in_seconds]: Optional. Set to 'None' or '0' for permanent cache.")
        print("  [check_query]: Optional. If provided, will attempt to retrieve cache for this query instead of the primary one.")
        sys.exit(1)

    primary_query = sys.argv[1]
    response = sys.argv[2]
    ttl = None  # Default to permanent cache

    # Parse TTL argument
    if len(sys.argv) >= 4:
        ttl_arg = sys.argv[3].lower()
        if ttl_arg == 'none' or ttl_arg == '0':
            ttl = None
        else:
            try:
                ttl = int(ttl_arg)
                if ttl < 0:
                    raise ValueError("TTL must be positive or '0'/'None'")
            except ValueError as e:
                print(f"Error: {e}. TTL must be a positive integer, '0', or 'None'.")
                sys.exit(1)
    
    # Determine the query for which to check the cache (could be primary or a semantic match)
    check_query = sys.argv[4] if len(sys.argv) == 5 else primary_query

    semantic_cache = RedisSemanticCache()

    # --- Step 1: Store the primary query and response ---
    print(f"\n--- Attempting to Store Semantic Cache for Query: '{primary_query}' ---")
    stored_redis_key = semantic_cache.set_semantic(primary_query, response, ttl=ttl)
    
    if stored_redis_key:
        print(f"Successfully Stored Semantic Cache for Key: {stored_redis_key}")
        # Verify TTL immediately after setting
        actual_ttl_after_set = semantic_cache.get_ttl(stored_redis_key)
        if ttl is None:
            expected_ttl_after_set = -1 # Redis returns -1 for permanent keys
        else:
            expected_ttl_after_set = ttl
        print(f"Expected TTL after set: {'Permanent' if expected_ttl_after_set == -1 else f'{expected_ttl_after_set}s'}")
        print(f"Actual TTL after set (via Redis TTL command): {'Permanent' if actual_ttl_after_set == -1 else f'{actual_ttl_after_set}s'}")
        if actual_ttl_after_set != expected_ttl_after_set:
            # For temporary keys, it might be slightly less due to time elapsed, check range
            if ttl is not None and ttl > 0 and not (0 <= actual_ttl_after_set < expected_ttl_after_set):
                 print(f"WARNING: Actual TTL ({actual_ttl_after_set}) does not match expected ({expected_ttl_after_set}) for temporary key.")
            elif ttl is None and actual_ttl_after_set != -1:
                 print(f"WARNING: Actual TTL ({actual_ttl_after_set}) does not match expected ({expected_ttl_after_set}) for permanent key.")
    else:
        print("ERROR: Failed to store semantic cache.")
        sys.exit(1)


    # --- Step 2: Attempt to retrieve from semantic cache using check_query ---
    print(f"\n--- Attempting to Retrieve Semantic Cache for Check Query: '{check_query}' ---")
    retrieved_response, matched_query_text, similarity_score = semantic_cache.get_semantic(check_query, similarity_threshold=0.7) # Use a similarity threshold

    if retrieved_response:
        print(f"SUCCESS: Retrieved from semantic cache.")
        print(f"  Retrieved Response: {retrieved_response}")
        print(f"  Matched Query in Cache: {matched_query_text}")
        print(f"  Similarity Score: {similarity_score:.4f}")
        # If the check_query was the primary_query, verify response
        if check_query == primary_query and retrieved_response != response:
            print("ERROR: Retrieved response does not match the stored response!")
            sys.exit(1)
    else:
        print("FAILURE: No semantic cache hit for the check query or match below threshold.")
        sys.exit(1)

    # Optional: Verify TTL countdown for temporary keys after a delay
    if ttl is not None and ttl > 0:
        print("\nVerifying TTL countdown after 1 second...")
        time.sleep(1) # Wait for 1 second
        new_ttl = semantic_cache.get_ttl(stored_redis_key)
        print(f"TTL after 1 second: {'Permanent' if new_ttl == -1 else f'{new_ttl}s'}")
        if new_ttl >= ttl: # Should be less than initial TTL
            print("WARNING: TTL not decreasing properly or already expired!")
        elif new_ttl == -2:
             print("WARNING: Key expired prematurely or deleted after 1 second!")
        else:
             print("TTL appears to be decreasing correctly.")

if __name__ == "__main__":
    main()
