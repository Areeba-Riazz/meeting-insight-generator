"""Caching utilities for LLM responses and embeddings."""

import hashlib
import json
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class SimpleCache:
    """Simple in-memory cache with optional disk persistence."""
    
    def __init__(self, max_size: int = 1000, cache_dir: Optional[Path] = None):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of items in memory cache
            cache_dir: Optional directory for disk cache persistence
        """
        self._cache: dict[str, Any] = {}
        self.max_size = max_size
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        # Create a hash of the arguments
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Optional[Path]:
        """Get path for disk cache file."""
        if not self.cache_dir:
            return None
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check memory cache first
        if key in self._cache:
            return self._cache[key]
        
        # Check disk cache
        cache_path = self._get_cache_path(key)
        if cache_path and cache_path.exists():
            try:
                with open(cache_path, 'r') as f:
                    value = json.load(f)
                    # Promote to memory cache
                    self._cache[key] = value
                    return value
            except Exception as e:
                logger.warning(f"Failed to load cache from disk: {e}")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        # Evict oldest if cache is full
        if len(self._cache) >= self.max_size and key not in self._cache:
            # Remove first item (FIFO)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
        
        self._cache[key] = value
        
        # Persist to disk
        cache_path = self._get_cache_path(key)
        if cache_path:
            try:
                with open(cache_path, 'w') as f:
                    json.dump(value, f)
            except Exception as e:
                logger.warning(f"Failed to write cache to disk: {e}")
    
    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")


# Global cache instance
_llm_cache: Optional[SimpleCache] = None


def get_llm_cache() -> SimpleCache:
    """Get or create global LLM cache."""
    global _llm_cache
    if _llm_cache is None:
        cache_dir = Path("storage/cache/llm")
        _llm_cache = SimpleCache(max_size=500, cache_dir=cache_dir)
    return _llm_cache


def cached_llm_call(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to cache LLM function calls based on prompt content.
    
    Usage:
        @cached_llm_call
        async def get_completion(prompt: str, ...):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract prompt from args/kwargs (usually first arg or 'prompt' kwarg)
        prompt = None
        if args and isinstance(args[0], str):
            prompt = args[0]
        elif 'prompt' in kwargs:
            prompt = kwargs['prompt']
        
        if not prompt:
            # No prompt found, skip caching
            return await func(*args, **kwargs)
        
        cache = get_llm_cache()
        # Create cache key from prompt and other relevant params
        cache_key = cache._get_key(prompt, kwargs.get('max_tokens'), kwargs.get('temperature'))
        
        # Check cache
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.debug(f"Cache hit for LLM call: {prompt[:50]}...")
            return cached_result
        
        # Call function
        result = await func(*args, **kwargs)
        
        # Cache result
        cache.set(cache_key, result)
        logger.debug(f"Cached LLM call result: {prompt[:50]}...")
        
        return result
    
    return wrapper

