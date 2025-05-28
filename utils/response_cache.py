import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class ResponseCache:
    """In-memory response caching with TTL."""
    
    def __init__(self, config_manager, default_ttl_minutes: int = 60):
        self.config = config_manager
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._stats = {
            'hits': 0,
            'misses': 0,
            'total_queries': 0
        }
        self._lock = threading.RLock()
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _generate_cache_key(self, query: str) -> str:
        """Generate cache key from query."""
        # Normalize query for caching
        normalized_query = query.lower().strip()
        
        # Create hash of the query
        return hashlib.md5(normalized_query.encode()).hexdigest()
    
    def get_cached_response(self, query: str) -> Optional[str]:
        """Get cached response if available and not expired."""
        cache_key = self._generate_cache_key(query)
        
        with self._lock:
            self._stats['total_queries'] += 1
            
            if cache_key in self._cache:
                cache_entry = self._cache[cache_key]
                
                # Check if expired
                if datetime.now() > cache_entry['expires_at']:
                    del self._cache[cache_key]
                    self._stats['misses'] += 1
                    return None
                
                # Update access time
                cache_entry['last_accessed'] = datetime.now()
                self._stats['hits'] += 1
                
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cache_entry['response']
            
            self._stats['misses'] += 1
            return None
    
    def cache_response(self, query: str, response: str, ttl: Optional[timedelta] = None) -> None:
        """Cache a response with optional TTL."""
        if not response or len(response.strip()) == 0:
            return
        
        cache_key = self._generate_cache_key(query)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            self._cache[cache_key] = {
                'query': query[:100],  # Store truncated query for debugging
                'response': response,
                'created_at': datetime.now(),
                'last_accessed': datetime.now(),
                'expires_at': datetime.now() + ttl
            }
            
            logger.debug(f"Cached response for query: {query[:50]}...")
    
    def clear_cache(self) -> int:
        """Clear all cached responses."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared {count} cached responses")
            return count
    
    def clear_expired(self) -> int:
        """Clear expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        with self._lock:
            for key, entry in self._cache.items():
                if now > entry['expires_at']:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.debug(f"Cleared {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            hit_rate = (self._stats['hits'] / max(1, self._stats['total_queries'])) * 100
            
            return {
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'total_queries': self._stats['total_queries'],
                'hit_rate_percent': round(hit_rate, 2),
                'cached_items': len(self._cache),
                'cache_size_mb': self._estimate_cache_size()
            }
    
    def _estimate_cache_size(self) -> float:
        """Estimate cache size in MB."""
        total_size = 0
        for entry in self._cache.values():
            # Rough estimation
            total_size += len(str(entry))
        
        return round(total_size / (1024 * 1024), 2)
    
    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries."""
        import time
        
        while True:
            try:
                time.sleep(300)  # Run every 5 minutes
                self.clear_expired()
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")