import sys
from cache import RedisCache


def main():
    # Expecting arguments: script_name query  response [ttl]
    if len(sys.argv) < 3:
        print("Usage: python set_cache_entry.py <query> <response> [ttl_in_seconds]")
        sys.exit(1)

    query = sys.argv[1]
    response = sys.argv[2]

    ttl = None # Default to permanent if not provided
    if len(sys.argv) > 3:
        try:
            ttl = int(sys.argv[3])+1
        except ValueError:
            print(f"Error: Invalid TTL value '{sys.argv[3]}'. Must be an integer.")
            sys.exit(1)

    cache = RedisCache()
    key = cache.set(query, response, ttl=ttl)

    print(key)
    print(f"TTL: {'Permanent' if ttl is None else str(ttl) + ' seconds'}")

if __name__ == "__main__":
    main()
