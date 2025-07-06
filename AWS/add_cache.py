import sys
from cache import RedisCache

def main():
    if len(sys.argv) < 3:
        print("Usage: python set_cache_entry.py <query> <response> [ttl_in_seconds]")
        print("  ttl_in_seconds: Optional. Set to 0 or 'None' for permanent cache.")
        sys.exit(1)

    query = sys.argv[1]
    response = sys.argv[2]
    ttl = None

    if len(sys.argv) == 4:
        try:
            ttl_arg = sys.argv[3].lower()
            ttl = None if ttl_arg == 'none' else int(ttl_arg)
        except ValueError:
            print(f"Error: Invalid TTL value '{sys.argv[3]}'. Must be an integer, '0', or 'None'.")
            sys.exit(1)

    cache = RedisCache()
    
    # Ensure consistent data type (bytes)
    response_bytes = response.encode('utf-8')  # Convert to bytes
    key = cache.set(query, response_bytes, ttl=ttl)

    print(key)
    print(f"TTL: {'Permanent' if ttl is None else str(ttl) + ' seconds'}")

if __name__ == "__main__":
    main()
