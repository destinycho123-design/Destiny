"""Caching layer for weather data."""

import json
import time
from typing import Optional, Dict, Any
from pathlib import Path


class WeatherCache:
    """In-memory and file-based cache for weather data."""

    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: int = 3600):
        """
        Initialize weather cache.
        
        Args:
            cache_dir: Directory for persistent cache files (None = memory only)
            ttl_seconds: Time to live for cache entries in seconds (default: 1 hour)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.ttl_seconds = ttl_seconds
        self.memory_cache: Dict[str, tuple] = {}  # (data, expiry_time)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        # Check memory cache first
        if key in self.memory_cache:
            data, expiry = self.memory_cache[key]
            if time.time() < expiry:
                return data
            else:
                del self.memory_cache[key]

        # Check file cache
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, "r") as f:
                        cache_data = json.load(f)
                    if time.time() < cache_data["expiry"]:
                        return cache_data["data"]
                    else:
                        cache_file.unlink()
                except (json.JSONDecodeError, IOError, KeyError):
                    pass

        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        expiry = time.time() + self.ttl_seconds

        # Store in memory
        self.memory_cache[key] = (value, expiry)

        # Store in file if cache_dir is set
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file = self.cache_dir / f"{key}.json"
            try:
                with open(cache_file, "w") as f:
                    json.dump({"data": value, "expiry": expiry}, f)
            except IOError:
                pass  # Silently fail if we can't write to file

    def clear(self) -> None:
        """Clear all cache entries."""
        self.memory_cache.clear()
        if self.cache_dir and self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
