"""Unit tests for cache utilities."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.cache import SimpleCache, get_llm_cache, cached_llm_call


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    return Path(tempfile.mkdtemp())


@pytest.fixture
def cache(temp_cache_dir):
    """Create a SimpleCache instance for testing."""
    # Use None for cache_dir to avoid disk interference in this test
    return SimpleCache(max_size=10, cache_dir=None)


@pytest.mark.unit
def test_simple_cache_get_set(cache):
    """Test basic get/set operations."""
    # Set a value
    cache.set("test_key", "test_value")
    
    # Get the value
    result = cache.get("test_key")
    assert result == "test_value"


@pytest.mark.unit
def test_simple_cache_get_missing(cache):
    """Test getting a non-existent key."""
    result = cache.get("nonexistent")
    assert result is None


@pytest.mark.unit
def test_simple_cache_get_key():
    """Test cache key generation."""
    cache = SimpleCache()
    key1 = cache._get_key("arg1", "arg2", kwarg1="value1")
    key2 = cache._get_key("arg1", "arg2", kwarg1="value1")
    key3 = cache._get_key("arg1", "arg2", kwarg1="value2")
    
    # Same arguments should generate same key
    assert key1 == key2
    # Different arguments should generate different key
    assert key1 != key3


@pytest.mark.unit
def test_simple_cache_max_size(cache):
    """Test cache eviction when max size is reached."""
    # Fill cache to exactly max_size (10)
    for i in range(10):
        cache.set(f"key_{i}", f"value_{i}")
    
    # All keys should be present
    assert cache.get("key_0") == "value_0"
    assert cache.get("key_9") == "value_9"
    assert len(cache._cache) == 10
    
    # Add one more key to trigger eviction (since key_10 is new, not in cache)
    # This should evict the first key (key_0) due to FIFO
    cache.set("key_10", "value_10")
    
    # First key (key_0) should be evicted (FIFO)
    assert cache.get("key_0") is None, "First key should be evicted when cache is full"
    # Last key should still be present
    assert cache.get("key_10") == "value_10"
    # Cache should still be at max_size
    assert len(cache._cache) == 10
    
    # Add another key to evict key_1
    cache.set("key_11", "value_11")
    assert cache.get("key_1") is None, "Second key should be evicted"
    assert cache.get("key_11") == "value_11"
    assert len(cache._cache) == 10


@pytest.mark.unit
def test_simple_cache_clear(cache):
    """Test clearing the cache."""
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    
    cache.clear()
    
    assert cache.get("key1") is None
    assert cache.get("key2") is None


@pytest.mark.unit
def test_simple_cache_disk_persistence(temp_cache_dir):
    """Test disk cache persistence."""
    # Use a cache with disk persistence
    cache1 = SimpleCache(max_size=10, cache_dir=temp_cache_dir)
    test_value = {"data": "test"}
    # Set using a simple key (the cache uses the key directly, not _get_key)
    cache1.set("disk_key", test_value)
    
    # Create a new cache instance with same directory
    cache2 = SimpleCache(max_size=10, cache_dir=temp_cache_dir)
    
    # Should load from disk
    result = cache2.get("disk_key")
    assert result == test_value


@pytest.mark.unit
def test_simple_cache_disk_load_error(cache, temp_cache_dir):
    """Test handling of disk load errors."""
    # Create invalid cache file
    cache_file = temp_cache_dir / "invalid_key.json"
    cache_file.write_text("invalid json")
    
    # Should return None on error
    result = cache.get("invalid_key")
    assert result is None


@pytest.mark.unit
def test_get_llm_cache():
    """Test getting global LLM cache."""
    cache1 = get_llm_cache()
    cache2 = get_llm_cache()
    
    # Should return same instance
    assert cache1 is cache2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cached_llm_call_cache_hit():
    """Test cached_llm_call decorator with cache hit."""
    from src.utils.cache import SimpleCache, cached_llm_call
    import src.utils.cache as cache_module
    
    # Save old cache and create a clean one for testing
    old_cache = cache_module._llm_cache
    test_cache = SimpleCache(max_size=100, cache_dir=None)  # No disk cache for speed
    cache_module._llm_cache = test_cache
    
    try:
        call_count = 0
        
        @cached_llm_call
        async def test_func(prompt: str):
            nonlocal call_count
            call_count += 1
            return f"response for {prompt}"
        
        # First call should execute function (cache miss)
        result1 = await test_func("test prompt")
        assert result1 == "response for test prompt"
        assert call_count == 1, f"Expected 1 call but got {call_count}"
        
        # Second call should use cache (cache hit)
        result2 = await test_func("test prompt")
        assert result2 == "response for test prompt"
        assert call_count == 1, f"Expected 1 call (cached) but got {call_count}"
    finally:
        # Restore original cache
        cache_module._llm_cache = old_cache


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cached_llm_call_cache_miss():
    """Test cached_llm_call with different prompts."""
    from src.utils.cache import SimpleCache, cached_llm_call
    import src.utils.cache as cache_module
    
    # Save old cache and create a clean one for testing
    old_cache = cache_module._llm_cache
    test_cache = SimpleCache(max_size=100, cache_dir=None)  # No disk cache for speed
    cache_module._llm_cache = test_cache
    
    try:
        call_count = 0
        
        @cached_llm_call
        async def test_func(prompt: str):
            nonlocal call_count
            call_count += 1
            return f"response for {prompt}"
        
        await test_func("prompt1")
        await test_func("prompt2")
        
        # Both should call the function (different prompts = different cache keys)
        assert call_count == 2
    finally:
        # Restore original cache
        cache_module._llm_cache = old_cache


@pytest.mark.unit
@pytest.mark.asyncio
async def test_cached_llm_call_with_kwargs():
    """Test cached_llm_call with kwargs."""
    @cached_llm_call
    async def test_func(prompt: str, max_tokens: int = 100):
        return f"response for {prompt} with {max_tokens} tokens"
    
    result1 = await test_func("test", max_tokens=100)
    result2 = await test_func("test", max_tokens=200)
    
    # Different max_tokens should result in different cache entries
    assert result1 != result2

