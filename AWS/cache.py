from sentence_transformers import SentenceTransformer, util

class SemanticCache:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Efficient embedding model
        self.cache = []  # List of dicts: {'key': str, 'embedding': tensor, 'value': any}

    def _get_embedding(self, key):
        return self.model.encode(key, convert_to_tensor=True)

    def get(self, key, threshold=0.9):
        query_emb = self._get_embedding(key)
        for item in self.cache:
            sim = util.cos_sim(query_emb, item['embedding']).item()
            if sim >= threshold:
                return item['value']
        return None

    def set(self, key, value):
        emb = self._get_embedding(key)
        self.cache.append({'key': key, 'embedding': emb, 'value': value})

# Global instance of the cache
cache = SemanticCache()
