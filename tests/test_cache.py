"""Tests for weather cache."""

import unittest
import time
import tempfile
import shutil
from pathlib import Path
from weather.cache import WeatherCache


class TestWeatherCache(unittest.TestCase):
    """Test WeatherCache."""

    def setUp(self):
        """Set up test cache."""
        self.cache = WeatherCache(ttl_seconds=2)  # Short TTL for testing

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        self.cache.set("test_key", {"data": "value"})
        result = self.cache.get("test_key")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["data"], "value")

    def test_cache_expiry(self):
        """Test cache expiration."""
        self.cache.set("test_key", {"data": "value"})
        
        # Wait for cache to expire
        time.sleep(2.5)
        
        result = self.cache.get("test_key")
        self.assertIsNone(result)

    def test_cache_miss(self):
        """Test cache miss."""
        result = self.cache.get("nonexistent_key")
        self.assertIsNone(result)

    def test_cache_clear(self):
        """Test clearing cache."""
        self.cache.set("key1", {"data": "value1"})
        self.cache.set("key2", {"data": "value2"})
        
        self.cache.clear()
        
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_file_based_cache(self):
        """Test file-based cache persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = WeatherCache(cache_dir=tmpdir, ttl_seconds=3600)
            cache.set("test_key", {"data": "value"})
            
            # Create new cache instance reading from same directory
            cache2 = WeatherCache(cache_dir=tmpdir, ttl_seconds=3600)
            result = cache2.get("test_key")
            
            self.assertIsNotNone(result)
            self.assertEqual(result["data"], "value")


if __name__ == "__main__":
    unittest.main()
