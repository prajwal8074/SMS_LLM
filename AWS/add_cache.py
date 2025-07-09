import sys
import time
from cache import RedisCache

def main():
    if len(sys.argv) < 3:
        print("Usage: python add_cache.py <query> <response> [ttl_in_seconds]")
        print("  ttl_in_seconds: Optional. Set to 0 or 'None' for permanent cache.")
        sys.exit(1)

    query = sys.argv[1]
    response = sys.argv[2]
    ttl = None  # Default to permanent cache

    if len(sys.argv) == 4:
        ttl_arg = sys.argv[3].lower()
        if ttl_arg == 'none':
            ttl = None
        elif ttl_arg == '0':
            ttl = None  # 0 also means permanent
        else:
            try:
                ttl = int(ttl_arg)
                if ttl < 0:
                    raise ValueError("TTL must be positive")
            except ValueError as e:
                print(f"Error: {e}. Must be a positive integer, '0', or 'None'.")
                sys.exit(1)

    cache = RedisCache()
    key = cache.set(query, response, ttl=ttl)

    # Verify the key was actually set
    stored_value = cache.get(query)
    if stored_value != response:
        print("ERROR: Failed to store value in cache!")
        sys.exit(1)

    # Get actual TTL from Redis
    actual_ttl = cache.redis.ttl(key)
    if ttl is None:
        expected_ttl = -1  # Redis returns -1 for permanent keys
    else:
        expected_ttl = ttl

    print(f"Cache Key: {key}")
    print(f"Stored Value: {stored_value}")
    print(f"Requested TTL: {'Permanent' if ttl is None else f'{ttl} seconds'}")
    print(f"Actual TTL: {'Permanent' if actual_ttl == -1 else f'{actual_ttl} seconds'}")

    # Additional verification for temporary keys
    if ttl is not None and ttl > 0:
        print("\nVerifying TTL countdown...")
        time.sleep(1)
        new_ttl = cache.redis.ttl(key)
        print(f"TTL after 1 second: {new_ttl} seconds")
        if new_ttl >= ttl:
            print("WARNING: TTL not decreasing properly!")

if __name__ == "__main__":
    main()
