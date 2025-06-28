from cache import RedisCache
import time
import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Redis cache
cache = RedisCache()

# Configure Gemini - using environment variable for API key
genai.configure(api_key=os.getenv('GEMINI_API_KEY')

def call_gemini(query: str) -> str:
    """Call Google Gemini API"""
    try:
        model = genai.GenerativeModel('gemini-1.0-pro')
        response = model.generate_content(query)
        
        # Handle different response formats
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates'):
            return response.candidates[0].content.parts[0].text
        else:
            raise Exception("Unexpected response format from Gemini API")
    
    except Exception as e:
        print(f"Gemini API error: {str(e)}")
        raise

def get_llm_response(query: str) -> str:
    """Get response with caching"""
    start_time = time.time()
    
    # Check cache first
    if cached_response := cache.get(query):
        print(f"⚡ Cache HIT! ({time.time()-start_time:.3f}s)")
        return cached_response
    
    # Cache miss - call Gemini
    print(f"🔄 Cache MISS - Calling Gemini...")
    try:
        gemini_response = call_gemini(query)
        cache.set(query, gemini_response, ex=86400)  # 24h expiration
        return gemini_response
    
    except Exception as e:
        if cached_fallback := cache.get(query):
            print(f"⚠️ Gemini Failed! Using stale cache")
            return cached_fallback
        raise Exception(f"Gemini call failed: {str(e)}")

def get_cache_stats():
    """Safe way to get cache statistics"""
    try:
        # Try to get basic info about the cache
        stats = {
            'keys': len(cache.redis.keys('*')),
            'size': cache.redis.dbsize(),
        }
        return stats
    except Exception as e:
        print(f"⚠️ Could not get cache stats: {str(e)}")
        return {'error': 'Stats unavailable'}

if __name__ == "__main__":
    queries = []
    while True:
        query = input("Enter a query (or type 'done' to finish): ")
        if query.lower() == 'done':
            break
        queries.append(query)
    
    for query in queries:
        print(f"\nQuery: '{query}'")
        try:
            response = get_llm_response(query)
            print(f"Answer: {response[:200]}..." if response else "Empty response")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print(f"\nCache Info: {get_cache_stats()}")
