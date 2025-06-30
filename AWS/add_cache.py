import sys
from cache import RedisCache

def main():
    # Expecting arguments: script_name query response [ttl]
    if len(sys.argv) < 3:
        print("Usage: python set_cache_entry.py <query> <response> [ttl_in_seconds]")
        print("  ttl_in_seconds: Optional. Set to 0 or 'None' for permanent cache.")
        sys.exit(1)

    query = sys.argv[1]
    response = sys.argv[2]
    ttl = None # Default to permanent if not provided or explicitly 'None'

    if len(sys.argv) == 4:
        try:
            ttl = int(ttl_str)
        except ValueError:
            print(f"Error: Invalid TTL value '{sys.argv[3]}'. Must be an integer, '0', or 'None'.")
            sys.exit(1)

    cache = RedisCache()
    cache.set(query, response, ttl=ttl)

    print(f"Cache entry set successfully for query: '{query}'")
    print(f"Response: '{response}'")
    print(f"TTL: {'Permanent' if ttl is None else str(ttl) + ' seconds'}")

if __name__ == "__main__":
    main()