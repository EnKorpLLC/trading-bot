from typing import Dict, Optional, Any
import logging
from datetime import datetime, timedelta
import pickle
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

class CacheItem:
    def __init__(self, value: Any, ttl: int = 3600):
        self.value = value
        self.expiry = datetime.now() + timedelta(seconds=ttl)
        
    def is_expired(self) -> bool:
        return datetime.now() > self.expiry

class CacheManager:
    def __init__(self):
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache: Dict[str, CacheItem] = {}
        self.disk_cache_enabled = True
        self.lock = threading.Lock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self.cleanup_thread.start()
        
    def get_market_data(self, key: str) -> Optional[Dict]:
        """Get market data from cache."""
        # Check memory cache first
        if cached := self.memory_cache.get(key):
            if not cached.is_expired():
                return cached.value
            else:
                self.memory_cache.pop(key)
                
        # Check disk cache
        if self.disk_cache_enabled:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        cached = pickle.load(f)
                    if not cached.is_expired():
                        # Restore to memory cache
                        self.memory_cache[key] = cached
                        return cached.value
                    else:
                        cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error reading cache file: {str(e)}")
                    
        return None
        
    def cache_market_data(self, key: str, data: Dict, ttl: int = 3600):
        """Cache market data in memory and disk."""
        try:
            with self.lock:
                cache_item = CacheItem(data, ttl)
                self.memory_cache[key] = cache_item
                
                if self.disk_cache_enabled:
                    cache_file = self.cache_dir / f"{key}.cache"
                    with open(cache_file, 'wb') as f:
                        pickle.dump(cache_item, f)
                        
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            
    def invalidate(self, key: str):
        """Invalidate cache entry."""
        with self.lock:
            self.memory_cache.pop(key, None)
            if self.disk_cache_enabled:
                cache_file = self.cache_dir / f"{key}.cache"
                if cache_file.exists():
                    cache_file.unlink()
                    
    def clear(self):
        """Clear all cache."""
        with self.lock:
            self.memory_cache.clear()
            if self.disk_cache_enabled:
                for cache_file in self.cache_dir.glob("*.cache"):
                    cache_file.unlink()
                    
    def _cleanup_loop(self):
        """Periodically clean up expired cache entries."""
        while True:
            try:
                with self.lock:
                    # Clean memory cache
                    expired_keys = [
                        k for k, v in self.memory_cache.items()
                        if v.is_expired()
                    ]
                    for key in expired_keys:
                        self.memory_cache.pop(key)
                        
                    # Clean disk cache
                    if self.disk_cache_enabled:
                        for cache_file in self.cache_dir.glob("*.cache"):
                            try:
                                with open(cache_file, 'rb') as f:
                                    cached = pickle.load(f)
                                if cached.is_expired():
                                    cache_file.unlink()
                            except Exception:
                                cache_file.unlink()
                                
            except Exception as e:
                logger.error(f"Error in cache cleanup: {str(e)}")
                
            time.sleep(300)  # Clean every 5 minutes 