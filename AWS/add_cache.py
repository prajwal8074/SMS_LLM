import sys
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
        else:
            try:
                ttl = int(ttl_arg)
            except ValueError:
                print(f"Error: Invalid TTL value '{sys.argv[3]}'. Must be an integer, '0', or 'None'.")
                sys.exit(1)

    cache = RedisCache()
    key = cache.set(query, response, ttl=ttl)

    print(f"Cache Key: {key}")
    print(f"Stored Value: {response}")
    print(f"TTL: {'Permanent' if ttl is None else f'{ttl} seconds'}")

if __name__ == "__main__":
    main()
