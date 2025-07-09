import sys
from cache import RedisCache

def main():
    if len(sys.argv) < 3:
        print("Usage: python set_cache_entry.py <query> <response> [ttl_in_seconds] [--semantic]")
        print("Options:")
        print("  ttl_in_seconds: Set to 0 or 'None' for permanent cache")
        print("  --semantic: Store as semantic cache entry")
        sys.exit(1)

    query = sys.argv[1]
    response = sys.argv[2]
    ttl = None
    semantic = False

    # Parse arguments
    for i in range(3, len(sys.argv)):
        arg = sys.argv[i]
        if arg == "--semantic":
            semantic = True
        else:
            try:
                ttl = int(arg)
            except ValueError:
                print(f"Warning: Ignoring invalid argument '{arg}'")

    cache = RedisCache()
    
    if semantic:
        key = cache.set_semantic_cache(query, response, ttl=ttl)
        cache_type = "Semantic"
    else:
        key = cache.set(query, response, ttl=ttl)
        cache_type = "Standard"

    print(f"{cache_type} Cache Key: {key}")
    print(f"TTL: {'Permanent' if ttl is None else str(ttl) + ' seconds'}")

if __name__ == "__main__":
    main()
