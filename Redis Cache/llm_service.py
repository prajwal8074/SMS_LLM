from cache import RedisCache
import time

# Initialize cache
cache = RedisCache()

def get_llm_response(query: str):
    """Main function to handle requests with caching"""
    # 1. Check cache first
    start_time = time.time()
    if cached := cache.get(query):
        print(f"✅ Cache HIT! ({time.time()-start_time:.3f}s)")
        return cached
    
    # 2. Cache miss - call LLM (simulated)
    print(f"❌ Cache MISS! Calling LLM...")
    llm_response = expensive_llm_call(query)  # Your actual LLM API call
    
    # 3. Save to cache
    cache.set(query, llm_response)
    
    return llm_response

def expensive_llm_call(query: str) -> str:
    """Simulate slow LLM API call"""
    time.sleep(0.5)  # Simulate 500ms delay
    return f"LLM response to: {query}"

# Test it!
if __name__ == "__main__":
    queries = []
    while True:
        query = input("Enter a query (or type 'done' to finish): ")
        if query.lower() == 'done':
            break
        queries.append(query)
    print("Your queries:", queries)
    
    for q in queries:
        print(f"\nQuery: '{q}'")
        response = get_llm_response(q)
        print(f"Response: {response[:50]}...")
    
    print(f"\nCache Hit Rate: {cache.cache_hit_rate()*100:.1f}%")