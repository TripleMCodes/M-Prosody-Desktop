import json
import os
from threading import RLock
from pathlib import Path

#cache folder file dir
cache_dir = Path(__file__).parent / "cache dir/cache.json"

class DictionaryCache:
    def __init__(self, filename=cache_dir):
        self.filename = filename
        self.lock = RLock()
        self.cache = {}
        self._load_from_disk()

    def _load_from_disk(self):
        """Load cache from file if it exists."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    self.cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.cache = {}
    
    def _save_to_disk(self):
        """Save current cache to file"""
        with self.lock:
            with open(self.filename, "w") as f:
                json.dump(self.cache, f, indent=4)

    def set(self, key, value, persist=True):
        """Set a value in the cache."""
        with self.lock:
            self.cache[key] = value
            if persist:
                self._save_to_disk()

    def get(self, key, default=None):
        """Get a value from the cache."""
        with self.lock:
            return self.cache.get(key, default)
        
    def delete(self, key):
        """Remove a key from the cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self._save_to_disk()
    
    def clear(self):
        """Clear the entire cache."""
        with self.lock:
            self.cache = {}
            self._save_to_disk()

    def all(self):
        """Return the full cache dictionary."""
        with self.lock:
            return self.cache.copy()